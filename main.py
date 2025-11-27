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
from config import *
from States import *

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

# ПОПОЛНЕНИЕ БАЛАНСА (ваш код)
@dp.message(F.text == '💸 Пополнить баланс')
async def add_balance_user(message: Message, state: FSMContext):
    """Пополнение баланса через Crypto Bot"""
    if not crypto:
        await message.answer(
            "❌ Сервис пополнения временно недоступен\n\n"
            "💳 Для пополнения баланса обратитесь к администратору",
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="📞 Связаться с админом", url="https://t.me/your_admin")]
            ]).as_markup()
        )
        return
    
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
    if not crypto:
        await callback.answer("❌ Сервис платежей недоступен", show_alert=True)
        return
        
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

# КОСТИ
@dp.callback_query(F.data == "game_dice")
async def game_dice_menu(callback: CallbackQuery, state: FSMContext):
    """Меню игры в кости"""
    balance = db.get_user_balance(callback.from_user.id)
    
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

# СЛОТЫ
@dp.callback_query(F.data == "game_slots")
async def game_slots_menu(callback: CallbackQuery, state: FSMContext):
    """Меню игры в слоты"""
    balance = db.get_user_balance(callback.from_user.id)
    
    await callback.message.edit_text(
        f'<b>🎰 Игровые автоматы</b>\n\n'
        f'💰 <b>Баланс:</b> {balance}$\n\n'
        f'<b>Введите сумму ставки:</b>\n'
        f'<i>Минимальная ставка: 1$</i>',
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
        
        await asyncio.sleep(3)
        
        # Простая логика
        win = (slots_value in [1, 22, 43, 64])  # Выигрышные комбинации
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
            f'<b>🎰 Результат игры в слоты</b>\n\n'
            f'🎰 <b>Результат:</b> {get_slots_name(slots_value)}\n'
            f'💰 <b>Сумма ставки:</b> {amount}$\n'
            f'📈 <b>Коэффициент:</b> x{multiplier}\n\n'
            f'{result_text}\n\n'
            f'💰 <b>Новый баланс:</b> {new_balance}$',
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="🎰 Сыграть еще", callback_data="game_slots")],
                [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
            ]).adjust(1).as_markup()
        )
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите корректную сумму (например: 10)")

# ФУТБОЛ
@dp.callback_query(F.data == "game_football")
async def game_football_menu(callback: CallbackQuery, state: FSMContext):
    """Меню игры в футбол"""
    balance = db.get_user_balance(callback.from_user.id)
    
    await callback.message.edit_text(
        f'<b>⚽️ Футбол</b>\n\n'
        f'💰 <b>Баланс:</b> {balance}$\n\n'
        f'<b>Введите сумму ставки:</b>\n'
        f'<i>Минимальная ставка: 1$</i>',
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

# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
def get_slots_name(value):
    """Получение названия комбинации слотов"""
    if value == 64: return "7️⃣7️⃣7️⃣"
    elif value == 1: return "🍒🍒🍒" 
    elif value == 22: return "🍋🍋🍋"
    elif value == 43: return "💰💰💰"
    else: return "Проигрыш"

@dp.callback_query(F.data == "back_to_games")
async def back_to_games(callback: CallbackQuery):
    """Возврат в меню игр"""
    await play_game_menu(callback.message)

@dp.callback_query(F.data == "close_games")
async def close_games_menu(callback: CallbackQuery):
    """Закрытие меню игр"""
    await callback.message.delete()

@dp.callback_query(F.data == "cancel_game")
async def cancel_game(callback: CallbackQuery, state: FSMContext):
    """Отмена игры"""
    await state.clear()
    await callback.message.edit_text("❌ Игра отменена")
    await play_game_menu(callback.message)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
