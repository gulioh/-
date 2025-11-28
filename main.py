import datetime
import asyncio
import random

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
        f'<b>📞 Поддержка:</b> {ADMIN_USERNAME}\n\n'
        f'<b>Доступные игры:</b>\n'
        f'🎯 Кости\n'
        f'🎰 Слоты\n'
        f'⚽️ Футбол\n'
        f'🪨✂️📄 Камень-Ножницы-Бумага\n\n'
        f'<b>Минимальная ставка:</b> 1$\n'
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

# ОБРАБОТЧИКИ АДМИНКИ
@dp.callback_query(F.data == "back_admin")
async def back_admin_handler(callback: CallbackQuery):
    """Возврат в админ-панель"""
    if callback.from_user.id not in ADMIN:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        '<b>👑 Панель администратора</b>\n\n'
        'Выберите действие:',
        reply_markup=kb_admin()
    )

@dp.callback_query(F.data == "stats_project")
async def stats_project_handler(callback: CallbackQuery):
    """Статистика проекта"""
    if callback.from_user.id not in ADMIN:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        stats = db.all_stats()
        day_stats = db.all_stats_day()
        
        if stats and day_stats:
            total_plays, total_wins, total_loses, total_win_amount, total_lose_amount, total_users = stats
            day_plays, day_wins, day_loses, day_win_amount, day_lose_amount = day_stats
            
            await callback.message.edit_text(
                f'<b>📊 Статистика проекта</b>\n\n'
                f'<b>👥 Пользователи:</b>\n'
                f'┖ <b>Всего:</b> {total_users} чел.\n\n'
                f'<b>🎮 За все время:</b>\n'
                f'┠ <b>Игр:</b> {total_plays}\n'
                f'┠ <b>Побед:</b> {total_wins}\n'
                f'┠ <b>Поражений:</b> {total_loses}\n'
                f'┠ <b>Выиграно:</b> {total_win_amount}$\n'
                f'┖ <b>Проиграно:</b> {total_lose_amount}$\n\n'
                f'<b>📅 За сегодня:</b>\n'
                f'┠ <b>Игр:</b> {day_plays}\n'
                f'┠ <b>Побед:</b> {day_wins}\n'
                f'┠ <b>Поражений:</b> {day_loses}\n'
                f'┠ <b>Выиграно:</b> {day_win_amount}$\n'
                f'┖ <b>Проиграно:</b> {day_lose_amount}$',
                reply_markup=kb_back_admin()
            )
    except Exception as e:
        await callback.message.edit_text(
            f'❌ Ошибка получения статистики: {e}',
            reply_markup=kb_back_admin()
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
            [InlineKeyboardButton(text="🎯 Кости", callback_data="game_dice")],
            [InlineKeyboardButton(text="🎰 Слоты", callback_data="game_slots")],
            [InlineKeyboardButton(text="⚽️ Футбол", callback_data="game_football")],
            [InlineKeyboardButton(text="🪨✂️📄 КНБ", callback_data="game_knb")],
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

# КОСТИ
@dp.callback_query(F.data == "game_dice")
async def game_dice_menu(callback: CallbackQuery, state: FSMContext):
    """Меню игры в кости"""
    balance = db.get_user_balance(callback.from_user.id)
    
    if balance < 1:
        await callback.answer("❌ Недостаточно средств. Минимальная ставка: 1$", show_alert=True)
        return
    
    await callback.message.edit_text(
        f'<b>🎯 Игра в кости</b>\n\n'
        f'💰 <b>Баланс:</b> {balance}$\n\n'
        f'<b>Введите сумму ставки:</b>\n'
        f'<i>Минимальная ставка: 1$</i>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="❌ Назад", callback_data="back_to_games")]
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
        
        if amount < 1:
            await message.answer("❌ Минимальная ставка: 1$")
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
                [InlineKeyboardButton(text="🎯 Сыграть еще", callback_data="game_dice")],
                [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
            ]).adjust(1).as_markup()
        )
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму (например: 10)")

# ДОБАВЬТЕ АНАЛОГИЧНЫЕ ОБРАБОТЧИКИ ДЛЯ ДРУГИХ ИГР (слоты, футбол, КНБ)
# Для простоты можно скопировать логику игры в кости и адаптировать

async def main():
    """Запуск бота"""
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
