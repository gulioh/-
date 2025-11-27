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

# ФУНКЦИИ ПРОФИЛЯ
@dp.message(F.text == '👤 Профиль')
async def profile_handler(message: Message):
    """Показ профиля пользователя"""
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

# АДМИН ПАНЕЛЬ
@dp.message(F.text == '👑 Админка')
async def admin_panel(message: Message):
    """Админка из сообщения"""
    if message.from_user.id not in ADMIN:
        await message.answer("❌ У вас нет доступа к админ панели")
        return
    
    try:
        # Получаем баланс казино
        casino_balance = db.get_casino_balance()
    except:
        casino_balance = 0
        
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
    try:
        casino_balance = db.get_casino_balance()
    except:
        casino_balance = 0
        
    await callback.message.edit_text(
        text='<b>👑 Админ панель</b>\n\n'
             f'💰 <b>Баланс казино:</b> <code>{casino_balance}$</code>\n\n'
             f'<i>Выберите действие:</i>',
        reply_markup=kb_admin()
    )

@dp.callback_query(F.data == 'stats_project')
async def stats_adm(callback: CallbackQuery):
    """Статистика проекта"""
    if callback.from_user.id not in ADMIN:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        stats = db.all_stats() or [0, 0, 0, 0, 0, 0]
        casino_balance = db.get_casino_balance()
        info_day = db.all_stats_day() or [0, 0, 0, 0, 0]
        all_users = db.all_user()
    except:
        stats = [0, 0, 0, 0, 0, 0]
        casino_balance = 0
        info_day = [0, 0, 0, 0, 0]
        all_users = []
        
    await callback.message.edit_text(
        text=f'<b>📊 Статистика проекта</b>\n\n'
             f'👥 <b>Всего пользователей:</b> <code>{len(all_users)}</code>\n'
             f'🎮 <b>Всего игр:</b> <code>{stats[1]}</code>\n'
             f'✅ <b>Побед:</b> <code>{stats[2]}</code>\n'
             f'❌ <b>Поражений:</b> <code>{stats[3]}</code>\n'
             f'💸 <b>Выплаты:</b> <code>{stats[4]}$</code>\n'
             f'💰 <b>Доход:</b> <code>{stats[5]}$</code>\n\n'
             f'<b>📈 За сегодня:</b>\n'
             f'🎮 <b>Игры:</b> <code>{info_day[0]}</code>\n'
             f'✅ <b>Побед:</b> <code>{info_day[1]}</code>\n'
             f'❌ <b>Поражений:</b> <code>{info_day[2]}</code>\n'
             f'💸 <b>Выплаты:</b> <code>{info_day[3]}$</code>\n'
             f'💰 <b>Доход:</b> <code>{info_day[4]}$</code>\n\n'
             f'💳 <b>Баланс казино:</b> <code>{casino_balance}$</code>',
        reply_markup=kb_back_admin()
    )

@dp.callback_query(F.data == 'fake_deposit')
async def fake_deposit_menu(callback: CallbackQuery, state: FSMContext):
    """Меню фейкового пополнения"""
    if callback.from_user.id not in ADMIN:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        text='<b>💰 Фейк пополнение баланса</b>\n\n'
             'Введите ID пользователя:',
        reply_markup=kb_back_admin()
    )
    await state.set_state(FakeDeposit.user_id)

@dp.message(FakeDeposit.user_id)
async def process_fake_deposit_user_id(message: Message, state: FSMContext):
    """Обработка ID пользователя для фейк пополнения"""
    try:
        user_id = int(message.text)
        await state.update_data(user_id=user_id)
        
        await message.answer(
            '<b>💰 Фейк пополнение баланса</b>\n\n'
            f'Пользователь: <code>{user_id}</code>\n'
            'Введите сумму пополнения ($):',
            reply_markup=kb_back_admin()
        )
        await state.set_state(FakeDeposit.amount)
        
    except ValueError:
        await message.answer('❌ Введите корректный ID пользователя (число)')

@dp.message(FakeDeposit.amount)
async def process_fake_deposit_amount(message: Message, state: FSMContext):
    """Обработка суммы фейк пополнения"""
    try:
        amount = float(message.text)
        data = await state.get_data()
        user_id = data['user_id']
        
        if amount <= 0:
            await message.answer('❌ Сумма должна быть больше 0')
            return
        
        # Пополняем баланс
        db.update_user_balance(user_id, amount)
        
        # Добавляем запись в транзакции
        db.add_transaction(
            user_id=user_id,
            transaction_type='fake_deposit',
            amount=amount,
            status='completed',
            description=f'Фейк пополнение от админа {message.from_user.id}'
        )
        
        await message.answer(
            f'✅ <b>Баланс пользователя {user_id} пополнен на {amount}$</b>\n\n'
            f'💳 <b>Сумма:</b> {amount}$\n'
            f'👤 <b>Пользователь:</b> <code>{user_id}</code>\n'
            f'🆔 <b>Админ:</b> <code>{message.from_user.id}</code>',
            reply_markup=kb_back_admin()
        )
        
        # Пытаемся уведомить пользователя
        try:
            await bot.send_message(
                user_id,
                f'🎉 <b>Ваш баланс пополнен на {amount}$</b>\n\n'
                f'💰 <b>Сумма:</b> {amount}$\n'
                f'📝 <b>Тип:</b> Административное пополнение\n\n'
                f'💳 <b>Текущий баланс:</b> {db.get_user_balance(user_id)}$'
            )
        except:
            pass
            
        await state.clear()
        
    except ValueError:
        await message.answer('❌ Введите корректную сумму')

# Другие админ функции
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
