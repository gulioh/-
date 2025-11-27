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
    
    await message.answer(
        '<b>🎲 Начать игру</b>\n\n'
        'Чтобы начать игру:\n'
        '1. Перейдите в игровой канал по кнопке ниже\n'
        '2. Пополните баланс если нужно\n'
        '3. Сделайте ставку по инструкции\n'
        '4. Следите за результатом в канале\n\n'
        'Используйте команды из раздела "Ключевые слова"',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text='🎯 Игровой канал', url=channals_url)],
            [InlineKeyboardButton(text='📋 Ключевые слова', url=command_url)]
        ]).as_markup(),
        disable_web_page_preview=True
    )

@dp.message(F.text == '💸 Пополнить баланс')
async def add_balance_handler(message: Message):
    checks_url = safe_get_url('checks')
    await message.answer(
        '<b>💸 Пополнение баланса</b>\n\n'
        'Для пополнения баланса перейдите в канал с чеками:',
        reply_markup=InlineKeyboardBuilder([
            [InlineKeyboardButton(text='💳 Перейти к чекам', url=checks_url)]
        ]).as_markup(),
        disable_web_page_preview=True
    )

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
