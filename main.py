import datetime
import asyncio
import random

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram import F
from aiogram.utils.keyboard import InlineKeyboardBuilder

from loader import dp, db, bot
from keybords import *
from config import *
from States import *

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
    
    if balance < 0.1:
        await callback.answer("❌ Недостаточно средств. Минимальная ставка: 0.1$", show_alert=True)
        return
    
    await callback.message.edit_text(
        f'<b>🎯 Игра в кости</b>\n\n'
        f'💰 <b>Баланс:</b> {balance}$\n\n'
        f'<b>Введите сумму ставки:</b>\n'
        f'<i>Минимальная ставка: 0.1$</i>',
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
        
        if amount < 0.1:
            await message.answer("❌ Минимальная ставка: 0.1$")
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

# СЛОТЫ
@dp.callback_query(F.data == "game_slots")
async def game_slots_menu(callback: CallbackQuery, state: FSMContext):
    """Меню игры в слоты"""
    balance = db.get_user_balance(callback.from_user.id)
    
    if balance < 0.1:
        await callback.answer("❌ Недостаточно средств. Минимальная ставка: 0.1$", show_alert=True)
        return
    
    await callback.message.edit_text(
        f'<b>🎰 Игровые автоматы</b>\n\n'
        f'💰 <b>Баланс:</b> {balance}$\n\n'
        f'<b>Введите сумму ставки:</b>\n'
        f'<i>Минимальная ставка: 0.1$</i>',
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
        user_id = message.from_user.id
        balance = db.get_user_balance(user_id)
        
        if amount < 0.1:
            await message.answer("❌ Минимальная ставка: 0.1$")
            return
            
        if amount > balance:
            await message.answer(f"❌ Недостаточно средств. Ваш баланс: {balance}$")
            return
        
        # Списываем ставку
        db.update_user_balance(user_id, -amount)
        
        # Обновляем статистику
        db.update_user_stats(user_id, 'total_games', 1)
        db.update_user_stats(user_id, 'total_bet', amount)
        
        # Крутим слоты
        slots_message = await message.answer_dice(emoji="🎰")
        slots_value = slots_message.dice.value
        
        await asyncio.sleep(3)
        
        # Простая логика выигрыша
        win = (slots_value in [1, 22, 43, 64])  # Выигрышные комбинации
        multiplier = 3 if slots_value == 64 else 2  # 777 дает x3, остальные x2
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
            f'🎰 <b>Комбинация:</b> {get_slots_name(slots_value)}\n'
            f'💰 <b>Сумма ставки:</b> {amount}$\n'
            f'📈 <b>Коэффициент:</b> x{multiplier if win else 0}\n\n'
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

def get_slots_name(value):
    """Получение названия комбинации слотов"""
    if value == 64: return "7️⃣7️⃣7️⃣"
    elif value == 1: return "🍒🍒🍒" 
    elif value == 22: return "🍋🍋🍋"
    elif value == 43: return "💰💰💰"
    else: return "💥Проигрыш💥"

# ФУТБОЛ
@dp.callback_query(F.data == "game_football")
async def game_football_menu(callback: CallbackQuery, state: FSMContext):
    """Меню игры в футбол"""
    balance = db.get_user_balance(callback.from_user.id)
    
    if balance < 0.1:
        await callback.answer("❌ Недостаточно средств. Минимальная ставка: 0.1$", show_alert=True)
        return
    
    await callback.message.edit_text(
        f'<b>⚽️ Футбол</b>\n\n'
        f'💰 <b>Баланс:</b> {balance}$\n\n'
        f'<b>Введите сумму ставки:</b>\n'
        f'<i>Минимальная ставка: 0.1$</i>',
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
        user_id = message.from_user.id
        balance = db.get_user_balance(user_id)
        
        if amount < 0.1:
            await message.answer("❌ Минимальная ставка: 0.1$")
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
    try:
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
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)
        await state.clear()

@dp.callback_query(F.data == "cancel_game")
async def cancel_game(callback: CallbackQuery, state: FSMContext):
    """Отмена игры"""
    await state.clear()
    await callback.message.edit_text("❌ Игра отменена")
    await play_game_menu(callback.message)

# КНБ
@dp.callback_query(F.data == "game_knb")
async def game_knb_menu(callback: CallbackQuery, state: FSMContext):
    """Меню игры в КНБ"""
    balance = db.get_user_balance(callback.from_user.id)
    
    if balance < 0.1:
        await callback.answer("❌ Недостаточно средств. Минимальная ставка: 0.1$", show_alert=True)
        return
    
    await callback.message.edit_text(
        f'<b>🪨✂️📄 Камень-Ножницы-Бумага</b>\n\n'
        f'💰 <b>Баланс:</b> {balance}$\n\n'
        f'<b>Введите сумму ставки:</b>\n'
        f'<i>Минимальная ставка: 0.1$</i>',
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
        user_id = message.from_user.id
        balance = db.get_user_balance(user_id)
        
        if amount < 0.1:
            await message.answer("❌ Минимальная ставка: 0.1$")
            return
            
        if amount > balance:
            await message.answer(f"❌ Недостаточно средств. Ваш баланс: {balance}$")
            return
        
        await state.update_data(amount=amount)
        
        await message.answer(
            f'<b>🪨✂️📄 Камень-Ножницы-Бумага</b>\n\n'
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
async def process_knb_game(callback: CallbackQuery, state: FSMContext):
    """Обработка игры в КНБ"""
    try:
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
        
        # Бот делает случайный ход
        bot_choices = ['rock', 'scissors', 'paper']
        bot_choice = random.choice(bot_choices)
        
        # Определяем результат
        win = False
        draw = False
        multiplier = 2
        
        if user_choice == bot_choice:
            draw = True
        elif (user_choice == 'rock' and bot_choice == 'scissors') or \
             (user_choice == 'scissors' and bot_choice == 'paper') or \
             (user_choice == 'paper' and bot_choice == 'rock'):
            win = True
        
        win_amount = amount * multiplier if win else amount if draw else 0
        
        if win:
            db.update_user_balance(user_id, win_amount)
            db.update_user_stats(user_id, 'wins', 1)
            db.update_user_stats(user_id, 'total_win', win_amount)
            result_text = f"🎉 <b>ПОБЕДА!</b>\nВы выиграли: {win_amount}$"
        elif draw:
            db.update_user_balance(user_id, win_amount)
            result_text = f"🤝 <b>НИЧЬЯ!</b>\nВозврат ставки: {amount}$"
        else:
            db.update_user_stats(user_id, 'loses', 1)
            result_text = f"😞 <b>ПРОИГРЫШ</b>\nВы проиграли: {amount}$"
        
        new_balance = db.get_user_balance(user_id)
        
        choice_emojis = {'rock': '🪨', 'scissors': '✂️', 'paper': '📄'}
        
        await callback.message.answer(
            f'<b>🪨✂️📄 Результат игры</b>\n\n'
            f'👤 <b>Ваш ход:</b> {choice_emojis[user_choice]}\n'
            f'🤖 <b>Ход бота:</b> {choice_emojis[bot_choice]}\n'
            f'💰 <b>Сумма ставки:</b> {amount}$\n'
            f'📈 <b>Коэффициент:</b> x{multiplier if win else 1 if draw else 0}\n\n'
            f'{result_text}\n\n'
            f'💰 <b>Новый баланс:</b> {new_balance}$',
            reply_markup=InlineKeyboardBuilder([
                [InlineKeyboardButton(text="🪨 Сыграть еще", callback_data="game_knb")],
                [InlineKeyboardButton(text="📊 Меню игр", callback_data="back_to_games")]
            ]).adjust(1).as_markup()
        )
        await state.clear()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)
        await state.clear()
