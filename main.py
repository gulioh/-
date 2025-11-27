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

@dp.message(F.text == '🎲 Играть')
async def play_game_handler(message: Message):
    channals_url = safe_get_url('channals')
    command_url = safe_get_url('command_game')
    
@dp.message(F.text == '🎲 Играть')
async def play_game_menu(message: Message):
    """Меню игр"""
    await message.answer(
        '<b>🎲 Выберите игру</b>\n\n'
        'Доступные игры:\n'
        '🎯 <b>Кости</b> - классическая игра в кости\n'
        '🎰 <b>Слоты</b> - игровые автоматы\n'
        '⚽️ <b>Футбол</b> - ставки на гол/мимо\n'
        '🪨✂️📄 <b>КНБ</b> - камень-ножницы-бумага\n\n'
        'Выберите игру:',
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

@dp.message(GameDice.amount)
async def process_dice_amount(message: Message, state: FSMContext):
    """Обработка суммы ставки в кости"""
    try:
        amount = float(message.text)
        # Здесь проверка баланса пользователя
        # Если баланс >= amount, продолжаем
        
        await message.answer(
            f'<b>🎯 Ставка в кости</b>\n\n'
            f'Сумма: {amount}$\n'
            f'Выберите тип ставки:',
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣", callback_data=f"dice_number_{amount}")],
                [InlineKeyboardButton(text="📈 Больше (4-6)", callback_data=f"dice_more_{amount}")],
                [InlineKeyboardButton(text="📉 Меньше (1-3)", callback_data=f"dice_less_{amount}")],
                [InlineKeyboardButton(text="2️⃣4️⃣6️⃣ Четное", callback_data=f"dice_even_{amount}")],
                [InlineKeyboardButton(text="1️⃣3️⃣5️⃣ Нечетное", callback_data=f"dice_odd_{amount}")]
            ]).as_markup()
        )
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму")

@dp.callback_query(F.data.startswith("dice_number_"))
async def dice_number_bet(callback: CallbackQuery):
    """Ставка на конкретное число в костях"""
    amount = float(callback.data.split("_")[2])
    
    await callback.message.edit_text(
        f'<b>🎯 Ставка на число</b>\n\n'
        f'Сумма: {amount}$\n'
        f'Выберите число (1-6):',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="1️⃣", callback_data=f"dice_bet_1_{amount}"),
             InlineKeyboardButton(text="2️⃣", callback_data=f"dice_bet_2_{amount}"),
             InlineKeyboardButton(text="3️⃣", callback_data=f"dice_bet_3_{amount}")],
            [InlineKeyboardButton(text="4️⃣", callback_data=f"dice_bet_4_{amount}"),
             InlineKeyboardButton(text="5️⃣", callback_data=f"dice_bet_5_{amount}"),
             InlineKeyboardButton(text="6️⃣", callback_data=f"dice_bet_6_{amount}")],
            [InlineKeyboardButton(text="❌ Назад", callback_data=f"game_dice")]
        ]).as_markup()
    )

@dp.callback_query(F.data.startswith("dice_bet_"))
async def process_dice_bet(callback: CallbackQuery):
    """Обработка ставки в кости"""
    data = callback.data.split("_")
    bet_type = data[2]  # число или more/less/even/odd
    amount = float(data[3])
    
    # Отправляем анимацию кубика
    dice_message = await callback.message.answer_dice(emoji="🎲")
    dice_value = dice_message.dice.value
    
    # Определяем результат
    win = False
    multiplier = 1
    
    if bet_type.isdigit():  # Ставка на число
        chosen_number = int(bet_type)
        if dice_value == chosen_number:
            win = True
            multiplier = 6
    elif bet_type == "more":  # Ставка на больше
        if dice_value >= 4:
            win = True
            multiplier = 2
    elif bet_type == "less":  # Ставка на меньше
        if dice_value <= 3:
            win = True
            multiplier = 2
    elif bet_type == "even":  # Ставка на четное
        if dice_value % 2 == 0:
            win = True
            multiplier = 2
    elif bet_type == "odd":  # Ставка на нечетное
        if dice_value % 2 == 1:
            win = True
            multiplier = 2
    
    # Расчет выигрыша
    if win:
        win_amount = amount * multiplier
        result_text = f"🎉 <b>ПОБЕДА!</b>\nВы выиграли: {win_amount}$"
        # Здесь добавляем выигрыш к балансу пользователя
    else:
        result_text = f"😞 <b>ПРОИГРЫШ</b>\nВы проиграли: {amount}$"
        # Здесь вычитаем ставку из баланса
    
    await asyncio.sleep(3)  # Ждем пока анимация кубика завершится
    
    await callback.message.answer(
        f'<b>🎯 Результат игры</b>\n\n'
        f'Выпало: {dice_value}\n'
        f'Ставка: {amount}$\n'
        f'Коэффициент: x{multiplier}\n\n'
        f'{result_text}\n\n'
        f'<i>Сыграть еще раз?</i>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="🎯 Сыграть еще", callback_data="game_dice")],
            [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
        ]).as_markup()
    )

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
# АДМИНСКИЕ ФУНКЦИИ (оставьте ваши существующие админские функции ниже)

@admin.message(F.text == '👑 Админка')
async def stats_adm(message: Message):
    try:
        balance_data = await crypto.get_balance()
        balance = balance_data[0].available if balance_data else 0
    except:
        balance = 0
        
    await message.answer(text='<b>Вы в админ меню\n'
                              f'Баланс казино: <code>{round(float(balance), 2)}$</code></b>',
                         reply_markup=kb_admin())

# ... остальные ваши админские функции оставьте без изменений

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


