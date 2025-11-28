import random
from collections import OrderedDict

from aiogram.types import InlineKeyboardButton, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from captcha_element import captcha_dict
from config import *
from loader import db

def shuffle_dict(d):
    keys = list(d.keys())
    random.shuffle(keys)
    return OrderedDict([(k, d[k]) for k in keys])


async def captcha_keybord(word):
    keybord = InlineKeyboardBuilder()
    button = []
    res = shuffle_dict(captcha_dict)
    for k, v in res.items():
        if len(button) == 6:
            break
        button.append(InlineKeyboardButton(text=f'{v}', callback_data=f'Captcha|{k}|{word}'))
    keybord.add(*button)
    keybord.adjust(3)
    return keybord.as_markup()


def safe_get_url(key, default_url="#"):
    """Безопасное получение URL с запасным значением"""
    try:
        urls = db.get_URL()
        if urls and urls.get(key):
            return urls.get(key)
    except:
        pass
    return default_url


def send_stavka():
    checks_url = safe_get_url('checks', '#')
    keybord = InlineKeyboardBuilder([
        [InlineKeyboardButton(text='💸 Сделать ставку', url=checks_url)]
    ])
    return keybord.as_markup()


def kb_url_Channel():
    channals_url = safe_get_url('channals', '#')
    keybord = InlineKeyboardBuilder([
        [InlineKeyboardButton(text='💸 Сделать ставку', url=channals_url)]
    ])
    return keybord.as_markup()


def send_okey():
    keybord = InlineKeyboardBuilder([
        [InlineKeyboardButton(text='✅ completed', callback_data=f'null')]
    ])
    return keybord.as_markup()


def get_cashback(user, amount):
    keybord = InlineKeyboardBuilder([
        [InlineKeyboardButton(text=f'💸 Получить {round(float(amount), 2)}$', callback_data=f'GET_CASH|{user}|{amount}')]
    ])
    return keybord.as_markup()


def get_fake_cashback(amount, status):
    text = f'✅ Кэшбэк получен [{amount}$]' if status else f'💸 Получить {round(float(amount), 2)}$'
    keybord = InlineKeyboardBuilder([
        [InlineKeyboardButton(text=text, callback_data=f'None')]
    ])
    return keybord.as_markup()


def okay_cashback(amount):
    keybord = InlineKeyboardBuilder([
        [InlineKeyboardButton(text=f'✅ Кэшбэк получен [{amount}$]', callback_data=f'nul')]
    ])
    return keybord.as_markup()


def keybord_add_balance(url):
    keybord = InlineKeyboardBuilder([
        [InlineKeyboardButton(text='💸 Оплатить', url=url)]
    ])
    return keybord.as_markup()


def commands_game():
    command_url = safe_get_url('command_game', '#')
    keybord = InlineKeyboardBuilder([
        [InlineKeyboardButton(text='📄 Команды', url=command_url)]
    ])
    return keybord.as_markup()


def ikb_stop():
    bilder = InlineKeyboardBuilder([
        [InlineKeyboardButton(text='⛔️ Выйти из режима ввода данных', callback_data='back_admin')]
    ])
    return bilder.as_markup()


def kb_menu(user):
    keybord = ReplyKeyboardBuilder()
    
    # Создаем все кнопки
    kb1 = KeyboardButton(text='📎 Реферальная программа')
    kb2 = KeyboardButton(text='👑 Админка') 
    kb3 = KeyboardButton(text='💭 Информация')
    kb4 = KeyboardButton(text='💸 Баланс')  # Исправлен регистр
    kb5 = KeyboardButton(text='🎲 Играть')
    kb6 = KeyboardButton(text='👤 Профиль')
    
    if user in ADMIN:
        # Для админа: 3 кнопки в ряду
        keybord.row(kb5, kb4, kb6)    # Первый ряд: Играть, Баланс, Профиль
        keybord.row(kb1, kb3, kb2)    # Второй ряд: Рефералка, Информация, Админка
    else:
        # Для обычных пользователей: 3 кнопки в ряду
        keybord.row(kb5, kb4, kb6)    # Первый ряд: Играть
