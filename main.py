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
from States import Captcha_users, AddBalanceUser, WithdrawBalance, GameDice, GameSlots, GameFootball, GameKNB

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
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
    except Exception as e:
        logger.error(f"Ошибка получения URL {key}: {e}")
    return "https://t.me/telegram"

# Коэффициенты для игр
def get_game_kefs():
    """Получение коэффициентов из базы данных"""
    try:
        kefs = db.get_all_KEF()
        return {
            'dice': kefs.get('KEF1', 1.7),
            'slots': kefs.get('KEF2', 1.3),
            'football': kefs.get('KEF3', 1.7),
            'knb_win': kefs.get('KEF4', 2.7),
            'knb_lose': kefs.get('KEF5', 1.7)
        }
    except:
        return {
            'dice': 1.7,
            'slots': 1.3, 
            'football': 1.7,
            'knb_win': 2.7,
            'knb_lose': 1.7
        }

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        
        logger.info(f"🔄 Команда /start от пользователя {user_id} (@{username}) - {first_name}")
        
        # Проверяем существование пользователя
        if db.user_exists(user_id):
            logger.info(f"✅ Существующий пользователь {user_id} - показываем меню")
            await message.answer(
                f'👋🏻 С возвращением, {first_name}!',
                reply_markup=kb_menu(user_id)
            )
            await state.clear()
            return
        
        # Новый пользователь - капча
        word = random.choice(list(captcha_dict.keys()))
        start_cmd = message.text
        referi_id = str(start_cmd[7:])
        
        logger.info(f"🆕 Новый пользователь {user_id}, реферал: {referi_id if referi_id else 'нет'}")
        
        if referi_id and referi_id != '' and referi_id != str(user_id):
            db.add_users(user_id, referi_id)
            logger.info(f"📎 Пользователь {user_id} добавлен с рефералом {referi_id}")
        else:
            db.add_users(user_id)
            logger.info(f"👤 Пользователь {user_id} добавлен без реферала")
        
        await message.answer(
            f'👋🏻 Привет {first_name}, чтобы убедиться что вы не робот 🤖 - пройдите капчу\n\n'
            f'Нажми на 👉 <b>{word}</b>', 
            reply_markup=await captcha_keybord(word)
        )
        await state.set_state(Captcha_users.status)
        logger.info(f"🔐 Показана капча для пользователя {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в cmd_start для {message.from_user.id}: {e}")
        await message.answer("❌ Произошла ошибка при запуске бота")

@dp.callback_query(F.data.startswith('Captcha'), Captcha_users.status)
async def chek_captcha(callback: CallbackQuery, state: FSMContext):
    """Проверка капчи"""
    try:
        user_id = callback.from_user.id
        keys = callback.data.split('|')[1]
        word = callback.data.split('|')[2]
        
        logger.info(f"🔍 Проверка капчи пользователем {user_id}: ключ={keys}, слово={word}")
        
        word_new = random.choice(list(captcha_dict.keys()))
        if keys == word:
            logger.info(f"✅ Пользователь {user_id} успешно прошел капчу")
            await callback.message.delete()
            await callback.message.answer(
                f'<b>👋 Добро пожаловать в {NAME_CASINO} 🎲</b>\n\n'
                f'<b>Теперь вы можете:</b>\n'
                f'🎲 <b>Играть</b> - сделать ставку в казино\n'
                f'💸 <b>Пополнить/Вывести баланс</b> - управление средствами\n'
                f'📎 <b>Реферальная программа</b> - приглашать друзей\n'
                f'💭 <b>Информация</b> - правила и инструкции\n'
                f'👤 <b>Профиль</b> - ваша статистика\n\n'
                f'<i>Используйте кнопки меню ниже ↓</i>',
                reply_markup=kb_menu(user_id)
            )
            await state.clear()
        else:
            logger.warning(f"❌ Пользователь {user_id} не прошел капчу")
            await callback.answer('⚠️ Вы не прошли проверку!', show_alert=True)
            await callback.message.edit_text(
                text=f'👋🏻 Привет {callback.from_user.first_name}, чтобы убедиться что вы не робот 🤖 - пройдите капчу\n\n'
                     f'Нажми на 👉 <b>{word_new}</b>', 
                reply_markup=await captcha_keybord(word_new)
            )
    except Exception as e:
        logger.error(f"❌ Ошибка проверки капчи для {callback.from_user.id}: {e}")
        await callback.answer('❌ Ошибка проверки капчи', show_alert=True)
        await state.clear()

# УПРАВЛЕНИЕ БАЛАНСОМ
@dp.message(F.text == '💸 Баланс')
async def balance_menu(message: Message):
    """Меню управления балансом"""
    user_id = message.from_user.id
    balance = db.get_user_balance(user_id)
    
    logger.info(f"💰 Пользователь {user_id} открыл меню баланса: {balance}$")
    
    await message.answer(
        f'<b>💸 Управление балансом</b>\n\n'
        f'💰 <b>Текущий баланс:</b> {balance}$\n\n'
        f'<b>Выберите действие:</b>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="📥 Пополнить", callback_data="add_balance")],
            [InlineKeyboardButton(text="📤 Вывести", callback_data="withdraw_balance")],
            [InlineKeyboardButton(text="📊 Профиль", callback_data="profile_from_balance")],
            [InlineKeyboardButton(text="📋 Меню", callback_data="back_to_menu")]
        ]).adjust(2).as_markup()
    )

# ПОПОЛНЕНИЕ БАЛАНСА
@dp.callback_query(F.data == "add_balance")
async def add_balance_callback(callback: CallbackQuery, state: FSMContext):
    """Пополнение баланса из меню"""
    user_id = callback.from_user.id
    logger.info(f"💰 Пользователь {user_id} начал пополнение баланса")
    
    await callback.message.edit_text(
        '<b>💸 Пополнение баланса</b>\n\n'
        'Введите сумму пополнения в $ (например: 10):',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="❌ Отмена", callback_data="balance_menu")]
        ]).as_markup()
    )
    await state.set_state(AddBalanceUser.amount)

@dp.message(AddBalanceUser.amount)
async def process_add_balance(message: Message, state: FSMContext):
    """Обработка суммы пополнения"""
    user_id = message.from_user.id
    
    if message.text == "❌ Отмена":
        logger.info(f"❌ Пользователь {user_id} отменил пополнение")
        await state.clear()
        await balance_menu(message)
        return
    
    try:
        amount = float(message.text)
        balance = db.get_user_balance(user_id)
        
        logger.info(f"💳 Пользователь {user_id} ввел сумму {amount}$, баланс: {balance}$")
        
        if amount < 1:
            logger.warning(f"⚠️ Пользователь {user_id} ввел слишком маленькую сумму: {amount}$")
            await message.answer("❌ Минимальная сумма пополнения: 1$")
            return
        
        # Создаем инвойс через Crypto Bot
        logger.info(f"🔄 Создание инвойса для пользователя {user_id} на сумму {amount}$")
        invoice = await crypto.create_invoice(
            asset='USDT',
            amount=amount,
            description=f'Пополнение баланса для пользователя {user_id}'
        )
        
        logger.info(f"✅ Инвойс создан: {invoice.invoice_id} для пользователя {user_id}")
        
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
        logger.warning(f"⚠️ Пользователь {user_id} ввел некорректную сумму: {message.text}")
        await message.answer("❌ Введите корректную сумму (например: 10)")
    except Exception as e:
        logger.error(f"❌ Ошибка создания счета для пользователя {user_id}: {e}")
        await message.answer(f"❌ Ошибка создания счета: {e}")

# ВЫВОД СРЕДСТВ
@dp.callback_query(F.data == "withdraw_balance")
async def withdraw_balance_menu(callback: CallbackQuery, state: FSMContext):
    """Меню вывода средств"""
    user_id = callback.from_user.id
    balance = db.get_user_balance(user_id)
    
    logger.info(f"📤 Пользователь {user_id} открыл меню вывода, баланс: {balance}$")
    
    if balance < MIN_WITHDRAWAL:
        await callback.answer(f"❌ Минимальная сумма вывода: {MIN_WITHDRAWAL}$", show_alert=True)
        return
    
    await callback.message.edit_text(
        f'<b>📤 Вывод средств</b>\n\n'
        f'💰 <b>Доступно для вывода:</b> {balance}$\n'
        f'📝 <b>Минимальная сумма:</b> {MIN_WITHDRAWAL}$\n\n'
        f'Введите сумму для вывода в $:',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="❌ Отмена", callback_data="balance_menu")]
        ]).as_markup()
    )
    await state.set_state(WithdrawBalance.amount)

@dp.message(WithdrawBalance.amount)
async def process_withdraw_amount(message: Message, state: FSMContext):
    """Обработка суммы вывода"""
    user_id = message.from_user.id
    current_balance = db.get_user_balance(user_id)
    
    if message.text == "❌ Отмена":
        logger.info(f"❌ Пользователь {user_id} отменил вывод")
        await state.clear()
        await balance_menu(message)
        return
    
    try:
        amount = float(message.text)
        
        logger.info(f"📤 Пользователь {user_id} запросил вывод: {amount}$, баланс: {current_balance}$")
        
        # Проверки
        if amount < MIN_WITHDRAWAL:
            await message.answer(f"❌ Минимальная сумма вывода: {MIN_WITHDRAWAL}$")
            return
            
        if amount > current_balance:
            await message.answer(f"❌ Недостаточно средств. Ваш баланс: {current_balance}$")
            return
        
        # Списываем средства
        db.update_user_balance(user_id, -amount)
        
        # Создаем чек в Crypto Bot
        try:
            logger.info(f"🔄 Создание чека для пользователя {user_id} на сумму {amount}$")
            
            # Получаем информацию о пользователе для комментария
            user_info = f"Вывод средств пользователем {user_id}"
            if message.from_user.username:
                user_info += f" (@{message.from_user.username})"
            
            # Создаем чек
            cheque = await crypto.create_check(
                asset='USDT',
                amount=amount,
                pin_to_user_id=user_id,  # Привязываем чек к пользователю
                description=user_info
            )
            
            logger.info(f"✅ Чек создан: {cheque.check_id} для пользователя {user_id}")
            
            # Отправляем чек пользователю
            await message.answer(
                f'<b>✅ Чек на вывод создан!</b>\n\n'
                f'💰 <b>Сумма:</b> {amount}$\n'
                f'📝 <b>Статус:</b> Ожидает активации\n\n'
                f'<b>Для получения средств:</b>\n'
                f'1. Нажмите на кнопку ниже\n'
                f'2. Перейдите в @CryptoBot\n'
                f'3. Активируйте чек\n\n'
                f'<i>Чек действителен 24 часа</i>',
                reply_markup=InlineKeyboardBuilder([
                    [InlineKeyboardButton(text="💳 Получить средства", url=cheque.bot_check_url)],
                    [InlineKeyboardButton(text="📊 Баланс", callback_data="balance_menu")],
                    [InlineKeyboardButton(text="🎲 Играть", callback_data="back_to_games")]
                ]).adjust(1).as_markup()
            )
            
            # Обновляем статистику выводов
            db.update_user_stats(user_id, 'total_withdraw', amount)
            
        except Exception as e:
            # Если ошибка при создании чека - возвращаем средства
            db.update_user_balance(user_id, amount)
            logger.error(f"❌ Ошибка создания чека для пользователя {user_id}: {e}")
            await message.answer(
                f'❌ Ошибка при создании чека: {e}\n\n'
                f'💰 Средства возвращены на баланс.',
                reply_markup=InlineKeyboardBuilder([
                    [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="withdraw_balance")],
                    [InlineKeyboardButton(text="📊 Баланс", callback_data="balance_menu")]
                ]).adjust(1).as_markup()
            )
        
        await state.clear()
        
    except ValueError:
        logger.warning(f"⚠️ Пользователь {user_id} ввел некорректную сумму: {message.text}")
        await message.answer("❌ Введите корректную сумму (например: 10)")
    except Exception as e:
        logger.error(f"❌ Ошибка вывода для пользователя {user_id}: {e}")
        await message.answer(f"❌ Ошибка при выводе средств: {e}")

@dp.callback_query(F.data == "balance_menu")
async def back_to_balance_menu(callback: CallbackQuery):
    """Возврат в меню баланса"""
    await balance_menu(callback.message)

@dp.callback_query(F.data == "profile_from_balance")
async def profile_from_balance(callback: CallbackQuery):
    """Переход в профиль из меню баланса"""
    await user_profile(callback.message)

# ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
@dp.message(F.text == '👤 Профиль')
async def user_profile(message: Message):
    """Профиль пользователя"""
    user_id = message.from_user.id
    logger.info(f"📊 Пользователь {user_id} запросил профиль")
    
    balance = db.get_user_balance(user_id)
    stats = db.all_stats_users(user_id)
    
    if stats:
        total_games, wins, loses, total_win, total_lose, balance_ref = stats
    else:
        total_games = wins = loses = total_win = total_lose = balance_ref = 0
    
    referrals_count = db.count_ref(user_id)
    referrals_earnings = db.refka_cheks_money(user_id)
    
    win_rate = round((wins/total_games*100), 1) if total_games > 0 else 0
    
    logger.info(f"📈 Статистика пользователя {user_id}: игры={total_games}, победы={wins}, баланс={balance}$")
    
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
            [InlineKeyboardButton(text="💸 Управление балансом", callback_data="balance_menu")],
            [InlineKeyboardButton(text="🎲 Играть", callback_data="back_to_games")]
        ]).adjust(1).as_markup()
    )

# МЕНЮ ИГР
@dp.message(F.text == '🎲 Играть')
async def play_menu(message: Message):
    """Меню игр"""
    user_id = message.from_user.id
    logger.info(f"🎮 Пользователь {user_id} открыл меню игр")
    
    kefs = get_game_kefs()
    
    await message.answer(
        "<b>🎮 Выберите игру:</b>\n\n"
        f"🎲 <b>Кости</b> - коэффициент: x{kefs['dice']}\n"
        f"🎰 <b>Слоты</b> - коэффициент: x{kefs['slots']}\n" 
        f"⚽ <b>Футбол</b> - коэффициент: x{kefs['football']}\n"
        f"✂️ <b>КНБ</b> - коэффициент выигрыша: x{kefs['knb_win']}\n\n"
        f"<i>Выберите игру для начала:</i>",
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="🎲 Кости", callback_data="game_dice")],
            [InlineKeyboardButton(text="🎰 Слоты", callback_data="game_slots")],
            [InlineKeyboardButton(text="⚽ Футбол", callback_data="game_football")],
            [InlineKeyboardButton(text="✂️ КНБ", callback_data="game_knb")],
            [InlineKeyboardButton(text="📋 Меню", callback_data="back_to_menu")]
        ]).adjust(2).as_markup()
    )

# ИГРА В КОСТИ
@dp.callback_query(F.data == "game_dice")
async def game_dice_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик игры в кости"""
    user_id = callback.from_user.id
    kefs = get_game_kefs()
    
    logger.info(f"🎲 Пользователь {user_id} выбрал игру в кости")
    
    await callback.message.edit_text(
        f'<b>🎲 Игра в кости</b>\n\n'
        f'<b>Правила:</b>\n'
        f'• Бросаются две кости\n'
        f'• Сумма от 2 до 6 - проигрыш\n'
        f'• Сумма от 8 до 12 - выигрыш\n'
        f'• Сумма 7 - ничья (ставка возвращается)\n\n'
        f'<b>Коэффициент:</b> x{kefs["dice"]}\n'
        f'<b>Ваш баланс:</b> {db.get_user_balance(user_id)}$\n\n'
        f'Введите сумму ставки в $:',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_games")]
        ]).as_markup()
    )
    await state.set_state(GameDice.amount)

@dp.message(GameDice.amount)
async def process_dice_bet(message: Message, state: FSMContext):
    """Обработка ставки в кости"""
    user_id = message.from_user.id
    balance = db.get_user_balance(user_id)
    
    if message.text == "❌ Отмена":
        logger.info(f"❌ Пользователь {user_id} отменил игру в кости")
        await state.clear()
        await play_menu(message)
        return
    
    try:
        amount = float(message.text)
        
        if amount < 1:
            await message.answer("❌ Минимальная ставка: 1$")
            return
            
        if amount > balance:
            await message.answer(f"❌ Недостаточно средств. Ваш баланс: {balance}$")
            return
        
        # Списываем ставку
        db.update_user_balance(user_id, -amount)
        
        # Играем в кости
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        total = dice1 + dice2
        
        kefs = get_game_kefs()
        kef = kefs['dice']
        
        if total in [8, 9, 10, 11, 12]:  # Выигрыш
            win_amount = round(amount * kef, 2)
            db.update_user_balance(user_id, win_amount)
            db.add_count_pay(user_id, 'win', win_amount)
            db.add_count_pay_stats_day('win', win_amount)
            
            result_text = f"🎉 <b>ПОБЕДА!</b>"
            result_details = f"Вы выиграли: {win_amount}$"
            logger.info(f"✅ Пользователь {user_id} выиграл в кости: {win_amount}$")
            
        elif total in [2, 3, 4, 5, 6]:  # Проигрыш
            db.add_count_pay(user_id, 'lose', amount)
            db.add_count_pay_stats_day('lose', amount)
            
            result_text = f"❌ <b>ПРОИГРЫШ</b>"
            result_details = f"Вы проиграли: {amount}$"
            logger.info(f"❌ Пользователь {user_id} проиграл в кости: {amount}$")
            
        else:  # Ничья (7)
            db.update_user_balance(user_id, amount)
            
            result_text = f"⚖️ <b>НИЧЬЯ</b>"
            result_details = f"Ставка возвращена"
            logger.info(f"⚖️ Пользователь {user_id} ничья в кости")
        
        new_balance = db.get_user_balance(user_id)
        
        await message.answer(
            f'<b>🎲 Результат игры в кости</b>\n\n'
            f'🎯 <b>Бросок:</b> {dice1} + {dice2} = {total}\n'
            f'💰 <b>Ставка:</b> {amount}$\n'
            f'📈 <b>Коэффициент:</b> x{kef}\n\n'
            f'{result_text}\n'
            f'{result_details}\n\n'
            f'💰 <b>Новый баланс:</b> {new_balance}$',
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="🎲 Играть снова", callback_data="game_dice")],
                [InlineKeyboardButton(text="📋 Меню игр", callback_data="back_to_games")],
                [InlineKeyboardButton(text="💸 Баланс", callback_data="balance_menu")]
            ]).adjust(1).as_markup()
        )
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму (например: 10)")
    except Exception as e:
        logger.error(f"❌ Ошибка в игре кости для пользователя {user_id}: {e}")
        await message.answer("❌ Произошла ошибка во время игры")

# ИГРА В СЛОТЫ
@dp.callback_query(F.data == "game_slots")
async def game_slots_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик игры в слоты"""
    user_id = callback.from_user.id
    kefs = get_game_kefs()
    
    logger.info(f"🎰 Пользователь {user_id} выбрал игру в слоты")
    
    await callback.message.edit_text(
        f'<b>🎰 Игра в слоты</b>\n\n'
        f'<b>Правила:</b>\n'
        f'• Три одинаковых символа - выигрыш\n'
        f'• Два одинаковых символа - маленький выигрыш\n'
        f'• Все разные - проигрыш\n\n'
        f'<b>Коэффициент:</b> x{kefs["slots"]}\n'
        f'<b>Ваш баланс:</b> {db.get_user_balance(user_id)}$\n\n'
        f'Введите сумму ставки в $:',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_games")]
        ]).as_markup()
    )
    await state.set_state(GameSlots.amount)

@dp.message(GameSlots.amount)
async def process_slots_bet(message: Message, state: FSMContext):
    """Обработка ставки в слоты"""
    user_id = message.from_user.id
    balance = db.get_user_balance(user_id)
    
    if message.text == "❌ Отмена":
        logger.info(f"❌ Пользователь {user_id} отменил игру в слоты")
        await state.clear()
        await play_menu(message)
        return
    
    try:
        amount = float(message.text)
        
        if amount < 1:
            await message.answer("❌ Минимальная ставка: 1$")
            return
            
        if amount > balance:
            await message.answer(f"❌ Недостаточно средств. Ваш баланс: {balance}$")
            return
        
        # Списываем ставку
        db.update_user_balance(user_id, -amount)
        
        # Играем в слоты
        symbols = ['🍒', '🍋', '🍊', '🍇', '🔔', '💎', '7️⃣']
        result = [random.choice(symbols) for _ in range(3)]
        
        kefs = get_game_kefs()
        kef = kefs['slots']
        
        if result[0] == result[1] == result[2]:  # Три одинаковых
            win_amount = round(amount * kef, 2)
            db.update_user_balance(user_id, win_amount)
            db.add_count_pay(user_id, 'win', win_amount)
            db.add_count_pay_stats_day('win', win_amount)
            
            result_text = f"🎉 <b>ДЖЕКПОТ!</b>"
            result_details = f"Три одинаковых символа!\nВы выиграли: {win_amount}$"
            logger.info(f"🎰 Пользователь {user_id} выиграл джекпот в слотах: {win_amount}$")
            
        elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:  # Два одинаковых
            win_amount = round(amount * (kef / 2), 2)
            db.update_user_balance(user_id, win_amount)
            db.add_count_pay(user_id, 'win', win_amount)
            db.add_count_pay_stats_day('win', win_amount)
            
            result_text = f"✅ <b>ВЫИГРЫШ!</b>"
            result_details = f"Два одинаковых символа!\nВы выиграли: {win_amount}$"
            logger.info(f"✅ Пользователь {user_id} выиграл в слотах: {win_amount}$")
            
        else:  # Проигрыш
            db.add_count_pay(user_id, 'lose', amount)
            db.add_count_pay_stats_day('lose', amount)
            
            result_text = f"❌ <b>ПРОИГРЫШ</b>"
            result_details = f"Вы проиграли: {amount}$"
            logger.info(f"❌ Пользователь {user_id} проиграл в слотах: {amount}$")
        
        new_balance = db.get_user_balance(user_id)
        
        await message.answer(
            f'<b>🎰 Результат игры в слоты</b>\n\n'
            f'🎯 <b>Результат:</b> {" | ".join(result)}\n'
            f'💰 <b>Ставка:</b> {amount}$\n'
            f'📈 <b>Коэффициент:</b> x{kef}\n\n'
            f'{result_text}\n'
            f'{result_details}\n\n'
            f'💰 <b>Новый баланс:</b> {new_balance}$',
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="🎰 Играть снова", callback_data="game_slots")],
                [InlineKeyboardButton(text="📋 Меню игр", callback_data="back_to_games")],
                [InlineKeyboardButton(text="💸 Баланс", callback_data="balance_menu")]
            ]).adjust(1).as_markup()
        )
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму (например: 10)")
    except Exception as e:
        logger.error(f"❌ Ошибка в игре слоты для пользователя {user_id}: {e}")
        await message.answer("❌ Произошла ошибка во время игры")

# ИГРА В ФУТБОЛ
@dp.callback_query(F.data == "game_football")
async def game_football_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик игры в футбол"""
    user_id = callback.from_user.id
    kefs = get_game_kefs()
    
    logger.info(f"⚽ Пользователь {user_id} выбрал игру в футбол")
    
    await callback.message.edit_text(
        f'<b>⚽ Игра в футбол</b>\n\n'
        f'<b>Правила:</b>\n'
        f'• Выбирается случайный счет матча\n'
        f'• Если ваш счет больше - выигрыш\n'
        f'• Если счет противника больше - проигрыш\n'
        f'• Ничья - ставка возвращается\n\n'
        f'<b>Коэффициент:</b> x{kefs["football"]}\n'
        f'<b>Ваш баланс:</b> {db.get_user_balance(user_id)}$\n\n'
        f'Введите сумму ставки в $:',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_games")]
        ]).as_markup()
    )
    await state.set_state(GameFootball.amount)

@dp.message(GameFootball.amount)
async def process_football_bet(message: Message, state: FSMContext):
    """Обработка ставки в футбол"""
    user_id = message.from_user.id
    balance = db.get_user_balance(user_id)
    
    if message.text == "❌ Отмена":
        logger.info(f"❌ Пользователь {user_id} отменил игру в футбол")
        await state.clear()
        await play_menu(message)
        return
    
    try:
        amount = float(message.text)
        
        if amount < 1:
            await message.answer("❌ Минимальная ставка: 1$")
            return
            
        if amount > balance:
            await message.answer(f"❌ Недостаточно средств. Ваш баланс: {balance}$")
            return
        
        # Списываем ставку
        db.update_user_balance(user_id, -amount)
        
        # Играем в футбол
        user_score = random.randint(0, 5)
        opponent_score = random.randint(0, 5)
        
        kefs = get_game_kefs()
        kef = kefs['football']
        
        if user_score > opponent_score:  # Выигрыш
            win_amount = round(amount * kef, 2)
            db.update_user_balance(user_id, win_amount)
            db.add_count_pay(user_id, 'win', win_amount)
            db.add_count_pay_stats_day('win', win_amount)
            
            result_text = f"🎉 <b>ПОБЕДА!</b>"
            result_details = f"Вы выиграли: {win_amount}$"
            logger.info(f"✅ Пользователь {user_id} выиграл в футбол: {win_amount}$")
            
        elif user_score < opponent_score:  # Проигрыш
            db.add_count_pay(user_id, 'lose', amount)
            db.add_count_pay_stats_day('lose', amount)
            
            result_text = f"❌ <b>ПРОИГРЫШ</b>"
            result_details = f"Вы проиграли: {amount}$"
            logger.info(f"❌ Пользователь {user_id} проиграл в футбол: {amount}$")
            
        else:  # Ничья
            db.update_user_balance(user_id, amount)
            
            result_text = f"⚖️ <b>НИЧЬЯ</b>"
            result_details = f"Ставка возвращена"
            logger.info(f"⚖️ Пользователь {user_id} ничья в футбол")
        
        new_balance = db.get_user_balance(user_id)
        
        await message.answer(
            f'<b>⚽ Результат футбольного матча</b>\n\n'
            f'🎯 <b>Счет:</b> Вы {user_score}:{opponent_score} Противник\n'
            f'💰 <b>Ставка:</b> {amount}$\n'
            f'📈 <b>Коэффициент:</b> x{kef}\n\n'
            f'{result_text}\n'
            f'{result_details}\n\n'
            f'💰 <b>Новый баланс:</b> {new_balance}$',
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="⚽ Играть снова", callback_data="game_football")],
                [InlineKeyboardButton(text="📋 Меню игр", callback_data="back_to_games")],
                [InlineKeyboardButton(text="💸 Баланс", callback_data="balance_menu")]
            ]).adjust(1).as_markup()
        )
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму (например: 10)")
    except Exception as e:
        logger.error(f"❌ Ошибка в игре футбол для пользователя {user_id}: {e}")
        await message.answer("❌ Произошла ошибка во время игры")

# ИГРА КАМЕНЬ-НОЖНИЦЫ-БУМАГА
@dp.callback_query(F.data == "game_knb")
async def game_knb_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик игры камень-ножницы-бумага"""
    user_id = callback.from_user.id
    kefs = get_game_kefs()
    
    logger.info(f"✂️ Пользователь {user_id} выбрал игру КНБ")
    
    await callback.message.edit_text(
        f'<b>✂️ Игра Камень-Ножницы-Бумага</b>\n\n'
        f'<b>Правила:</b>\n'
        f'• Камень бьет ножницы\n'
        f'• Ножницы бьют бумагу\n'
        f'• Бумага бьет камень\n\n'
        f'<b>Коэффициент выигрыша:</b> x{kefs["knb_win"]}\n'
        f'<b>Ваш баланс:</b> {db.get_user_balance(user_id)}$\n\n'
        f'Введите сумму ставки в $:',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_games")]
        ]).as_markup()
    )
    await state.set_state(GameKNB.amount)

@dp.message(GameKNB.amount)
async def process_knb_bet(message: Message, state: FSMContext):
    """Обработка ставки в КНБ"""
    user_id = message.from_user.id
    balance = db.get_user_balance(user_id)
    
    if message.text == "❌ Отмена":
        logger.info(f"❌ Пользователь {user_id} отменил игру в КНБ")
        await state.clear()
        await play_menu(message)
        return
    
    try:
        amount = float(message.text)
        
        if amount < 1:
            await message.answer("❌ Минимальная ставка: 1$")
            return
            
        if amount > balance:
            await message.answer(f"❌ Недостаточно средств. Ваш баланс: {balance}$")
            return
        
        # Сохраняем сумму ставки и переходим к выбору хода
        await state.update_data(amount=amount)
        
        await message.answer(
            f'<b>✂️ Выберите ваш ход:</b>\n\n'
            f'💰 <b>Ставка:</b> {amount}$\n\n'
            f'<i>Камень бьет ножницы, ножницы бьют бумагу, бумага бьет камень</i>',
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="🪨 Камень", callback_data="knb_rock")],
                [InlineKeyboardButton(text="✂️ Ножницы", callback_data="knb_scissors")],
                [InlineKeyboardButton(text="📄 Бумага", callback_data="knb_paper")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_games")]
            ]).adjust(3).as_markup()
        )
        await state.set_state(GameKNB.choice)
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму (например: 10)")
    except Exception as e:
        logger.error(f"❌ Ошибка в игре КНБ для пользователя {user_id}: {e}")
        await message.answer("❌ Произошла ошибка во время игры")

@dp.callback_query(GameKNB.choice, F.data.startswith("knb_"))
async def process_knb_choice(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора в КНБ"""
    user_id = callback.from_user.id
    user_choice = callback.data.replace("knb_", "")
    
    # Получаем сохраненную сумму ставки
    data = await state.get_data()
    amount = data.get('amount', 0)
    
    if amount == 0:
        await callback.answer("❌ Ошибка: сумма ставки не найдена", show_alert=True)
        await state.clear()
        return
    
    # Списываем ставку
    db.update_user_balance(user_id, -amount)
    
    # Бот выбирает случайный ход
    choices = ['rock', 'scissors', 'paper']
    bot_choice = random.choice(choices)
    
    # Определяем победителя
    kefs = get_game_kefs()
    
    if user_choice == bot_choice:  # Ничья
        db.update_user_balance(user_id, amount)
        result = "ничья"
        result_text = f"⚖️ <b>НИЧЬЯ!</b>"
        result_details = f"Ставка возвращена"
        logger.info(f"⚖️ Пользователь {user_id} ничья в КНБ")
        
    elif ((user_choice == 'rock' and bot_choice == 'scissors') or
          (user_choice == 'scissors' and bot_choice == 'paper') or
          (user_choice == 'paper' and bot_choice == 'rock')):  # Выигрыш
        win_amount = round(amount * kefs['knb_win'], 2)
        db.update_user_balance(user_id, win_amount)
        db.add_count_pay(user_id, 'win', win_amount)
        db.add_count_pay_stats_day('win', win_amount)
        
        result = "победа"
        result_text = f"🎉 <b>ПОБЕДА!</b>"
        result_details = f"Вы выиграли: {win_amount}$"
        logger.info(f"✅ Пользователь {user_id} выиграл в КНБ: {win_amount}$")
        
    else:  # Проигрыш
        db.add_count_pay(user_id, 'lose', amount)
        db.add_count_pay_stats_day('lose', amount)
        
        result = "проигрыш"
        result_text = f"❌ <b>ПРОИГРЫШ</b>"
        result_details = f"Вы проиграли: {amount}$"
        logger.info(f"❌ Пользователь {user_id} проиграл в КНБ: {amount}$")
    
    # Перевод выбора в эмодзи
    choice_emojis = {
        'rock': '🪨 Камень',
        'scissors': '✂️ Ножницы', 
        'paper': '📄 Бумага'
    }
    
    new_balance = db.get_user_balance(user_id)
    
    await callback.message.edit_text(
        f'<b>✂️ Результат игры КНБ</b>\n\n'
        f'👤 <b>Ваш ход:</b> {choice_emojis[user_choice]}\n'
        f'🤖 <b>Ход бота:</b> {choice_emojis[bot_choice]}\n\n'
        f'💰 <b>Ставка:</b> {amount}$\n'
        f'📈 <b>Коэффициент:</b> x{kefs["knb_win"]}\n\n'
        f'{result_text}\n'
        f'{result_details}\n\n'
        f'💰 <b>Новый баланс:</b> {new_balance}$',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="✂️ Играть снова", callback_data="game_knb")],
            [InlineKeyboardButton(text="📋 Меню игр", callback_data="back_to_games")],
            [InlineKeyboardButton(text="💸 Баланс", callback_data="balance_menu")]
        ]).adjust(1).as_markup()
    )
    await state.clear()

# РЕФЕРАЛЬНАЯ ПРОГРАММА
@dp.message(F.text == '📎 Реферальная программа')
async def referral_menu(message: Message):
    """Реферальная программа"""
    user_id = message.from_user.id
    referrals_count = db.count_ref(user_id)
    referrals_earnings = db.refka_cheks_money(user_id)
    
    logger.info(f"👥 Пользователь {user_id} открыл реферальное меню")
    
    await message.answer(
        f'<b>📎 Реферальная программа</b>\n\n'
        f'👤 <b>Приглашено пользователей:</b> {referrals_count}\n'
        f'💰 <b>Заработано с рефералов:</b> {referrals_earnings}$\n\n'
        f'<b>Ваша реферальная ссылка:</b>\n'
        f'<code>https://t.me/{NICNAME}?start={user_id}</code>\n\n'
        f'<b>Приглашайте друзей и получайте бонусы!</b>',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="👤 Профиль", callback_data="refresh_profile")],
            [InlineKeyboardButton(text="📋 Меню", callback_data="back_to_menu")]
        ]).adjust(1).as_markup()
    )

# ИНФОРМАЦИЯ
@dp.message(F.text == '💭 Информация')
async def info_menu(message: Message):
    """Информационное меню"""
    user_id = message.from_user.id
    logger.info(f"💭 Пользователь {user_id} открыл информационное меню")
    
    await message.answer(
        "<b>💭 Информация</b>\n\n"
        "Здесь вы можете найти полезные ссылки и информацию о боте:",
        reply_markup=kb_info()
    )

# АДМИНКА
@dp.message(F.text == '👑 Админка')
async def admin_menu(message: Message):
    """Админ-меню"""
    user_id = message.from_user.id
    if user_id not in ADMIN:
        logger.warning(f"🚫 Пользователь {user_id} попытался войти в админку")
        await message.answer("❌ Доступ запрещен")
        return
    
    logger.info(f"👑 Админ {user_id} открыл админ-меню")
    await message.answer(
        "<b>👑 Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=kb_admin()
    )

# ВОЗВРАТ В МЕНЮ
@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    user_id = callback.from_user.id
    logger.info(f"🏠 Пользователь {user_id} вернулся в меню")
    await callback.message.answer(
        "📋 <b>Главное меню</b>",
        reply_markup=kb_menu(user_id)
    )

@dp.callback_query(F.data == "back_to_games")
async def back_to_games(callback: CallbackQuery):
    """Возврат к играм"""
    await play_menu(callback.message)

@dp.callback_query(F.data == "refresh_profile")
async def refresh_profile(callback: CallbackQuery):
    """Обновление профиля"""
    await user_profile(callback.message)

# ПРОВЕРКА ПЛАТЕЖЕЙ
@dp.callback_query(F.data.startswith("check_payment_"))
async def check_payment_handler(callback: CallbackQuery):
    """Проверка статуса оплаты"""
    invoice_id = callback.data.replace("check_payment_", "")
    user_id = callback.from_user.id
    
    logger.info(f"🔍 Пользователь {user_id} проверяет оплату инвойса {invoice_id}")
    
    try:
        # Получаем информацию о инвойсе
        invoices = await crypto.get_invoices(invoice_ids=invoice_id)
        if not invoices:
            logger.warning(f"⚠️ Инвойс {invoice_id} не найден для пользователя {user_id}")
            await callback.answer("❌ Счет не найден", show_alert=True)
            return
        
        invoice = invoices[0]
        logger.info(f"📊 Статус инвойса {invoice_id}: {invoice.status}")
        
        if invoice.status == 'paid':
            # Пополняем баланс
            amount = float(invoice.amount)
            old_balance = db.get_user_balance(user_id)
            db.update_user_balance(user_id, amount)
            new_balance = db.get_user_balance(user_id)
            
            logger.info(f"✅ Оплата подтверждена: пользователь {user_id}, сумма {amount}$, баланс {old_balance}$ -> {new_balance}$")
            
            await callback.message.edit_text(
                f'<b>✅ Оплата подтверждена!</b>\n\n'
                f'💰 <b>Сумма:</b> {amount}$\n'
                f'💳 <b>Баланс пополнен</b>\n\n'
                f'💰 <b>Текущий баланс:</b> {new_balance}$',
                reply_markup=InlineKeyboardBuilder([
                    [InlineKeyboardButton(text="🎲 Играть", callback_data="back_to_games")],
                    [InlineKeyboardButton(text="💸 Баланс", callback_data="balance_menu")],
                    [InlineKeyboardButton(text="👤 Профиль", callback_data="refresh_profile")]
                ]).adjust(1).as_markup()
            )
            
        elif invoice.status == 'active':
            logger.info(f"⏳ Инвойс {invoice_id} еще не оплачен")
            await callback.answer("⏳ Оплата еще не поступила", show_alert=True)
        else:
            logger.warning(f"❌ Инвойс {invoice_id} просрочен или отменен")
            await callback.answer("❌ Счет просрочен или отменен", show_alert=True)
            
    except Exception as e:
        logger.error(f"❌ Ошибка проверки оплаты для пользователя {user_id}, инвойс {invoice_id}: {e}")
        await callback.answer(f"❌ Ошибка проверки: {e}", show_alert=True)

@dp.callback_query(F.data == "cancel_payment")
async def cancel_payment_handler(callback: CallbackQuery):
    """Отмена платежа"""
    user_id = callback.from_user.id
    logger.info(f"❌ Пользователь {user_id} отменил платеж")
    
    await callback.message.edit_text(
        "❌ Пополнение баланса отменено",
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text="💸 Баланс", callback_data="balance_menu")],
            [InlineKeyboardButton(text="📋 Меню", callback_data="back_to_menu")]
        ]).adjust(1).as_markup()
    )

async def main():
    """Основная функция запуска бота"""
    try:
        logger.info("🤖 Бот запускается...")
        print("✅ Бот успешно запущен!")
        
        # Проверяем подключение к базе данных
        try:
            test_user = db.user_exists(1)  # Тестовый запрос
            logger.info("✅ Подключение к базе данных успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к базе данных: {e}")
        
        # Проверяем Crypto Bot
        try:
            await crypto.get_me()
            logger.info("✅ Подключение к Crypto Bot успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Crypto Bot: {e}")
        
        logger.info("🚀 Запуск опроса...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске бота: {e}")
        print(f"❌ Ошибка: {e}")
    finally:
        logger.info("🛑 Бот остановлен")
        await bot.session.close()

if __name__ == "__main__":
    logger.info("🔧 Запуск приложения...")
    asyncio.run(main())
