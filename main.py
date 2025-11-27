import datetime
import asyncio
import random

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram import F
from aiogram.filters import CommandStart, CommandObject
from aiogram.utils.markdown import hlink
from aiogram.utils.keyboard import InlineKeyboardBuilder

from loader import dp, db, bot, admin, lock
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
            f'💸 <b>Пополнить баланс</b> - добавить средства\n'
            f'📎 <b>Реферальная программа</b> - приглашать друзей\n'
            f'💭 <b>Информация</b> - правила и инструкции\n\n'
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

@dp.message(F.text == '📎 Реферальная программа')
async def stats_adm(message: Message):
    await message.answer(f'<b>📎 Ваша реферальная ссылка:\n'
                         f'https://t.me/{NICNAME}?start={message.from_user.id}\n\n'
                         f'👥 Количество рефералов: <code>{db.count_ref(message.from_user.id)}</code>\n'
                         f'💵 Заработано с рефералов: <code>{db.refka_cheks_money(message.from_user.id)}</code>$\n\n'
                         f'❓ Как работает реферальная программа:\n'
                         f'Вы будете получать {lose_withdraw}% с каждого проигрыша своего реферала.\n'
                         f'Начисление происходит автоматически на ваш кошелек CryptoBot\n\n'
                         f'⚠️ Минимальная ставка реферала должна составлять: {min_stavka_referal}$</b>',
                         reply_markup=kb_url_Channel())

@dp.message(F.text == '💭 Информация')
async def info_func(message:Message):
    game_channel = safe_get_url('channals')
    await message.answer(f'<b>💭 Информация о проекте {hlink(title=NAME_CASINO, url=game_channel)}</b>', 
                         reply_markup=kb_info(), disable_web_page_preview=True)

# ДОБАВЬТЕ ЭТИ ОБРАБОТЧИКИ ИГР

@dp.message(F.text == '🎲 Играть')
async def play_game_menu(message: Message):
    """Меню выбора игры"""
    balance = db.get_user_balance(message.from_user.id)
    
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
            [InlineKeyboardButton(text="🪨✂️📄 КНБ", callback_data="game_knb")]
        ]).as_markup()
    )

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
        
        if amount < 0.1:
            await message.answer("❌ Минимальная ставка:0.1$")
            return
            
        if amount > balance:
            await message.answer(f"❌ Недостаточно средств. Ваш баланс: {balance}$")
            return
        
        await state.update_data(amount=amount)
        
        await message.answer(
            f'<b>🎯 Ставка в кости</b>\n\n'
            f'💰 <b>Сумма:</b> {amount}$\n'
            f'<b>Выберите тип ставки:</b>',
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣", callback_data="dice_number")],
                [InlineKeyboardButton(text="📈 Больше (4-6)", callback_data="dice_more")],
                [InlineKeyboardButton(text="📉 Меньше (1-3)", callback_data="dice_less")],
                [InlineKeyboardButton(text="2️⃣4️⃣6️⃣ Четное", callback_data="dice_even")],
                [InlineKeyboardButton(text="1️⃣3️⃣5️⃣ Нечетное", callback_data="dice_odd")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_game")]
            ]).as_markup()
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
        f'💰 <b>Сумма:</b> {amount}$\n'
        f'<b>Выберите число (1-6):</b>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="1️⃣", callback_data="dice_bet_1"),
             InlineKeyboardButton(text="2️⃣", callback_data="dice_bet_2"),
             InlineKeyboardButton(text="3️⃣", callback_data="dice_bet_3")],
            [InlineKeyboardButton(text="4️⃣", callback_data="dice_bet_4"),
             InlineKeyboardButton(text="5️⃣", callback_data="dice_bet_5"),
             InlineKeyboardButton(text="6️⃣", callback_data="dice_bet_6")],
            [InlineKeyboardButton(text="❌ Назад", callback_data="game_dice")]
        ]).as_markup()
    )

@dp.callback_query(F.data.startswith("dice_bet_"))
async def process_dice_bet(callback: CallbackQuery, state: FSMContext):
    """Обработка ставки в кости"""
    data = await state.get_data()
    amount = data['amount']
    bet_type = callback.data.split("_")[2]  # число от 1 до 6
    
    # Списываем ставку с баланса
    db.update_user_balance(callback.from_user.id, -amount)
    
    # Отправляем анимацию кубика
    dice_message = await callback.message.answer_dice(emoji="🎲")
    dice_value = dice_message.dice.value
    
    # Определяем результат
    chosen_number = int(bet_type)
    win = (dice_value == chosen_number)
    multiplier = 6 if win else 0
    win_amount = amount * multiplier if win else 0
    
    if win:
        # Начисляем выигрыш
        db.update_user_balance(callback.from_user.id, win_amount)
        result_text = f"🎉 <b>ПОБЕДА!</b>\nВы выиграли: {win_amount}$"
    else:
        result_text = f"😞 <b>ПРОИГРЫШ</b>\nВы проиграли: {amount}$"
    
    await asyncio.sleep(3)  # Ждем пока анимация кубика завершится
    
    new_balance = db.get_user_balance(callback.from_user.id)
    
    await callback.message.answer(
        f'<b>🎯 Результат игры в кости</b>\n\n'
        f'🎲 <b>Выпало:</b> {dice_value}\n'
        f'🎯 <b>Ваша ставка:</b> на {chosen_number}\n'
        f'💰 <b>Сумма ставки:</b> {amount}$\n'
        f'📈 <b>Коэффициент:</b> x{multiplier}\n\n'
        f'{result_text}\n\n'
        f'💰 <b>Новый баланс:</b> {new_balance}$\n\n'
        f'<i>Сыграть еще раз?</i>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="🎯 Сыграть еще", callback_data="game_dice")],
            [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
        ]).as_markup()
    )
    await state.clear()

@dp.callback_query(F.data == "back_to_games")
async def back_to_games(callback: CallbackQuery, state: FSMContext):
    """Возврат в меню игр"""
    await state.clear()
    await play_game_menu(callback.message)

@dp.callback_query(F.data == "cancel_game")
async def cancel_game(callback: CallbackQuery, state: FSMContext):
    """Отмена игры"""
    await state.clear()
    await callback.message.edit_text("❌ Игра отменена")
    await play_game_menu(callback.message)

# === ДОБАВЬТЕ ЭТОТ КОД ДЛЯ ОСТАЛЬНЫХ ИГР ===

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
        
        if amount < 0.1:
            await message.answer("❌ Минимальная ставка: 0.1$")
            return
            
        if amount > balance:
            await message.answer(f"❌ Недостаточно средств. Ваш баланс: {balance}$")
            return
        
        # Списываем ставку
        db.update_user_balance(message.from_user.id, -amount)
        
        # Крутим слоты
        slots_message = await message.answer_dice(emoji="🎰")
        slots_value = slots_message.dice.value
        
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
            db.update_user_balance(message.from_user.id, win_amount)
            result_text = f"🎉 <b>ДЖЕКПОТ!</b>\nВы выиграли: {win_amount}$"
        else:
            result_text = f"😞 <b>ПРОИГРЫШ</b>\nВы проиграли: {amount}$"
        
        await asyncio.sleep(3)  # Ждем анимацию
        
        new_balance = db.get_user_balance(message.from_user.id)
        
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
            ]).as_markup()
        )
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму (например: 10)")

@dp.callback_query(F.data == "game_football")
async def game_football_menu(callback: CallbackQuery, state: FSMContext):
    """Меню игры в футбол"""
    balance = db.get_user_balance(callback.from_user.id)
    
    await callback.message.edit_text(
        f'<b>⚽️ Футбол</b>\n\n'
        f'💰 <b>Баланс:</b> {balance}$\n\n'
        f'<b>Правила:</b>\n'
        f'• Ставка на "Гол" (3-5) - коэффициент x2\n'
        f'• Ставка на "Мимо" (1-2) - коэффициент x2\n\n'
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
        
        if amount < 0.1:
            await message.answer("❌ Минимальная ставка: 0.1$")
            return
            
        if amount > balance:
            await message.answer(f"❌ Недостаточно средств. Ваш баланс: {balance}$")
            return
        
        await state.update_data(amount=amount)
        
        await message.answer(
            f'<b>⚽️ Ставка в футбол</b>\n\n'
            f'💰 <b>Сумма:</b> {amount}$\n'
            f'<b>Выберите тип ставки:</b>',
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="⚽️ Гол", callback_data="football_goal")],
                [InlineKeyboardButton(text="❌ Мимо", callback_data="football_miss")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_game")]
            ]).as_markup()
        )
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму (например: 10)")

@dp.callback_query(F.data.startswith("football_"))
async def process_football_bet(callback: CallbackQuery, state: FSMContext):
    """Обработка ставки в футбол"""
    data = await state.get_data()
    amount = data['amount']
    bet_type = callback.data.split("_")[1]  # goal или miss
    
    # Списываем ставку
    db.update_user_balance(callback.from_user.id, -amount)
    
    # Бросаем мяч
    football_message = await callback.message.answer_dice(emoji="⚽️")
    football_value = football_message.dice.value
    
    # Определяем результат
    win = False
    multiplier = 2
    
    if bet_type == "goal" and football_value >= 3:  # Гол
        win = True
    elif bet_type == "miss" and football_value <= 2:  # Мимо
        win = True
    else:
        win = False
    
    win_amount = amount * multiplier if win else 0
    
    if win:
        db.update_user_balance(callback.from_user.id, win_amount)
        result_text = f"🎉 <b>ГОООЛ!</b>\nВы выиграли: {win_amount}$"
    else:
        result_text = f"😞 <b>ПРОИГРЫШ</b>\nВы проиграли: {amount}$"
    
    await asyncio.sleep(3)  # Ждем анимацию
    
    new_balance = db.get_user_balance(callback.from_user.id)
    
    await callback.message.answer(
        f'<b>⚽️ Результат игры в футбол</b>\n\n'
        f'⚽️ <b>Результат:</b> {football_value} очков\n'
        f'🎯 <b>Ваша ставка:</b> на {bet_type}\n'
        f'💰 <b>Сумма ставки:</b> {amount}$\n'
        f'📈 <b>Коэффициент:</b> x{multiplier if win else 0}\n\n'
        f'{result_text}\n\n'
        f'💰 <b>Новый баланс:</b> {new_balance}$\n\n'
        f'<i>Сыграть еще раз?</i>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="⚽️ Сыграть еще", callback_data="game_football")],
            [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
        ]).as_markup()
    )
    await state.clear()

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
        
        if amount < 0.1:
            await message.answer("❌ Минимальная ставка: 0.1$")
            return
            
        if amount > balance:
            await message.answer(f"❌ Недостаточно средств. Ваш баланс: {balance}$")
            return
        
        await state.update_data(amount=amount)
        
        await message.answer(
            f'<b>🪨✂️📄 Ставка в КНБ</b>\n\n'
            f'💰 <b>Сумма:</b> {amount}$\n'
            f'<b>Выберите ваш ход:</b>',
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="🪨 Камень", callback_data="knb_rock")],
                [InlineKeyboardButton(text="✂️ Ножницы", callback_data="knb_scissors")],
                [InlineKeyboardButton(text="📄 Бумага", callback_data="knb_paper")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_game")]
            ]).as_markup()
        )
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму (например: 10)")

@dp.callback_query(F.data.startswith("knb_"))
async def process_knb_bet(callback: CallbackQuery, state: FSMContext):
    """Обработка ставки в КНБ"""
    data = await state.get_data()
    amount = data['amount']
    user_choice = callback.data.split("_")[1]  # rock, scissors, paper
    
    # Списываем ставку
    db.update_user_balance(callback.from_user.id, -amount)
    
    # Бот делает ход
    bot_choice = random.choice(["rock", "scissors", "paper"])
    
    # Определяем результат
    result = determine_knb_winner(user_choice, bot_choice)
    multiplier = 2 if result == "win" else 0
    win_amount = amount * multiplier if result == "win" else amount if result == "draw" else 0
    
    if result == "win":
        db.update_user_balance(callback.from_user.id, win_amount)
        result_text = f"🎉 <b>ПОБЕДА!</b>\nВы выиграли: {win_amount}$"
    elif result == "draw":
        db.update_user_balance(callback.from_user.id, amount)  # Возврат ставки
        result_text = f"🤝 <b>НИЧЬЯ</b>\nСтавка возвращена"
    else:
        result_text = f"😞 <b>ПРОИГРЫШ</b>\nВы проиграли: {amount}$"
    
    await callback.message.answer(
        f'<b>🪨✂️📄 Результат игры в КНБ</b>\n\n'
        f'👤 <b>Ваш ход:</b> {get_knb_emoji(user_choice)}\n'
        f'🤖 <b>Ход бота:</b> {get_knb_emoji(bot_choice)}\n'
        f'💰 <b>Сумма ставки:</b> {amount}$\n'
        f'📈 <b>Коэффициент:</b> x{multiplier}\n\n'
        f'{result_text}\n\n'
        f'<i>Сыграть еще раз?</i>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="🪨✂️📄 Сыграть еще", callback_data="game_knb")],
            [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
        ]).as_markup()
    )
    await state.clear()

# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ИГР

def get_slots_name(value):
    """Получение названия комбинации слотов"""
    if value == 64: return "7️⃣7️⃣7️⃣"
    elif value == 1: return "🍒🍒🍒" 
    elif value == 22: return "🍋🍋🍋"
    elif value == 43: return "💰💰💰"
    else: return "Проигрыш"

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

# === КОНЕЦ КОДА ДЛЯ ИГР ===

# АДМИНСКИЕ ФУНКЦИИ (ваш существующий код)

# ДОБАВЬТЕ ОБРАБОТЧИК ПОПОЛНЕНИЯ БАЛАНСА

@dp.message(F.text == '💸 Пополнить баланс')
async def add_balance_user(message: Message, state: FSMContext):
    """Пополнение баланса через Crypto Bot"""
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
        
        # Добавляем транзакцию в БД
        db.add_transaction(
            user_id=message.from_user.id,
            transaction_type='deposit',
            amount=amount,
            status='pending',
            description=f'Invoice: {invoice.invoice_id}'
        )
        
        await message.answer(
            f'<b>💸 Счет на оплату</b>\n\n'
            f'<b>Сумма:</b> {amount}$\n'
            f'<b>Статус:</b> Ожидание оплаты\n\n'
            f'Оплатите счет в течение 15 минут',
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="💳 Оплатить", url=invoice.bot_invoice_url)],
                [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_payment_{invoice.invoice_id}")]
            ]).as_markup()
        )
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму (например: 10)")
    except Exception as e:
        await message.answer(f"❌ Ошибка создания счета: {e}")

@dp.callback_query(F.data == "game_dice")
async def game_dice_menu(callback: CallbackQuery, state: FSMContext):
    """Меню игры в кости"""
    await callback.message.edit_text(
        '<b>🎯 Игра в кости</b>\n\n'
        'Правила:\n'
        '• Ставка на число (1-6) - коэффициент x6\n'
        '• Ставка на "Больше" (4-6) - коэффициент x2\n'
        '• Ставка на "Меньше" (1-3) - коэффициент x2\n'
        '• Ставка на "Чет/Нечет" - коэффициент x2\n\n'
        'Введите сумму ставки:',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="❌ Назад", callback_data="back_to_games")]
        ]).as_markup()
    )
    await state.set_state(GameDice.amount)


@dp.message(F.text == '👑 Админка')
async def admin_panel(message: Message):
    """Проверка админских прав и показ админки"""
    if message.from_user.id not in ADMIN:
        await message.answer("❌ У вас нет доступа к админ панели")
        return
    
    try:
        balance_data = await crypto.get_balance()
        balance = balance_data[0].available if balance_data else 0
    except:
        balance = 0
        
    await message.answer(
        text='<b>👑 Админ панель</b>\n\n'
             f'💰 <b>Баланс казино:</b> <code>{round(float(balance), 2)}$</code>\n\n'
             f'<i>Выберите действие:</i>',
        reply_markup=kb_admin()
    )

# ОБНОВИТЕ ВСЕ АДМИНСКИЕ ОБРАБОТЧИКИ - добавьте проверку прав:

@dp.callback_query(F.data == 'stats_project')
async def stats_adm(callback: CallbackQuery):
    """Статистика проекта"""
    if callback.from_user.id not in ADMIN:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        stats = db.all_stats() or [0, 0, 0, 0, 0, 0]
        balance_data = await crypto.get_balance()
        balance = balance_data[0].available if balance_data else 0
        info_day = db.all_stats_day() or [0, 0, 0, 0, 0]
    except:
        stats = [0, 0, 0, 0, 0, 0]
        balance = 0
        info_day = [0, 0, 0, 0, 0]
        
    # ... остальной код статистики

@dp.callback_query(F.data == 'stats_user')
async def stats_adm(callback: CallbackQuery, state: FSMContext):
    """Статистика пользователя"""
    if callback.from_user.id not in ADMIN:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text('<b>Введите id игрока</b>', reply_markup=kb_back_admin())
    await state.set_state(UserStats.user_id)

@dp.callback_query(F.data == 'add_balance')
async def stats_adm(callback: CallbackQuery, state: FSMContext):
    """Пополнение баланса казино"""
    if callback.from_user.id not in ADMIN:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(text='<b>Введите сумму в $</b>', reply_markup=kb_back_admin())
    await state.set_state(AddBalanceCasino.amount)

@dp.callback_query(F.data == 'settings_fake')
async def fake_game_adm(callback: CallbackQuery):
    """Настройки фейк ставок"""
    if callback.from_user.id not in ADMIN:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        values_fake = db.get_fake_values()
    except:
        values_fake = 0
        
    await callback.message.edit_text(
        text='<b>👀 Настройки фейк ставок</b>\n\n'
             f'Текущий интервал игр: ⌛️ <code>{TIMER}</code> сек.\n\n'
             f'<i>Включить/выключить фейк ставки:</i>', 
        reply_markup=kb_fake_switch(values_fake)
    )

@dp.callback_query(F.data.startswith('fake'))
async def fake_switch_func(callback: CallbackQuery):
    """Переключение фейк ставок"""
    if callback.from_user.id not in ADMIN:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    values_fake = callback.data.split('|')[1]
    try:
        if int(values_fake):
            db.update_fake(0)
        if int(values_fake) == 0:
            db.update_fake(1)

        values_fake = db.get_fake_values()
    except:
        values_fake = 0
        
    await callback.message.edit_text(
        text='<b>👀 Настройки фейк ставок</b>\n\n'
             f'Текущий интервал игр: ⌛️ <code>{TIMER}</code> сек.\n\n'
             f'<i>Включить/выключить фейк ставки:</i>',
        reply_markup=kb_fake_switch(int(values_fake))
    )
    await callback.answer('✅ Настройки обновлены')

@dp.callback_query(F.data == 'kef_edit')
async def kef_edit_adm(callback: CallbackQuery):
    """Редактирование коэффициентов"""
    if callback.from_user.id not in ADMIN:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        all_kef = db.get_all_KEF()
    except:
        all_kef = {}
        
    text = await kef_all_text(all_kef)
    await callback.message.edit_text(text=text, reply_markup=kb_edit_kef(all_kef))

@dp.callback_query(F.data == 'knb')
async def knb_settings_func(callback: CallbackQuery):
    """Настройки КНБ"""
    if callback.from_user.id not in ADMIN:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        cur_procent = db.get_cur_KEF('KNB')
    except:
        cur_procent = 50
        
    await callback.message.edit_text(
        text='<b>⚙️ Подкрутка КНБ</b>\n\n'
             'Берется рандомное число от 0-100, если рандомное число больше или равно указанному числу то юзер проиграет\n\n'
             '<code>1</code> - всегда проигрыш\n'
             '<code>100</code> - без накрутки\n\n'
             f'<b>Текущее значение:</b> {cur_procent}%', 
        reply_markup=kb_KNB_twist(cur_procent)
    )

@dp.callback_query(F.data == 'all_message_send')
async def all_message_send_func(callback: CallbackQuery):
    """Рассылка сообщений"""
    if callback.from_user.id not in ADMIN:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(text='<b>📢 Выберите тип рассылки</b>', reply_markup=ikb_tip_rassilka())

@dp.callback_query(F.data == 'urls')
async def urls_func(callback: CallbackQuery):
    """Редактирование URL"""
    if callback.from_user.id not in ADMIN:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        url = db.get_URL()
    except:
        url = {}
        
    await callback.message.edit_text(await urls_admin_text(url), reply_markup=kb_urls(), disable_web_page_preview=True)

@dp.callback_query(F.data == 'deleted_checks')
async def deleted_checks_func(callback: CallbackQuery):
    """Удаление чеков"""
    if callback.from_user.id not in ADMIN:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(text='<b>🗑 Удаление чеков</b>\n\nВы уверены что хотите удалить все активные чеки?', reply_markup=kb_answer_delete())

@dp.callback_query(F.data == 'send_db')
async def add_card(callback: CallbackQuery):
    """Отправка базы данных"""
    if callback.from_user.id not in ADMIN:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        document = FSInputFile('database.db')
        await bot.send_document(chat_id=callback.from_user.id, document=document)
        await callback.answer('✅ База данных отправлена')
    except Exception as e:
        await callback.answer(f"❌ Ошибка отправки БД: {e}", show_alert=True)

@dp.callback_query(F.data == 'back_admin')
async def back_admin_func(callback: CallbackQuery, state: FSMContext):
    """Возврат в админ меню"""
    if callback.from_user.id not in ADMIN:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await state.clear()
    try:
        balance_data = await crypto.get_balance()
        balance = balance_data[0].available if balance_data else 0
    except:
        balance = 0
        
    await callback.message.edit_text(
        text='<b>👑 Админ панель</b>\n\n'
             f'💰 <b>Баланс казино:</b> <code>{round(float(balance), 2)}$</code>\n\n'
             f'<i>Выберите действие:</i>',
        reply_markup=kb_admin()
    )

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





