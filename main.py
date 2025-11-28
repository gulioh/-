import datetime
import asyncio
import random
import logging

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram import F
from aiogram.filters import CommandStart
from aiogram.utils.markdown import hlink
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from loader import dp, db, bot, crypto
from keybords import *
from config import *
from States import *
from States import Captcha_users, AddBalanceUser, GameDice, GameSlots, GameFootball, GameKNB

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Импортируем словарь капчи
try:
    from captcha_element import captcha_dict
except ImportError:
    # Резервный словарь если файл не найден
    captcha_dict = {
        'apple': '🍎', 'banana': '🍌', 'grape': '🍇', 'strawberry': '🍓',
        'pineapple': '🍍', 'watermelon': '🍉', 'cherry': '🍒', 'peach': '🍑'
    }

# Безопасное получение URL
def safe_get_url(key):
    try:
        url_data = db.get_URL()
        if url_data and url_data.get(key):
            return url_data.get(key)
    except:
        pass
    return "https://t.me/telegram"

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    try:
        # Проверяем существование пользователя
        if db.user_exists(message.from_user.id):
            # Пользователь существует - сразу в меню
            await message.answer(
                f'👋🏻 С возвращением, {message.from_user.first_name}!',
                reply_markup=kb_menu(message.from_user.id)
            )
            await state.clear()
            return
        
        # Новый пользователь - капча
        word = random.choice(list(captcha_dict.keys()))
        start_cmd = message.text
        referi_id = str(start_cmd[7:])
        
        if referi_id and referi_id != '' and referi_id != str(message.from_user.id):
            db.add_users(message.from_user.id, referi_id)
        else:
            db.add_users(message.from_user.id)
        
        await message.answer(
            f'👋🏻 Привет {message.from_user.first_name}, чтобы убедиться что вы не робот 🤖 - пройдите капчу\n\n'
            f'Нажми на 👉 <b>{word}</b>', 
            reply_markup=await captcha_keybord(word)
        )
        await state.set_state(Captcha_users.status)
        
    except Exception as e:
        logger.error(f"Ошибка в cmd_start: {e}")
        await message.answer("❌ Произошла ошибка при запуске бота")

@dp.callback_query(F.data.startswith('Captcha'), Captcha_users.status)
async def chek_captcha(callback: CallbackQuery, state: FSMContext):
    """Проверка капчи"""
    try:
        keys = callback.data.split('|')[1]
        word = callback.data.split('|')[2]
        
        word_new = random.choice(list(captcha_dict.keys()))
        if keys == word:
            await callback.message.delete()
            await callback.message.answer(
                f'<b>👋 Добро пожаловать в {NAME_CASINO} 🎲</b>\n\n'
                f'<b>Теперь вы можете:</b>\n'
                f'🎲 <b>Играть</b> - сделать ставку в казино\n'
                f'💸 <b>Пополнить баланс</b> - добавить средств\n'
                f'📎 <b>Реферальная программа</b> - приглашать друзей\n'
                f'💭 <b>Информация</b> - правила и инструкции\n'
                f'👤 <b>Профиль</b> - ваша статистика\n\n'
                f'<i>Используйте кнопки меню ниже ↓</i>',
                reply_markup=kb_menu(callback.from_user.id)
            )
            await state.clear()
        else:
            await callback.answer('⚠️ Вы не прошли проверку!', show_alert=True)
            await callback.message.edit_text(
                text=f'👋🏻 Привет {callback.from_user.first_name}, чтобы убедиться что вы не робот 🤖 - пройдите капчу\n\n'
                     f'Нажми на 👉 <b>{word_new}</b>', 
                reply_markup=await captcha_keybord(word_new)
            )
    except Exception as e:
        logger.error(f"Ошибка в chek_captcha: {e}")
        await callback.answer('❌ Ошибка проверки капчи', show_alert=True)
        await state.clear()

# ПОПОЛНЕНИЕ БАЛАНСА
@dp.message(F.text == '💸 Пополнить баланс')
async def add_balance_user(message: Message, state: FSMContext):
    """Пополнение баланса"""
    await message.answer(
        '<b>💸 Пополнение баланса</b>\n\n'
        'Введите сумму пополнения в $ (например: 10):',
        reply_markup=ReplyKeyboardBuilder([
            [KeyboardButton(text="❌ Отмена")]
        ]).as_markup(resize_keyboard=True)
    )
    await state.set_state(AddBalanceUser.amount)

@dp.message(AddBalanceUser.amount)
async def process_add_balance(message: Message, state: FSMContext):
    """Обработка суммы пополнения"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Пополнение отменено", reply_markup=kb_menu(message.from_user.id))
        return
    
    try:
        amount = float(message.text)
        if amount < 1:
            await message.answer("❌ Минимальная сумма пополнения: 1$")
            return
        
        # Создаем инвойс через Crypto Bot
        invoice = await crypto.create_invoice(
            asset='USDT',
            amount=amount,
            description=f'Пополнение баланса для пользователя {message.from_user.id}'
        )
        
        await message.answer(
            f'<b>💸 Счет на оплату</b>\n\n'
            f'<b>Сумма:</b> {amount}$\n'
            f'<b>Статус:</b> Ожидание оплаты\n\n'
            f'Оплатите счет в течение 15 минут',
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="💳 Оплатить", url=invoice.bot_invoice_url)],
                [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_payment_{invoice.invoice_id}")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_payment")]
            ]).adjust(1).as_markup()
        )
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму (например: 10)")
    except Exception as e:
        logger.error(f"Ошибка в process_add_balance: {e}")
        await message.answer(f"❌ Ошибка создания счета: {e}")

@dp.callback_query(F.data.startswith("check_payment_"))
async def check_payment_handler(callback: CallbackQuery):
    """Проверка статуса оплаты"""
    invoice_id = callback.data.replace("check_payment_", "")
    user_id = callback.from_user.id
    
    try:
        # Получаем информацию о инвойсе
        invoices = await crypto.get_invoices(invoice_ids=invoice_id)
        if not invoices:
            await callback.answer("❌ Счет не найден", show_alert=True)
            return
        
        invoice = invoices[0]
        
        if invoice.status == 'paid':
            # Пополняем баланс
            amount = float(invoice.amount)
            db.update_user_balance(user_id, amount)
            
            new_balance = db.get_user_balance(user_id)
            
            await callback.message.edit_text(
                f'<b>✅ Оплата подтверждена!</b>\n\n'
                f'💰 <b>Сумма:</b> {amount}$\n'
                f'💳 <b>Баланс пополнен</b>\n\n'
                f'💰 <b>Текущий баланс:</b> {new_balance}$',
                reply_markup=InlineKeyboardBuilder([
                    [InlineKeyboardButton(text="🎲 Играть", callback_data="back_to_games")],
                    [InlineKeyboardButton(text="👤 Профиль", callback_data="refresh_profile")]
                ]).adjust(1).as_markup()
            )
            
        elif invoice.status == 'active':
            await callback.answer("⏳ Оплата еще не поступила", show_alert=True)
        else:
            await callback.answer("❌ Счет просрочен или отменен", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка в check_payment_handler: {e}")
        await callback.answer(f"❌ Ошибка проверки: {e}", show_alert=True)

@dp.callback_query(F.data == "cancel_payment")
async def cancel_payment_handler(callback: CallbackQuery):
    """Отмена платежа"""
    await callback.message.edit_text(
        "❌ Пополнение баланса отменено",
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="💸 Пополнить баланс", callback_data="add_balance_from_profile")],
            [InlineKeyboardButton(text="📋 Меню", callback_data="back_to_menu")]
        ]).adjust(1).as_markup()
    )

# ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
@dp.message(F.text == '👤 Профиль')
async def user_profile(message: Message):
    """Профиль пользователя"""
    user_id = message.from_user.id
    balance = db.get_user_balance(user_id)
    stats = db.all_stats_users(user_id)
    
    if stats:
        total_games, wins, loses, total_win, total_lose, balance_ref = stats
    else:
        total_games = wins = loses = total_win = total_lose = balance_ref = 0
    
    referrals_count = db.count_ref(user_id)
    referrals_earnings = db.refka_cheks_money(user_id)
    
    win_rate = round((wins/total_games*100), 1) if total_games > 0 else 0
    
    await message.answer(
        f'<b>👤 Ваш профиль</b>\n\n'
        f'💰 <b>Баланс:</b> {balance}$\n'
        f'🎮 <b>Всего игр:</b> {total_games}\n'
        f'✅ <b>Побед:</b> {wins}\n'
        f'❌ <b>Поражений:</b> {loses}\n'
        f'🏆 <b>Процент побед:</b> {win_rate}%\n\n'
        f'<b>📊 Статистика:</b>\n'
        f'💸 <b>Выиграно:</b> {total_win}$\n'
        f'📉 <b>Проиграно:</b> {total_lose}$\n\n'
        f'<b>👥 Реферальная программа:</b>\n'
        f'👤 <b>Приглашено:</b> {referrals_count} чел.\n'
        f'💵 <b>Заработано:</b> {referrals_earnings}$\n\n'
        f'<b>Ваша реферальная ссылка:</b>\n'
        f'<code>https://t.me/{NICNAME}?start={user_id}</code>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="💸 Пополнить баланс", callback_data="add_balance_from_profile")],
            [InlineKeyboardButton(text="🎲 Играть", callback_data="back_to_games")]
        ]).adjust(1).as_markup()
    )

@dp.callback_query(F.data == "add_balance_from_profile")
async def add_balance_from_profile(callback: CallbackQuery, state: FSMContext):
    """Пополнение баланса из профиля"""
    await add_balance_user(callback.message, state)

@dp.callback_query(F.data == "refresh_profile")
async def refresh_profile(callback: CallbackQuery):
    """Обновление профиля"""
    await user_profile(callback.message)

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.answer(
        "📋 <b>Главное меню</b>",
        reply_markup=kb_menu(callback.from_user.id)
    )

# ИНФОРМАЦИЯ
@dp.message(F.text == '💭 Информация')
async def info_handler(message: Message):
    """Информация о боте"""
    urls = db.get_URL()
    
    await message.answer(
        '<b>💭 Информация</b>\n\n'
        f'<b>🎰 Казино:</b> {NAME_CASINO}\n'
        f'<b>🤖 Бот:</b> {NICNAME}\n'
        f'📞 Поддержка: {ADMIN_USERNAME}\n\n'
        f'<b>Доступные игры:</b>\n'
        f'🎯 Кости\n'
        f'🎰 Слоты\n'
        f'⚽️ Футбол\n'
        f'🪨✂️📄 Камень-Ножницы-Бумага\n\n'
        f'<b>Минимальная ставка:</b> 0.1$\n'
        f'<b>Автоматические выплаты</b>',
        reply_markup=kb_info()
    )

# РЕФЕРАЛЬНАЯ ПРОГРАММА
@dp.message(F.text == '📎 Реферальная программа')
async def referral_program(message: Message):
    """Реферальная программа"""
    user_id = message.from_user.id
    referrals_count = db.count_ref(user_id)
    referrals_earnings = db.refka_cheks_money(user_id)
    
    await message.answer(
        f'<b>📎 Реферальная программа</b>\n\n'
        f'💵 <b>Зарабатывайте {lose_withdraw}% от проигрышей ваших рефералов!</b>\n\n'
        f'<b>Ваша статистика:</b>\n'
        f'👤 <b>Приглашено:</b> {referrals_count} чел.\n'
        f'💰 <b>Заработано:</b> {referrals_earnings}$\n\n'
        f'<b>Ваша реферальная ссылка:</b>\n'
        f'<code>https://t.me/{NICNAME}?start={user_id}</code>\n\n'
        f'<b>Как это работает:</b>\n'
        f'• Приглашайте друзей по вашей ссылке\n'
        f'• Получайте {lose_withdraw}% от их проигрышей\n'
        f'• Минимальная ставка для начисления: {min_stavka_referal}$\n'
        f'• Выплаты автоматические',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="👤 Пригласить друзей", url=f"https://t.me/share/url?url=https://t.me/{NICNAME}?start={user_id}")],
            [InlineKeyboardButton(text="📋 Меню", callback_data="back_to_menu")]
        ]).adjust(1).as_markup()
    )

# АДМИНКА
@dp.message(F.text == '👑 Админка')
async def admin_panel(message: Message):
    """Панель администратора"""
    user_id = message.from_user.id
    
    if user_id not in ADMIN:
        await message.answer("❌ У вас нет доступа к админ-панели")
        return
    
    await message.answer(
        '<b>👑 Панель администратора</b>\n\n'
        'Выберите действие:',
        reply_markup=kb_admin()
    )

# ИГРЫ
@dp.message(F.text == '🎲 Играть')
async def play_game_menu(message: Message):
    """Меню выбора игры"""
    user_id = message.from_user.id
    balance = db.get_user_balance(user_id)
    
    await message.answer(
        f'<b>🎲 Выберите игру</b>\n\n'
        f'💰 <b>Ваш баланс:</b> {balance}$\n\n'
        f'<b>Доступные игры:</b>\n'
        f'🎯 <b>Кости</b> - классическая игра в кости\n'
        f'🎰 <b>Слоты</b> - игровые автоматы\n'
        f'⚽️ <b>Футбол</b> - ставки на гол/мимо\n'
        f'🪨✂️📄 <b>КНБ</b> - камень-ножницы-бумага\n\n'
        f'<i>Выберите игру:</i>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="🎯 Кости", callback_data="game_dice_info")],
            [InlineKeyboardButton(text="🎰 Слоты", callback_data="game_slots_info")],
            [InlineKeyboardButton(text="⚽️ Футбол", callback_data="game_football_info")],
            [InlineKeyboardButton(text="🪨✂️📄 КНБ", callback_data="game_knb_info")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_games")]
        ]).adjust(2).as_markup()
    )

@dp.callback_query(F.data == "back_to_games")
async def back_to_games(callback: CallbackQuery):
    """Возврат в меню игр"""
    await play_game_menu(callback.message)

@dp.callback_query(F.data == "close_games")
async def close_games_menu(callback: CallbackQuery):
    """Закрытие меню игр"""
    await callback.message.delete()

# КОСТИ - ИНФОРМАЦИЯ
@dp.callback_query(F.data == "game_dice_info")
async def game_dice_info(callback: CallbackQuery):
    """Информация об игре в кости"""
    await callback.message.edit_text(
        '<b>🎯 Игра в кости</b>\n\n'
        '<b>📖 Правила игры:</b>\n'
        '• Ставьте на четное или нечетное число\n'
        '• Бросается виртуальный кубик (1-6)\n'
        '• Четное число (2,4,6) - выигрыш x2\n'
        '• Нечетное число (1,3,5) - проигрыш\n\n'
        '<b>🎲 Коэффициент: x2</b>\n'
        '<b>💰 Минимальная ставка: 0.1$</b>\n\n'
        '<i>Готовы сделать ставку?</i>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="🎯 Сделать ставку", callback_data="game_dice")],
            [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
        ]).adjust(1).as_markup()
    )

# КОСТИ - ИГРА
@dp.callback_query(F.data == "game_dice")
async def game_dice_menu(callback: CallbackQuery, state: FSMContext):
    """Меню игры в кости"""
    balance = db.get_user_balance(callback.from_user.id)
    
    if balance < 0.1:
        await callback.answer("❌ Недостаточно средств. Минимальная ставка: 0.1$", show_alert=True)
        return
    
    await callback.message.edit_text(
        f'<b>🎯 Игра в кости</b>\n\n'
        f'💰 <b>Ваш баланс:</b> {balance}$\n\n'
        f'<b>Введите сумму ставки:</b>\n'
        f'<i>Минимальная ставка: 0.1$</i>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="❌ Назад", callback_data="game_dice_info")]
        ]).as_markup()
    )
    await state.set_state(GameDice.amount)

@dp.message(GameDice.amount)
async def process_dice_amount(message: Message, state: FSMContext):
    """Обработка суммы ставки в кости"""
    try:
        amount = float(message.text)
        user_id = message.from_user.id
        balance = db.get_user_balance(user_id)
        
        if amount < 0.1:
            await message.answer("❌ Минимальная ставка: 0.1$")
            return
            
        if amount > balance:
            await message.answer(f"❌ Недостаточно средств. Ваш баланс: {balance}$")
            return
        
        # Списываем ставку
        db.update_user_balance(user_id, -amount)
        
        # Обновляем статистику
        db.update_user_stats(user_id, 'total_games', 1)
        db.update_user_stats(user_id, 'total_bet', amount)
        
        # Бросаем кубик
        dice_message = await message.answer_dice(emoji="🎲")
        dice_value = dice_message.dice.value
        
        await asyncio.sleep(3)
        
        # Простая логика - четное = победа
        win = (dice_value % 2 == 0)
        multiplier = 2
        win_amount = amount * multiplier if win else 0
        
        if win:
            db.update_user_balance(user_id, win_amount)
            db.update_user_stats(user_id, 'wins', 1)
            db.update_user_stats(user_id, 'total_win', win_amount)
            result_text = f"🎉 <b>ПОБЕДА!</b>\nВы выиграли: {win_amount}$"
        else:
            db.update_user_stats(user_id, 'loses', 1)
            result_text = f"😞 <b>ПРОИГРЫШ</b>\nВы проиграли: {amount}$"
        
        new_balance = db.get_user_balance(user_id)
        
        await message.answer(
            f'<b>🎯 Результат игры в кости</b>\n\n'
            f'🎲 <b>Выпало:</b> {dice_value}\n'
            f'💰 <b>Сумма ставки:</b> {amount}$\n'
            f'📈 <b>Коэффициент:</b> x{multiplier}\n\n'
            f'{result_text}\n\n'
            f'💰 <b>Новый баланс:</b> {new_balance}$',
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="🎯 Сыграть еще", callback_data="game_dice_info")],
                [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
            ]).adjust(1).as_markup()
        )
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму (например: 0.5)")

# СЛОТЫ - ИНФОРМАЦИЯ
@dp.callback_query(F.data == "game_slots_info")
async def game_slots_info(callback: CallbackQuery):
    """Информация об игре в слоты"""
    await callback.message.edit_text(
        '<b>🎰 Игровые автоматы</b>\n\n'
        '<b>📖 Правила игры:</b>\n'
        '• Крутите барабаны и собирайте выигрышные комбинации\n'
        '• 3 одинаковых символа - победа\n'
        '• Комбинации и коэффициенты:\n'
        '  🍒🍒🍒 - x2\n'
        '  🍋🍋🍋 - x2\n'
        '  💰💰💰 - x2\n'
        '  7️⃣7️⃣7️⃣ - x3 (ДЖЕКПОТ!)\n\n'
        '<b>🎰 Коэффициенты: x2-x3</b>\n'
        '<b>💰 Минимальная ставка: 0.1$</b>\n\n'
        '<i>Готовы сделать ставку?</i>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="🎰 Сделать ставку", callback_data="game_slots")],
            [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
        ]).adjust(1).as_markup()
    )

# СЛОТЫ - ИГРА
@dp.callback_query(F.data == "game_slots")
async def game_slots_menu(callback: CallbackQuery, state: FSMContext):
    """Меню игры в слоты"""
    balance = db.get_user_balance(callback.from_user.id)
    
    if balance < 0.1:
        await callback.answer("❌ Недостаточно средств. Минимальная ставка: 0.1$", show_alert=True)
        return
    
    await callback.message.edit_text(
        f'<b>🎰 Игровые автоматы</b>\n\n'
        f'💰 <b>Ваш баланс:</b> {balance}$\n\n'
        f'<b>Введите сумму ставки:</b>\n'
        f'<i>Минимальная ставка: 0.1$</i>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="❌ Назад", callback_data="game_slots_info")]
        ]).as_markup()
    )
    await state.set_state(GameSlots.amount)

@dp.message(GameSlots.amount)
async def process_slots_amount(message: Message, state: FSMContext):
    """Обработка суммы ставки в слотах"""
    try:
        amount = float(message.text)
        user_id = message.from_user.id
        balance = db.get_user_balance(user_id)
        
        if amount < 0.1:
            await message.answer("❌ Минимальная ставка: 0.1$")
            return
            
        if amount > balance:
            await message.answer(f"❌ Недостаточно средств. Ваш баланс: {balance}$")
            return
        
        # Списываем ставку
        db.update_user_balance(user_id, -amount)
        
        # Обновляем статистику
        db.update_user_stats(user_id, 'total_games', 1)
        db.update_user_stats(user_id, 'total_bet', amount)
        
        # Крутим слоты
        slots_message = await message.answer_dice(emoji="🎰")
        slots_value = slots_message.dice.value
        
        await asyncio.sleep(3)
        
        # Простая логика выигрыша
        win = (slots_value in [1, 22, 43, 64])  # Выигрышные комбинации
        multiplier = 3 if slots_value == 64 else 2  # 777 дает x3, остальные x2
        win_amount = amount * multiplier if win else 0
        
        if win:
            db.update_user_balance(user_id, win_amount)
            db.update_user_stats(user_id, 'wins', 1)
            db.update_user_stats(user_id, 'total_win', win_amount)
            result_text = f"🎉 <b>ПОБЕДА!</b>\nВы выиграли: {win_amount}$"
        else:
            db.update_user_stats(user_id, 'loses', 1)
            result_text = f"😞 <b>ПРОИГРЫШ</b>\nВы проиграли: {amount}$"
        
        new_balance = db.get_user_balance(user_id)
        
        await message.answer(
            f'<b>🎰 Результат игры в слоты</b>\n\n'
            f'🎰 <b>Комбинация:</b> {get_slots_name(slots_value)}\n'
            f'💰 <b>Сумма ставки:</b> {amount}$\n'
            f'📈 <b>Коэффициент:</b> x{multiplier if win else 0}\n\n'
            f'{result_text}\n\n'
            f'💰 <b>Новый баланс:</b> {new_balance}$',
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="🎰 Сыграть еще", callback_data="game_slots_info")],
                [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
            ]).adjust(1).as_markup()
        )
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму (например: 0.5)")

def get_slots_name(value):
    """Получение названия комбинации слотов"""
    if value == 64: return "7️⃣7️⃣7️⃣"
    elif value == 1: return "🍒🍒🍒" 
    elif value == 22: return "🍋🍋🍋"
    elif value == 43: return "💰💰💰"
    else: return "💥Проигрыш💥"

# ФУТБОЛ - ИНФОРМАЦИЯ
@dp.callback_query(F.data == "game_football_info")
async def game_football_info(callback: CallbackQuery):
    """Информация об игре в футбол"""
    await callback.message.edit_text(
        '<b>⚽️ Футбол</b>\n\n'
        '<b>📖 Правила игры:</b>\n'
        '• Делайте ставку на результат броска мяча\n'
        '• Бросается виртуальный мяч (1-5 очков)\n'
        '• Гол: 3-5 очков (победа x2)\n'
        '• Мимо: 1-2 очка (победа x2)\n'
        '• Если угадали результат - выигрываете\n\n'
        '<b>⚽️ Коэффициент: x2</b>\n'
        '<b>💰 Минимальная ставка: 0.1$</b>\n\n'
        '<i>Готовы сделать ставку?</i>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="⚽️ Сделать ставку", callback_data="game_football")],
            [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
        ]).adjust(1).as_markup()
    )

# ФУТБОЛ - ИГРА
@dp.callback_query(F.data.startswith("football_"), GameFootball.amount)
async def process_football_bet(callback: CallbackQuery, state: FSMContext):
    """Обработка ставки в футбол"""
    try:
        data = await state.get_data()
        amount = data['amount']
        bet_type = callback.data.split("_")[1]  # goal или miss
        
        user_id = callback.from_user.id
        
        # Проверяем баланс еще раз
        balance = db.get_user_balance(user_id)
        if amount > balance:
            await callback.answer("❌ Недостаточно средств!", show_alert=True)
            await state.clear()
            return
        
        # Списываем ставку
        db.update_user_balance(user_id, -amount)
        
        # Обновляем статистику
        db.update_user_stats(user_id, 'total_games', 1)
        db.update_user_stats(user_id, 'total_bet', amount)
        
        # Бросаем мяч
        football_message = await callback.message.answer_dice(emoji="⚽️")
        football_value = football_message.dice.value
        
        await asyncio.sleep(3)
        
        # Определяем результат
        win = False
        multiplier = 2
        
        if bet_type == "goal" and football_value >= 3:  # Гол (3-5 очков)
            win = True
        elif bet_type == "miss" and football_value <= 2:  # Мимо (1-2 очка)
            win = True
        
        win_amount = amount * multiplier if win else 0
        
        if win:
            db.update_user_balance(user_id, win_amount)
            db.update_user_stats(user_id, 'wins', 1)
            db.update_user_stats(user_id, 'total_win', win_amount)
            result_text = f"🎉 <b>ГОООЛ!</b>\nВы выиграли: {win_amount}$"
        else:
            db.update_user_stats(user_id, 'loses', 1)
            result_text = f"😞 <b>ПРОИГРЫШ</b>\nВы проиграли: {amount}$"
        
        new_balance = db.get_user_balance(user_id)
        
        bet_type_text = "Гол ⚽️" if bet_type == "goal" else "Мимо ❌"
        
        await callback.message.edit_text(
            f'<b>⚽️ Результат футбольной ставки</b>\n\n'
            f'🎯 <b>Ваша ставка:</b> {bet_type_text}\n'
            f'⚽️ <b>Результат броска:</b> {football_value} очков\n'
            f'💰 <b>Сумма ставки:</b> {amount}$\n'
            f'📈 <b>Коэффициент:</b> x{multiplier}\n\n'
            f'{result_text}\n\n'
            f'💰 <b>Новый баланс:</b> {new_balance}$',
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="⚽️ Сыграть еще", callback_data="game_football_info")],
                [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
            ]).adjust(1).as_markup()
        )
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка в process_football_bet: {e}")
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)
        await state.clear()
        # Определяем результат
        win = False
        multiplier = 2
        
        if bet_type == "goal" and football_value >= 3:  # Гол (3-5 очков)
            win = True
        elif bet_type == "miss" and football_value <= 2:  # Мимо (1-2 очка)
            win = True
        
        win_amount = amount * multiplier if win else 0
        
        if win:
            db.update_user_balance(user_id, win_amount)
            db.update_user_stats(user_id, 'wins', 1)
            db.update_user_stats(user_id, 'total_win', win_amount)
            result_text = f

