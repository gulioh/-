import datetime
import asyncio
import random

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram import F
from aiogram.filters import CommandStart, CommandObject
from aiogram.utils.markdown import hlink
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from loader import dp, db, bot, admin, lock, crypto
from keybords import *
from func import *
from config import *
from States import *
import pytz
from datetime import datetime, timedelta
import datetime as dt
from middleware import *

# Безопасное получение URL
def safe_get_url(key):
    try:
        url_data = db.get_URL()
        if url_data and url_data.get(key):
            return url_data.get(key)
    except:
        pass
    return "https://t.me/telegram"

# Проверка и инициализация БД при запуске
try:
    url_data = db.get_URL()
    if not url_data:
        print("База URL пуста, требуется инициализация")
except:
    print("Ошибка БД, требуется настройка")

admin.message.filter(IsAdmin())

@dp.message(CommandStart())
async def cmd_start(message:Message, state:FSMContext):
    db.db_start()
    db.db_settings()
    db.db_stats()
    db.db_urls()

    word = random.choice(list(captcha_dict))
    if not db.user_exists(message.from_user.id):
        start_cmd = message.text
        referi_id = str(start_cmd[7:])
        if str(referi_id) != '':
            if str(referi_id) != str(message.from_user.id):
                db.add_users(message.from_user.id, referi_id)
                await message.answer(
                    f'👋🏻 Привет {message.from_user.first_name}, чтобы убедиться что вы не робот 🤖 - пройдите капчу\n\n'
                    f'Нажми на 👉 <b>{word}</b>', reply_markup=await captcha_keybord(word))
                try:
                    await bot.send_message(referi_id,
                                           f'<b>По вашей ссылке зарегистрировался новый пользователь с id <code>{message.from_user.id}</code> @{message.from_user.username}</b>')
                except:
                    pass
            else:
                db.add_users(message.from_user.id)
                await bot.send_message(message.from_user.id, "Нельзя регистрироваться по своей ссылке")
        else:
            db.add_users(message.from_user.id)
            await message.answer(
                f'👋🏻 Привет {message.from_user.first_name}, чтобы убедиться что вы не робот 🤖 - пройдите капчу\n\n'
                f'Нажми на 👉 <b>{word}</b>', reply_markup=await captcha_keybord(word))
        await state.set_state(Captcha_users.status)
        return

    await message.answer(
        f'👋🏻 Привет {message.from_user.first_name}, чтобы убедиться что вы не робот 🤖 - пройдите капчу\n\n'
        f'Нажми на 👉 <b>{word}</b>', reply_markup=await captcha_keybord(word))
    await state.set_state(Captcha_users.status)

@dp.callback_query(F.data.startswith('Captcha'), Captcha_users.status)
async def chek_captcha(callback: CallbackQuery, state: FSMContext):
    keys = callback.data.split('|')[1]
    word = callback.data.split('|')[2]
    users_link = hlink(callback.from_user.full_name, callback.from_user.url)
    
    game_channel = safe_get_url('channals')
    game_link = hlink(NAME_CASINO, game_channel)
    
    word_new = random.choice(list(captcha_dict))
    if keys == word:
        await callback.message.delete()
        await callback.message.answer(
            f'<b>👋 Добро пожаловать {users_link} в {game_link} 🎲</b>\n\n'
            f'<b>Теперь вы можете:</b>\n'
            f'🎲 <b>Играть</b> - сделать ставку в казино\n'
            f'💸 <b>Пополнить баланс</b> - добавить средств\n'
            f'📎 <b>Реферальная программа</b> - приглашать друзей\n'
            f'💭 <b>Информация</b> - правила и инструкции\n'
            f'👤 <b>Профиль</b> - ваша статистика\n\n'
            f'<i>Используйте кнопки меню ниже ↓</i>',
            reply_markup=kb_menu(callback.from_user.id),
            disable_web_page_preview=True
        )
        await state.clear()
    else:
        await callback.answer('⚠️ Вы не прошли проверку!', show_alert=True)
        await callback.message.edit_text(text=
            f'👋🏻 Привет {callback.from_user.first_name}, чтобы убедиться что вы не робот 🤖 - пройдите капчу\n\n'
            f'Нажми на 👉 <b>{word_new}</b>', reply_markup=await captcha_keybord(word_new))

# ОБРАБОТЧИК ПОПОЛНЕНИЯ БАЛАНСА
@dp.message(F.text == '💸 Пополнить баланс')
async def add_balance_user(message: Message, state: FSMContext):
    """Пополнение баланса через Crypto Pay"""
    if not crypto:
        await message.answer("❌ Сервис пополнения временно недоступен")
        return
    
    await message.answer(
        '<b>💸 Пополнение баланса</b>\n\n'
        'Введите сумму пополнения в $ (например: 10):\n\n'
        '<i>Минимальная сумма: 1$</i>',
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
        
        if amount > 1000:
            await message.answer("❌ Максимальная сумма пополнения: 1000$")
            return
        
        user_id = message.from_user.id
        
        # Создаем инвойс через Crypto Pay
        try:
            invoice = await crypto.create_invoice(
                asset='USDT',
                amount=amount,
                description=f'Пополнение баланса для пользователя {user_id}',
                paid_btn_name='callback',
                paid_btn_url='https://t.me/your_bot',
                allow_comments=False
            )
        except Exception as e:
            await message.answer(f"❌ Ошибка создания счета: {e}")
            return
        
        # Добавляем транзакцию в БД
        db.add_transaction(
            user_id=user_id,
            transaction_type='deposit',
            amount=amount,
            status='pending',
            description=f'Invoice: {invoice.invoice_id}'
        )
        
        await message.answer(
            f'<b>💸 Счет на оплату</b>\n\n'
            f'💰 <b>Сумма:</b> {amount}$\n'
            f'💳 <b>Метод:</b> USDT (TRC20)\n'
            f'📝 <b>Статус:</b> Ожидание оплаты\n\n'
            f'<i>Оплатите счет в течение 15 минут</i>',
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="💳 Оплатить", url=invoice.bot_invoice_url)],
                [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_payment_{invoice.invoice_id}")],
                [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_payment")]
            ]).adjust(1).as_markup()
        )
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму (например: 10)")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

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
            
            # Обновляем статус транзакции
            db.add_transaction(
                user_id=user_id,
                transaction_type='deposit',
                amount=amount,
                status='completed',
                description=f'Invoice paid: {invoice_id}'
            )
            
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

@dp.callback_query(F.data == "add_balance_from_profile")
async def add_balance_from_profile(callback: CallbackQuery, state: FSMContext):
    """Пополнение баланса из профиля"""
    if not crypto:
        await callback.answer("❌ Сервис пополнения временно недоступен", show_alert=True)
        return
    
    await callback.message.answer(
        '<b>💸 Пополнение баланса</b>\n\n'
        'Введите сумму пополнения в $ (например: 10):\n\n'
        '<i>Минимальная сумма: 1$</i>',
        reply_markup=ReplyKeyboardBuilder([
            [KeyboardButton(text="❌ Отмена")]
        ]).as_markup(resize_keyboard=True)
    )
    await state.set_state(AddBalanceUser.amount)
    await callback.answer()

# ОБРАБОТЧИК КНОПКИ "🎲 Играть"
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

@dp.callback_query(F.data == "close_games")
async def close_games_menu(callback: CallbackQuery):
    """Закрытие меню игр"""
    await callback.message.delete()

# КОСТИ - ОБНОВЛЕННАЯ ВЕРСИЯ С ВЫБОРОМ СТАВКИ
@dp.callback_query(F.data == "game_dice")
async def game_dice_menu(callback: CallbackQuery, state: FSMContext):
    """Меню игры в кости"""
    balance = db.get_user_balance(callback.from_user.id)
    
    await callback.message.edit_text(
        f'<b>🎯 Игра в кости</b>\n\n'
        f'💰 <b>Баланс:</b> {balance}$\n\n'
        f'<b>Правила:</b>\n'
        f'• Ставка на число (1-6) - коэффициент x6\n'
        f'• Ставка на "Больше" (4-6) - коэффициент x2\n'
        f'• Ставка на "Меньше" (1-3) - коэффициент x2\n'
        f'• Ставка на "Чет/Нечет" - коэффициент x2\n\n'
        f'<b>Введите сумму ставки:</b>',
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
        balance = db.get_user_balance(message.from_user.id)
        
        if amount < 1:
            await message.answer("❌ Минимальная ставка: 1$")
            return
            
        if amount > balance:
            await message.answer(f"❌ Недостаточно средств. Ваш баланс: {balance}$")
            return
        
        await state.update_data(amount=amount)
        
        await message.answer(
            f'<b>🎯 Ставка в кости</b>\n\n'
            f'💰 <b>Сумма ставки:</b> {amount}$\n'
            f'<b>Выберите тип ставки:</b>',
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="🎲 На число (1-6)", callback_data="dice_number")],
                [InlineKeyboardButton(text="📈 Больше (4-6)", callback_data="dice_more")],
                [InlineKeyboardButton(text="📉 Меньше (1-3)", callback_data="dice_less")],
                [InlineKeyboardButton(text="2️⃣ Четное", callback_data="dice_even")],
                [InlineKeyboardButton(text="1️⃣ Нечетное", callback_data="dice_odd")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_game")]
            ]).adjust(2).as_markup()
        )
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму (например: 10)")

@dp.callback_query(F.data == "dice_number")
async def dice_number_bet(callback: CallbackQuery, state: FSMContext):
    """Ставка на конкретное число в костях"""
    data = await state.get_data()
    amount = data['amount']
    
    await callback.message.edit_text(
        f'<b>🎯 Ставка на число</b>\n\n'
        f'💰 <b>Сумма ставки:</b> {amount}$\n'
        f'<b>Выберите число (1-6):</b>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="1️⃣", callback_data="dice_bet_1"),
             InlineKeyboardButton(text="2️⃣", callback_data="dice_bet_2"),
             InlineKeyboardButton(text="3️⃣", callback_data="dice_bet_3")],
            [InlineKeyboardButton(text="4️⃣", callback_data="dice_bet_4"),
             InlineKeyboardButton(text="5️⃣", callback_data="dice_bet_5"),
             InlineKeyboardButton(text="6️⃣", callback_data="dice_bet_6")],
            [InlineKeyboardButton(text="❌ Назад", callback_data="game_dice")]
        ]).adjust(3).as_markup()
    )

@dp.callback_query(F.data.startswith("dice_bet_"))
async def process_dice_number_bet(callback: CallbackQuery, state: FSMContext):
    """Обработка ставки на число в костях"""
    data = await state.get_data()
    amount = data['amount']
    chosen_number = int(callback.data.split("_")[2])  # число от 1 до 6
    
    user_id = callback.from_user.id
    
    # Проверяем баланс еще раз
    balance = db.get_user_balance(user_id)
    if amount > balance:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        await state.clear()
        return
    
    # Списываем ставку с баланса
    db.update_user_balance(user_id, -amount)
    
    # Обновляем статистику
    db.update_user_stats(user_id, 'total_games', 1)
    db.update_user_stats(user_id, 'total_bet', amount)
    
    # Отправляем анимацию кубика
    dice_message = await callback.message.answer_dice(emoji="🎲")
    dice_value = dice_message.dice.value
    
    await asyncio.sleep(3)  # Ждем пока анимация кубика завершится
    
    # Определяем результат
    win = (dice_value == chosen_number)
    multiplier = 6 if win else 0
    win_amount = amount * multiplier if win else 0
    
    if win:
        # Начисляем выигрыш
        db.update_user_balance(user_id, win_amount)
        db.update_user_stats(user_id, 'wins', 1)
        db.update_user_stats(user_id, 'total_win', win_amount)
        result_text = f"🎉 <b>ПОБЕДА!</b>\nВы выиграли: {win_amount}$"
    else:
        db.update_user_stats(user_id, 'loses', 1)
        result_text = f"😞 <b>ПРОИГРЫШ</b>\nВы проиграли: {amount}$"
    
    new_balance = db.get_user_balance(user_id)
    
    await callback.message.answer(
        f'<b>🎯 Результат игры в кости</b>\n\n'
        f'🎯 <b>Ваша ставка:</b> на число {chosen_number}\n'
        f'🎲 <b>Выпало:</b> {dice_value}\n'
        f'💰 <b>Сумма ставки:</b> {amount}$\n'
        f'📈 <b>Коэффициент:</b> x{multiplier}\n\n'
        f'{result_text}\n\n'
        f'💰 <b>Новый баланс:</b> {new_balance}$\n\n'
        f'<i>Сыграть еще раз?</i>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="🎯 Сыграть еще", callback_data="game_dice")],
            [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
        ]).adjust(1).as_markup()
    )
    await state.clear()

# ОБРАБОТЧИКИ ДЛЯ ДРУГИХ ТИПОВ СТАВОК В КОСТЯХ
@dp.callback_query(F.data.in_(["dice_more", "dice_less", "dice_even", "dice_odd"]))
async def process_dice_special_bet(callback: CallbackQuery, state: FSMContext):
    """Обработка специальных ставок в костях (больше/меньше/чет/нечет)"""
    data = await state.get_data()
    amount = data['amount']
    bet_type = callback.data
    
    user_id = callback.from_user.id
    
    # Проверяем баланс еще раз
    balance = db.get_user_balance(user_id)
    if amount > balance:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        await state.clear()
        return
    
    # Списываем ставку с баланса
    db.update_user_balance(user_id, -amount)
    
    # Обновляем статистику
    db.update_user_stats(user_id, 'total_games', 1)
    db.update_user_stats(user_id, 'total_bet', amount)
    
    # Отправляем анимацию кубика
    dice_message = await callback.message.answer_dice(emoji="🎲")
    dice_value = dice_message.dice.value
    
    await asyncio.sleep(3)  # Ждем пока анимация кубика завершится
    
    # Определяем результат в зависимости от типа ставки
    win = False
    multiplier = 2
    
    if bet_type == "dice_more" and dice_value >= 4:  # Больше (4-6)
        win = True
    elif bet_type == "dice_less" and dice_value <= 3:  # Меньше (1-3)
        win = True
    elif bet_type == "dice_even" and dice_value % 2 == 0:  # Четное
        win = True
    elif bet_type == "dice_odd" and dice_value % 2 == 1:  # Нечетное
        win = True
    
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
    
    # Текст для типа ставки
    bet_type_text = {
        "dice_more": "Больше (4-6) 📈",
        "dice_less": "Меньше (1-3) 📉", 
        "dice_even": "Четное 2️⃣",
        "dice_odd": "Нечетное 1️⃣"
    }[bet_type]
    
    await callback.message.answer(
        f'<b>🎯 Результат игры в кости</b>\n\n'
        f'🎯 <b>Ваша ставка:</b> {bet_type_text}\n'
        f'🎲 <b>Выпало:</b> {dice_value}\n'
        f'💰 <b>Сумма ставки:</b> {amount}$\n'
        f'📈 <b>Коэффициент:</b> x{multiplier if win else 0}\n\n'
        f'{result_text}\n\n'
        f'💰 <b>Новый баланс:</b> {new_balance}$\n\n'
        f'<i>Сыграть еще раз?</i>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="🎯 Сыграть еще", callback_data="game_dice")],
            [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
        ]).adjust(1).as_markup()
    )
    await state.clear()

# СЛОТЫ
@dp.callback_query(F.data == "game_slots")
async def game_slots_menu(callback: CallbackQuery, state: FSMContext):
    """Меню игры в слоты"""
    balance = db.get_user_balance(callback.from_user.id)
    
    await callback.message.edit_text(
        f'<b>🎰 Игровые автоматы</b>\n\n'
        f'💰 <b>Баланс:</b> {balance}$\n\n'
        f'<b>Правила:</b>\n'
        f'• 7️⃣7️⃣7️⃣ - коэффициент x64\n'
        f'• 🍒🍒🍒 - коэффициент x5\n'
        f'• 🍋🍋🍋 - коэффициент x3\n'
        f'• 💰💰💰 - коэффициент x2\n\n'
        f'<b>Введите сумму ставки:</b>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="❌ Назад", callback_data="back_to_games")]
        ]).as_markup()
    )
    await state.set_state(GameSlots.amount)

@dp.message(GameSlots.amount)
async def process_slots_amount(message: Message, state: FSMContext):
    """Обработка суммы ставки в слотах"""
    try:
        amount = float(message.text)
        balance = db.get_user_balance(message.from_user.id)
        
        if amount < 1:
            await message.answer("❌ Минимальная ставка: 1$")
            return
            
        if amount > balance:
            await message.answer(f"❌ Недостаточно средств. Ваш баланс: {balance}$")
            return
        
        user_id = message.from_user.id
        
        # Списываем ставку
        db.update_user_balance(user_id, -amount)
        
        # Обновляем статистику
        db.update_user_stats(user_id, 'total_games', 1)
        db.update_user_stats(user_id, 'total_bet', amount)
        
        # Крутим слоты
        slots_message = await message.answer_dice(emoji="🎰")
        slots_value = slots_message.dice.value
        
        await asyncio.sleep(3)  # Ждем анимацию
        
        # Определяем выигрыш
        win = False
        multiplier = 0
        
        if slots_value == 64:  # 777
            win = True
            multiplier = 64
        elif slots_value == 1:  # Вишни
            win = True
            multiplier = 5
        elif slots_value == 22:  # Лимон
            win = True
            multiplier = 3
        elif slots_value == 43:  # Банан
            win = True
            multiplier = 2
        
        win_amount = amount * multiplier if win else 0
        
        if win:
            db.update_user_balance(user_id, win_amount)
            db.update_user_stats(user_id, 'wins', 1)
            db.update_user_stats(user_id, 'total_win', win_amount)
            result_text = f"🎉 <b>ДЖЕКПОТ!</b>\nВы выиграли: {win_amount}$"
        else:
            db.update_user_stats(user_id, 'loses', 1)
            result_text = f"😞 <b>ПРОИГРЫШ</b>\nВы проиграли: {amount}$"
        
        new_balance = db.get_user_balance(user_id)
        
        await message.answer(
            f'<b>🎰 Результат игры в слоты</b>\n\n'
            f'🎰 <b>Результат:</b> {get_slots_name(slots_value)}\n'
            f'💰 <b>Сумма ставки:</b> {amount}$\n'
            f'📈 <b>Коэффициент:</b> x{multiplier if win else 0}\n\n'
            f'{result_text}\n\n'
            f'💰 <b>Новый баланс:</b> {new_balance}$\n\n'
            f'<i>Сыграть еще раз?</i>',
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="🎰 Сыграть еще", callback_data="game_slots")],
                [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
            ]).adjust(1).as_markup()
        )
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму (например: 10)")

# ФУТБОЛ - ИСПРАВЛЕННАЯ ВЕРСИЯ
@dp.callback_query(F.data == "game_football")
async def game_football_menu(callback: CallbackQuery, state: FSMContext):
    """Меню игры в футбол"""
    balance = db.get_user_balance(callback.from_user.id)
    
    await callback.message.edit_text(
        f'<b>⚽️ Футбол</b>\n\n'
        f'💰 <b>Баланс:</b> {balance}$\n\n'
        f'<b>Правила:</b>\n'
        f'• Ставка на "Гол" (3-5 очков) - коэффициент x2\n'
        f'• Ставка на "Мимо" (1-2 очка) - коэффициент x2\n\n'
        f'<b>Введите сумму ставки:</b>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="❌ Назад", callback_data="back_to_games")]
        ]).as_markup()
    )
    await state.set_state(GameFootball.amount)

@dp.message(GameFootball.amount)
async def process_football_amount(message: Message, state: FSMContext):
    """Обработка суммы ставки в футбол"""
    try:
        amount = float(message.text)
        balance = db.get_user_balance(message.from_user.id)
        
        if amount < 1:
            await message.answer("❌ Минимальная ставка: 1$")
            return
            
        if amount > balance:
            await message.answer(f"❌ Недостаточно средств. Ваш баланс: {balance}$")
            return
        
        await state.update_data(amount=amount)
        
        await message.answer(
            f'<b>⚽️ Ставка в футбол</b>\n\n'
            f'💰 <b>Сумма ставки:</b> {amount}$\n'
            f'<b>Выберите тип ставки:</b>',
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="⚽️ Гол (3-5 очков)", callback_data="football_goal")],
                [InlineKeyboardButton(text="❌ Мимо (1-2 очка)", callback_data="football_miss")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_game")]
            ]).adjust(1).as_markup()
        )
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму (например: 10)")

@dp.callback_query(F.data.startswith("football_"))
async def process_football_bet(callback: CallbackQuery, state: FSMContext):
    """Обработка ставки в футбол"""
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
    
    await asyncio.sleep(3)  # Ждем анимацию
    
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
    
    await callback.message.answer(
        f'<b>⚽️ Результат игры в футбол</b>\n\n'
        f'🎯 <b>Ваша ставка:</b> {bet_type_text}\n'
        f'⚽️ <b>Результат:</b> {football_value} очков\n'
        f'💰 <b>Сумма ставки:</b> {amount}$\n'
        f'📈 <b>Коэффициент:</b> x{multiplier if win else 0}\n\n'
        f'{result_text}\n\n'
        f'💰 <b>Новый баланс:</b> {new_balance}$\n\n'
        f'<i>Сыграть еще раз?</i>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="⚽️ Сыграть еще", callback_data="game_football")],
            [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
        ]).adjust(1).as_markup()
    )
    await state.clear()

# КНБ - ИСПРАВЛЕННАЯ ВЕРСИЯ
@dp.callback_query(F.data == "game_knb")
async def game_knb_menu(callback: CallbackQuery, state: FSMContext):
    """Меню игры в камень-ножницы-бумага"""
    balance = db.get_user_balance(callback.from_user.id)
    
    await callback.message.edit_text(
        f'<b>🪨✂️📄 Камень-Ножницы-Бумага</b>\n\n'
        f'💰 <b>Баланс:</b> {balance}$\n\n'
        f'<b>Правила:</b>\n'
        f'• Победа - коэффициент x2\n'
        f'• Ничья - возврат ставки\n'
        f'• Проигрыш - потеря ставки\n\n'
        f'<b>Введите сумму ставки:</b>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="❌ Назад", callback_data="back_to_games")]
        ]).as_markup()
    )
    await state.set_state(GameKNB.amount)

@dp.message(GameKNB.amount)
async def process_knb_amount(message: Message, state: FSMContext):
    """Обработка суммы ставки в КНБ"""
    try:
        amount = float(message.text)
        balance = db.get_user_balance(message.from_user.id)
        
        if amount < 1:
            await message.answer("❌ Минимальная ставка: 1$")
            return
            
        if amount > balance:
            await message.answer(f"❌ Недостаточно средств. Ваш баланс: {balance}$")
            return
        
        await state.update_data(amount=amount)
        
        await message.answer(
            f'<b>🪨✂️📄 Ставка в КНБ</b>\n\n'
            f'💰 <b>Сумма ставки:</b> {amount}$\n'
            f'<b>Выберите ваш ход:</b>',
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="🪨 Камень", callback_data="knb_rock")],
                [InlineKeyboardButton(text="✂️ Ножницы", callback_data="knb_scissors")],
                [InlineKeyboardButton(text="📄 Бумага", callback_data="knb_paper")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_game")]
            ]).adjust(2).as_markup()
        )
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму (например: 10)")

@dp.callback_query(F.data.startswith("knb_"))
async def process_knb_bet(callback: CallbackQuery, state: FSMContext):
    """Обработка ставки в КНБ"""
    data = await state.get_data()
    amount = data['amount']
    user_choice = callback.data.split("_")[1]  # rock, scissors, paper
    
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
    
    # Бот делает ход
    bot_choice = random.choice(["rock", "scissors", "paper"])
    
    # Определяем результат
    result = determine_knb_winner(user_choice, bot_choice)
    multiplier = 2 if result == "win" else 0
    win_amount = amount * multiplier if result == "win" else amount if result == "draw" else 0
    
    if result == "win":
        db.update_user_balance(user_id, win_amount)
        db.update_user_stats(user_id, 'wins', 1)
        db.update_user_stats(user_id, 'total_win', win_amount)
        result_text = f"🎉 <b>ПОБЕДА!</b>\nВы выиграли: {win_amount}$"
    elif result == "draw":
        db.update_user_balance(user_id, amount)  # Возврат ставки
        result_text = f"🤝 <b>НИЧЬЯ</b>\nСтавка возвращена"
    else:
        db.update_user_stats(user_id, 'loses', 1)
        result_text = f"😞 <b>ПРОИГРЫШ</b>\nВы проиграли: {amount}$"
    
    new_balance = db.get_user_balance(user_id)
    
    await callback.message.answer(
        f'<b>🪨✂️📄 Результат игры в КНБ</b>\n\n'
        f'👤 <b>Ваш ход:</b> {get_knb_emoji(user_choice)} {get_knb_name(user_choice)}\n'
        f'🤖 <b>Ход бота:</b> {get_knb_emoji(bot_choice)} {get_knb_name(bot_choice)}\n'
        f'💰 <b>Сумма ставки:</b> {amount}$\n'
        f'📈 <b>Коэффициент:</b> x{multiplier}\n\n'
        f'{result_text}\n\n'
        f'💰 <b>Новый баланс:</b> {new_balance}$\n\n'
        f'<i>Сыграть еще раз?</i>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="🪨✂️📄 Сыграть еще", callback_data="game_knb")],
            [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
        ]).adjust(1).as_markup()
    )
    await state.clear()

@dp.callback_query(F.data == "back_to_games")
async def back_to_games(callback: CallbackQuery):
    """Возврат в меню игр"""
    await play_game_menu(callback.message)

@dp.callback_query(F.data == "cancel_game")
async def cancel_game(callback: CallbackQuery, state: FSMContext):
    """Отмена игры"""
    await state.clear()
    await callback.message.edit_text("❌ Игра отменена")
    await play_game_menu(callback.message)

# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
def get_slots_name(value):
    """Получение названия комбинации слотов"""
    if value == 64: return "7️⃣7️⃣7️⃣"
    elif value == 1: return "🍒🍒🍒" 
    elif value == 22: return "🍋🍋🍋"
    elif value == 43: return "💰💰💰"
    else: return "Проигрыш"

def get_knb_name(choice):
    """Получение названия для КНБ"""
    if choice == "rock": return "Камень"
    elif choice == "scissors": return "Ножницы"
    elif choice == "paper": return "Бумага"
    return ""

def get_knb_emoji(choice):
    """Получение emoji для КНБ"""
    if choice == "rock": return "🪨"
    elif choice == "scissors": return "✂️"
    elif choice == "paper": return "📄"
    return ""

def determine_knb_winner(user, bot):
    """Определение победителя в КНБ"""
    if user == bot:
        return "draw"
    elif (user == "rock" and bot == "scissors") or \
         (user == "scissors" and bot == "paper") or \
         (user == "paper" and bot == "rock"):
        return "win"
    else:
        return "lose"

# ОСТАЛЬНЫЕ ОБРАБОТЧИКИ (профиль, рефералы, админка и т.д.)
@dp.message(F.text == '📎 Реферальная программа')
async def referral_program(message: Message):
    """Реферальная программа"""
    user_id = message.from_user.id
    ref_count = db.count_ref(user_id)
    ref_earnings = db.refka_cheks_money(user_id)
    ref_link = f"https://t.me/{NICNAME}?start={user_id}"
    
    await message.answer(
        f'<b>📎 Реферальная программа</b>\n\n'
        f'🔗 <b>Ваша реферальная ссылка:</b>\n'
        f'<code>{ref_link}</code>\n\n'
        f'📊 <b>Статистика:</b>\n'
        f'• 👥 Рефералов: <code>{ref_count}</code>\n'
        f'• 💰 Заработано: <code>{ref_earnings}$</code>\n\n'
        f'<b>Как это работает:</b>\n'
        f'• Приглашайте друзей по вашей ссылке\n'
        f'• Получайте {lose_withdraw}% с их проигрышей\n'
        f'• Выплаты происходят автоматически\n\n'
        f'<i>Минимальная ставка реферала: {min_stavka_referal}$</i>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="📎 Поделиться ссылкой", 
                               url=f"https://t.me/share/url?url={ref_link}&text=Присоединяйся%20к%20казино!")],
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_referral")]
        ]).as_markup(),
        disable_web_page_preview=True
    )

@dp.message(F.text == '👤 Профиль')
async def profile_handler(message: Message):
    """Показ профиля пользователя"""
    user_id = message.from_user.id
    balance = db.get_user_balance(user_id)
    ref_count = db.count_ref(user_id)
    ref_earnings = db.refka_cheks_money(user_id)
    
    # Получаем информацию о пользователе
    username = f"@{message.from_user.username}" if message.from_user.username else "Не указан"
    first_name = message.from_user.first_name or "Пользователь"
    
    # Получаем статистику игр
    user_stats = db.all_stats_users(user_id)
    total_games = user_stats[0] if user_stats else 0
    wins = user_stats[1] if user_stats else 0
    loses = user_stats[2] if user_stats else 0
    
    # Рассчитываем процент побед
    win_rate = (wins / total_games * 100) if total_games > 0 else 0
    
    # Реферальная ссылка
    ref_link = f"https://t.me/{NICNAME}?start={user_id}"
    
    await message.answer(
        f'<b>👤 Профиль игрока</b>\n\n'
        f'🆔 <b>ID:</b> <code>{user_id}</code>\n'
        f'👤 <b>Имя:</b> {first_name}\n'
        f'📱 <b>Username:</b> {username}\n\n'
        f'💰 <b>Баланс:</b> <code>{balance}$</code>\n\n'
        f'📊 <b>Статистика игр:</b>\n'
        f'• 🎮 Всего игр: <code>{total_games}</code>\n'
        f'• ✅ Побед: <code>{wins}</code>\n'
        f'• ❌ Поражений: <code>{loses}</code>\n'
        f'• 📈 Процент побед: <code>{win_rate:.1f}%</code>\n\n'
        f'👥 <b>Реферальная программа:</b>\n'
        f'• 👤 Рефералов: <code>{ref_count}</code>\n'
        f'• 💰 Заработано: <code>{ref_earnings}$</code>\n\n'
        f'🔗 <b>Реферальная ссылка:</b>\n'
        f'<code>{ref_link}</code>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="💸 Пополнить баланс", callback_data="add_balance_from_profile")],
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_profile")],
            [InlineKeyboardButton(text="📎 Рефералы", callback_data="show_referrals")]
        ]).adjust(2).as_markup(),
        disable_web_page_preview=True
    )

@dp.callback_query(F.data == "refresh_profile")
async def refresh_profile(callback: CallbackQuery):
    """Обновление профиля"""
    await profile_handler(callback.message)

@dp.callback_query(F.data == "refresh_referral")
async def refresh_referral(callback: CallbackQuery):
    """Обновление реферальной статистики"""
    await referral_program(callback.message)

@dp.message(F.text == '👑 Админка')
async def admin_panel(message: Message):
    """Админка из сообщения"""
    if message.from_user.id not in ADMIN:
        await message.answer("❌ У вас нет доступа к админ панели")
        return
    
    casino_balance = db.get_casino_balance()
        
    await message.answer(
        text='<b>👑 Админ панель</b>\n\n'
             f'💰 <b>Баланс казино:</b> <code>{casino_balance}$</code>\n\n'
             f'<i>Выберите действие:</i>',
        reply_markup=kb_admin()
    )

@dp.callback_query(F.data == 'back_admin')
async def back_admin_func(callback: CallbackQuery, state: FSMContext):
    """Возврат в админ меню из callback"""
    if callback.from_user.id not in ADMIN:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await state.clear()
    casino_balance = db.get_casino_balance()
        
    await callback.message.edit_text(
        text='<b>👑 Админ панель</b>\n\n'
             f'💰 <b>Баланс казино:</b> <code>{casino_balance}$</code>\n\n'
             f'<i>Выберите действие:</i>',
        reply_markup=kb_admin()
    )

# ОСТАЛЬНЫЕ АДМИНСКИЕ ФУНКЦИИ...

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await set_default_commands()
    dp.update.outer_middleware(LoggingUsers())
    dp.include_router(admin)
    await scheduler_jobs()
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
