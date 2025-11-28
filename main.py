from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import KeyboardButton, InlineKeyboardButton
import random

def kb_menu(user_id):
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🎲 Играть"))
    builder.row(KeyboardButton(text="💸 Баланс"))
    builder.row(KeyboardButton(text="👤 Профиль"))
    builder.row(KeyboardButton(text="📎 Реферальная программа"))
    builder.row(KeyboardButton(text="💭 Информация"))
    if user_id in [123456789]:  # Ваш ID
        builder.row(KeyboardButton(text="👑 Админка"))
    return builder.as_markup(resize_keyboard=True)

def kb_info():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📞 Поддержка", url="https://t.me/username"))
    builder.row(InlineKeyboardButton(text="📋 Меню", callback_data="back_to_menu"))
    return builder.as_markup()

def kb_admin():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"))
    builder.row(InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_mailing"))
    builder.row(InlineKeyboardButton(text="📋 Меню", callback_data="back_to_menu"))
    return builder.as_markup()

async def captcha_keybord(word):
    builder = InlineKeyboardBuilder()
    words = list(set([word] + random.sample(list(captcha_dict.keys()), 3)))
    random.shuffle(words)
    for w in words:
        builder.row(InlineKeyboardButton(text=captcha_dict[w], callback_data=f"Captcha|{w}|{word}"))
    return builder.as_markup()

# Резервный словарь капчи
captcha_dict = {
    'apple': '🍎', 'banana': '🍌', 'grape': '🍇', 'strawberry': '🍓',
    'pineapple': '🍍', 'watermelon': '🍉', 'cherry': '🍒', 'peach': '🍑'
}
