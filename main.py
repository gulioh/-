import datetime
import asyncio
import random
import logging

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram import F
from aiogram.filters import CommandStart, CommandObject
from aiogram.utils.markdown import hlink
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

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

# Вспомогательные функции для игр
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

# Middleware для админа
admin.message.filter(IsAdmin())

@dp.message(CommandStart())
async def cmd_start(message:Message, state:FSMContext):
    try:
        db.db_start()
        db.db_settings()
        db.db_stats()
        db.db_urls()
    except Exception as e:
        print(f"Ошибка инициализации БД: {e}")

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
    try:
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
    except Exception as e:
        print(f"Ошибка в капче: {e}")
        await callback.answer('⚠️ Ошибка проверки!', show_alert=True)

@dp.message(F.text == '📎 Реферальная программа')
async def stats_adm(message: Message):
    try:
        ref_count = db.count_ref(message.from_user.id)
        ref_money = db.refka_cheks_money(message.from_user.id)
        await message.answer(f'<b>📎 Ваша реферальная ссылка:\n'
                             f'https://t.me/{NICNAME}?start={message.from_user.id}\n\n'
                             f'👥 Количество рефералов: <code>{ref_count}</code>\n'
                             f'💵 Заработано с рефералов: <code>{ref_money}$</code>\n\n'
                             f'❓ Как работает реферальная программа:\n'
                             f'Вы будете получать {lose_withdraw}% с каждого проигрыша своего реферала.\n'
                             f'Начисление происходит автоматически на ваш кошелек CryptoBot\n\n'
                             f'⚠️ Минимальная ставка реферала должна составлять: {min_stavka_referal}$</b>',
                             reply_markup=kb_url_Channel())
    except Exception as e:
        print(f"Ошибка в реферальной программе: {e}")
        await message.answer("❌ Ошибка загрузки реферальной информации")

@dp.message(F.text == '💭 Информация')
async def info_func(message:Message):
    game_channel = safe_get_url('channals')
    await message.answer(f'<b>💭 Информация о проекте {hlink(title=NAME_CASINO, url=game_channel)}</b>', 
                         reply_markup=kb_info(), disable_web_page_preview=True)

# ФУНКЦИИ ПРОФИЛЯ
@dp.message(F.text == '👤 Профиль')
async def profile_handler(message: Message):
    """Показ профиля пользователя"""
    try:
        user_id = message.from_user.id
        balance = db.get_user_balance(user_id)
        ref_count = db.count_ref(user_id)
        
        # Получаем информацию о пользователе
        username = f"@{message.from_user.username}" if message.from_user.username else "Не указан"
        first_name = message.from_user.first_name or "Пользователь"
        
        # Получаем статистику игр
        try:
            user_stats = db.all_stats_users(user_id) or [0, 0, 0, 0, 0, 0]
            total_games = user_stats[0]
            wins = user_stats[1]
            loses = user_stats[2]
        except:
            total_games = 0
            wins = 0
            loses = 0
        
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
            f'   • 🎮 Всего игр: <code>{total_games}</code>\n'
            f'   • ✅ Побед: <code>{wins}</code>\n'
            f'   • ❌ Поражений: <code>{loses}</code>\n'
            f'   • 📈 Процент побед: <code>{win_rate:.1f}%</code>\n\n'
            f'👥 <b>Реферальная программа:</b>\n'
            f'   • 👤 Рефералов: <code>{ref_count}</code>\n'
            f'   • 💰 Заработано: <code>{db.refka_cheks_money(user_id)}$</code>\n\n'
            f'🔗 <b>Ваша реферальная ссылка:</b>\n'
            f'<code>{ref_link}</code>',
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="📎 Поделиться ссылкой", url=f"https://t.me/share/url?url={ref_link}&text=Присоединяйся%20к%20казино!")],
                [InlineKeyboardButton(text="💸 Пополнить баланс", callback_data="add_balance_from_profile")],
                [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_profile")]
            ]).as_markup(),
            disable_web_page_preview=True
        )
    except Exception as e:
        print(f"Ошибка в профиле: {e}")
        await message.answer("❌ Ошибка загрузки профиля")

@dp.callback_query(F.data == "refresh_profile")
async def refresh_profile(callback: CallbackQuery):
    """Обновление профиля"""
    await profile_handler(callback.message)

@dp.callback_query(F.data == "add_balance_from_profile")
async def add_balance_from_profile(callback: CallbackQuery, state: FSMContext):
    """Пополнение баланса из профиля"""
    await callback.message.answer(
        '<b>💸 Пополнение баланса</b>\n\n'
        'Введите сумму пополнения в $ (например: 10):',
        reply_markup=ReplyKeyboardBuilder([
            [KeyboardButton(text="❌ Отмена")]
        ]).as_markup(resize_keyboard=True)
    )
    await state.set_state(AddBalanceUser.amount)
    await callback.answer()

# ИГРОВЫЕ ФУНКЦИИ
@dp.message(F.text == '🎲 Играть')
async def play_game_menu(message: Message):
    """Меню выбора игры"""
    try:
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
                [InlineKeyboardButton(text="🪨✂️📄 КНБ", callback_data="game_knb")],
                [InlineKeyboardButton(text="👤 Профиль", callback_data="refresh_profile")]
            ]).as_markup()
        )
    except Exception as e:
        print(f"Ошибка в меню игр: {e}")
        await message.answer("❌ Ошибка загрузки меню игр")

@dp.callback_query(F.data == "game_dice")
async def game_dice_menu(callback: CallbackQuery, state: FSMContext):
    """Меню игры в кости"""
    try:
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
    except Exception as e:
        print(f"Ошибка в меню костей: {e}")
        await callback.answer("❌ Ошибка загрузки игры")

@dp.message(GameDice.amount)
async def process_dice_amount(message: Message, state: FSMContext):
    """Обработка суммы ставки в кости"""
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
    except Exception as e:
        print(f"Ошибка обработки ставки: {e}")
        await message.answer("❌ Ошибка обработки ставки")

@dp.callback_query(F.data == "dice_number")
async def dice_number_bet(callback: CallbackQuery, state: FSMContext):
    """Ставка на конкретное число в костях"""
    try:
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
    except Exception as e:
        print(f"Ошибка выбора числа: {e}")
        await callback.answer("❌ Ошибка выбора числа")

@dp.callback_query(F.data.startswith("dice_bet_"))
async def process_dice_bet(callback: CallbackQuery, state: FSMContext):
    """Обработка ставки в кости"""
    try:
        data = await state.get_data()
        amount = data['amount']
        bet_type = callback.data.split("_")[2]  # число от 1 до 6
        
        # Списываем ставку с баланса
        db.update_user_balance(callback.from_user.id, -amount)
        
        # Обновляем статистику - увеличиваем общее количество игр
        try:
            db.update_user_stats(callback.from_user.id, 'total_games', 1)
        except:
            pass
        
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
            # Обновляем статистику - увеличиваем победы
            try:
                db.update_user_stats(callback.from_user.id, 'wins', 1)
                db.update_user_stats(callback.from_user.id, 'total_win', win_amount)
            except:
                pass
            result_text = f"🎉 <b>ПОБЕДА!</b>\nВы выиграли: {win_amount}$"
        else:
            # Обновляем статистику - увеличиваем поражения
            try:
                db.update_user_stats(callback.from_user.id, 'loses', 1)
            except:
                pass
            result_text = f"😞 <b>ПРОИГРЫШ</b>\nВы проиграли: {amount}$"
        
        # Обновляем общую сумму ставок
        try:
            db.update_user_stats(callback.from_user.id, 'total_bet', amount)
        except:
            pass
        
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
                [InlineKeyboardButton(text="👤 Профиль", callback_data="refresh_profile")],
                [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
            ]).as_markup()
        )
        await state.clear()
    except Exception as e:
        print(f"Ошибка в игре в кости: {e}")
        await callback.answer("❌ Ошибка в игре")
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

# ИГРА В СЛОТЫ
@dp.callback_query(F.data == "game_slots")
async def game_slots_menu(callback: CallbackQuery, state: FSMContext):
    """Меню игры в слоты"""
    try:
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
    except Exception as e:
        print(f"Ошибка в меню слотов: {e}")
        await callback.answer("❌ Ошибка загрузки игры")

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
        
        # Обновляем статистику
        try:
            db.update_user_stats(message.from_user.id, 'total_games', 1)
            db.update_user_stats(message.from_user.id, 'total_bet', amount)
        except:
            pass
        
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
            try:
                db.update_user_stats(message.from_user.id, 'wins', 1)
                db.update_user_stats(message.from_user.id, 'total_win', win_amount)
            except:
                pass
            result_text = f"🎉 <b>ДЖЕКПОТ!</b>\nВы выиграли: {win_amount}$"
        else:
            try:
                db.update_user_stats(message.from_user.id, 'loses', 1)
            except:
                pass
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
                [InlineKeyboardButton(text="👤 Профиль", callback_data="refresh_profile")],
                [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
            ]).as_markup()
        )
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму (например: 10)")
    except Exception as e:
        print(f"Ошибка в игре в слоты: {e}")
        await message.answer("❌ Ошибка в игре")
        await state.clear()

# ИГРА В ФУТБОЛ
@dp.callback_query(F.data == "game_football")
async def game_football_menu(callback: CallbackQuery, state: FSMContext):
    """Меню игры в футбол"""
    try:
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
    except Exception as e:
        print(f"Ошибка в меню футбола: {e}")
        await callback.answer("❌ Ошибка загрузки игры")

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
    except Exception as e:
        print(f"Ошибка обработки ставки в футбол: {e}")
        await message.answer("❌ Ошибка обработки ставки")

@dp.callback_query(F.data.startswith("football_"))
async def process_football_bet(callback: CallbackQuery, state: FSMContext):
    """Обработка ставки в футбол"""
    try:
        data = await state.get_data()
        amount = data['amount']
        bet_type = callback.data.split("_")[1]  # goal или miss
        
        # Списываем ставку
        db.update_user_balance(callback.from_user.id, -amount)
        
        # Обновляем статистику
        try:
            db.update_user_stats(callback.from_user.id, 'total_games', 1)
            db.update_user_stats(callback.from_user.id, 'total_bet', amount)
        except:
            pass
        
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
            try:
                db.update_user_stats(callback.from_user.id, 'wins', 1)
                db.update_user_stats(callback.from_user.id, 'total_win', win_amount)
            except:
                pass
            result_text = f"🎉 <b>ГОООЛ!</b>\nВы выиграли: {win_amount}$"
        else:
            try:
                db.update_user_stats(callback.from_user.id, 'loses', 1)
            except:
                pass
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
                [InlineKeyboardButton(text="👤 Профиль", callback_data="refresh_profile")],
                [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
            ]).as_markup()
        )
        await state.clear()
    except Exception as e:
        print(f"Ошибка в игре в футбол: {e}")
        await callback.answer("❌ Ошибка в игре")
        await state.clear()

# ИГРА КАМЕНЬ-НОЖНИЦЫ-БУМАГА
@dp.callback_query(F.data == "game_knb")
async def game_knb_menu(callback: CallbackQuery, state: FSMContext):
    """Меню игры в камень-ножницы-бумага"""
    try:
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
    except
