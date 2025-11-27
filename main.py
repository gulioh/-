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

# ОБРАБОТЧИК КНОПКИ "🎲 Играть" - ДОБАВЬТЕ ЭТОТ КОД
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

# ОБРАБОТЧИКИ ДЛЯ КНОПОК ИГР (упрощенные версии)
@dp.callback_query(F.data == "game_dice")
async def game_dice_menu(callback: CallbackQuery):
    """Меню игры в кости"""
    balance = db.get_user_balance(callback.from_user.id)
    
    await callback.message.edit_text(
        f'<b>🎯 Игра в кости</b>\n\n'
        f'💰 <b>Баланс:</b> {balance}$\n\n'
        f'<b>Правила:</b>\n'
        f'• Бросьте кубик и попробуйте угадать результат\n'
        f'• Коэффициент выигрыша: x2\n\n'
        f'<b>Нажмите кнопку ниже чтобы бросить кубик:</b>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="🎲 Бросить кубик", callback_data="roll_dice")],
            [InlineKeyboardButton(text="❌ Назад", callback_data="back_to_games")]
        ]).as_markup()
    )

@dp.callback_query(F.data == "roll_dice")
async def roll_dice_handler(callback: CallbackQuery):
    """Бросок кубика"""
    user_id = callback.from_user.id
    bet_amount = 1.0  # Фиксированная ставка для примера
    
    # Проверяем баланс
    balance = db.get_user_balance(user_id)
    if balance < bet_amount:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    # Списываем ставку
    db.update_user_balance(user_id, -bet_amount)
    
    # Бросаем кубик
    dice_message = await callback.message.answer_dice(emoji="🎲")
    dice_value = dice_message.dice.value
    
    await asyncio.sleep(3)  # Ждем завершения анимации
    
    # Определяем результат (простой вариант - четное/нечетное)
    win = (dice_value % 2 == 0)  # Четное число - победа
    multiplier = 2
    win_amount = bet_amount * multiplier if win else 0
    
    if win:
        db.update_user_balance(user_id, win_amount)
        result_text = f"🎉 <b>ПОБЕДА!</b>\nВы выиграли: {win_amount}$"
        db.update_user_stats(user_id, 'wins', 1)
    else:
        result_text = f"😞 <b>ПРОИГРЫШ</b>\nВы проиграли: {bet_amount}$"
        db.update_user_stats(user_id, 'loses', 1)
    
    db.update_user_stats(user_id, 'total_games', 1)
    
    new_balance = db.get_user_balance(user_id)
    
    await callback.message.answer(
        f'<b>🎯 Результат игры в кости</b>\n\n'
        f'🎲 <b>Выпало:</b> {dice_value}\n'
        f'💰 <b>Сумма ставки:</b> {bet_amount}$\n'
        f'📈 <b>Коэффициент:</b> x{multiplier}\n\n'
        f'{result_text}\n\n'
        f'💰 <b>Новый баланс:</b> {new_balance}$',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="🎯 Сыграть еще", callback_data="game_dice")],
            [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
        ]).as_markup()
    )

@dp.callback_query(F.data == "game_slots")
async def game_slots_menu(callback: CallbackQuery):
    """Меню игры в слоты"""
    balance = db.get_user_balance(callback.from_user.id)
    
    await callback.message.edit_text(
        f'<b>🎰 Игровые автоматы</b>\n\n'
        f'💰 <b>Баланс:</b> {balance}$\n\n'
        f'<b>Правила:</b>\n'
        f'• Крутите слоты и выигрывайте призы\n'
        f'• Выигрышные комбинации: 7️⃣7️⃣7️⃣, 🍒🍒🍒, 🍋🍋🍋\n\n'
        f'<b>Нажмите кнопку ниже чтобы крутить слоты:</b>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="🎰 Крутить слоты", callback_data="spin_slots")],
            [InlineKeyboardButton(text="❌ Назад", callback_data="back_to_games")]
        ]).as_markup()
    )

@dp.callback_query(F.data == "spin_slots")
async def spin_slots_handler(callback: CallbackQuery):
    """Кручение слотов"""
    user_id = callback.from_user.id
    bet_amount = 1.0  # Фиксированная ставка для примера
    
    # Проверяем баланс
    balance = db.get_user_balance(user_id)
    if balance < bet_amount:
        await callback.answer("❌ Недостаточно средств!", show_alert=True)
        return
    
    # Списываем ставку
    db.update_user_balance(user_id, -bet_amount)
    
    # Крутим слоты
    slots_message = await callback.message.answer_dice(emoji="🎰")
    slots_value = slots_message.dice.value
    
    await asyncio.sleep(3)  # Ждем завершения анимации
    
    # Определяем результат (упрощенная логика)
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
    
    win_amount = bet_amount * multiplier if win else 0
    
    if win:
        db.update_user_balance(user_id, win_amount)
        result_text = f"🎉 <b>ДЖЕКПОТ!</b>\nВы выиграли: {win_amount}$"
        db.update_user_stats(user_id, 'wins', 1)
    else:
        result_text = f"😞 <b>ПРОИГРЫШ</b>\nВы проиграли: {bet_amount}$"
        db.update_user_stats(user_id, 'loses', 1)
    
    db.update_user_stats(user_id, 'total_games', 1)
    
    new_balance = db.get_user_balance(user_id)
    
    await callback.message.answer(
        f'<b>🎰 Результат игры в слоты</b>\n\n'
        f'🎰 <b>Результат:</b> {get_slots_name(slots_value)}\n'
        f'💰 <b>Сумма ставки:</b> {bet_amount}$\n'
        f'📈 <b>Коэффициент:</b> x{multiplier}\n\n'
        f'{result_text}\n\n'
        f'💰 <b>Новый баланс:</b> {new_balance}$',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="🎰 Сыграть еще", callback_data="game_slots")],
            [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
        ]).as_markup()
    )

@dp.callback_query(F.data == "back_to_games")
async def back_to_games(callback: CallbackQuery):
    """Возврат в меню игр"""
    await play_game_menu(callback.message)

# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
def get_slots_name(value):
    """Получение названия комбинации слотов"""
    if value == 64: return "7️⃣7️⃣7️⃣"
    elif value == 1: return "🍒🍒🍒" 
    elif value == 22: return "🍋🍋🍋"
    elif value == 43: return "💰💰💰"
    else: return "Проигрыш"

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
