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
    kb4 = KeyboardButton(text='💸 баланс')
    kb5 = KeyboardButton(text='🎲 Играть')
    kb6 = KeyboardButton(text='👤 Профиль')  # Новая кнопка профиля
    
    if user in ADMIN:
        # Для админа: 3 кнопки в ряду
        keybord.row(kb5, kb4, kb6)    # Первый ряд: Играть, Пополнить, Профиль
        keybord.row(kb1, kb3, kb2)    # Второй ряд: Рефералка, Информация, Админка
    else:
        # Для обычных пользователей: 3 кнопки в ряду
        keybord.row(kb5, kb4, kb6)    # Первый ряд: Играть, Пополнить, Профиль
        keybord.row(kb1, kb3)         # Второй ряд: Рефералка, Информация
        
    return keybord.as_markup(resize_keyboard=True, input_field_placeholder='Выберите действие...')
    
    if user in ADMIN:
        keybord.add(kb1, kb3, kb4, kb5, kb2).adjust(2)  # 2 кнопки в ряд
        return keybord.as_markup(resize_keyboard=True)
    
    keybord.add(kb1, kb3, kb4, kb5).adjust(2)  # 2 кнопки в ряд для обычных пользователей
    return keybord.as_markup(resize_keyboard=True)


def kb_admin():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text='📊 Статистика проекта', callback_data='stats_project'),
        InlineKeyboardButton(text='👤 Статистика игрока', callback_data='stats_user')
    )
    builder.row(
        InlineKeyboardButton(text='💳 Пополнить баланс казино', callback_data='add_balance'),
        InlineKeyboardButton(text='💰 Фейк пополнение', callback_data='fake_deposit')  # ← ДОБАВЬ ЭТУ КНОПКУ
    )
    builder.row(
        InlineKeyboardButton(text='👀 Настройки фейк ставок', callback_data='settings_fake'),
        InlineKeyboardButton(text='⚙️ Коэффициенты', callback_data='kef_edit')
    )
    builder.row(
        InlineKeyboardButton(text='🪨✂️📄 КНБ', callback_data='knb'),
        InlineKeyboardButton(text='📢 Рассылка', callback_data='all_message_send')
    )
    builder.row(
        InlineKeyboardButton(text='🔗 Редактировать URL', callback_data='urls'),
        InlineKeyboardButton(text='🗑 Удалить чеки', callback_data='deleted_checks')
    )
    builder.row(
        InlineKeyboardButton(text='📦 Получить БД', callback_data='send_db')
    )
    return builder.as_markup()


def ikb_tip_rassilka():
    bilder = InlineKeyboardBuilder([
        [InlineKeyboardButton(text='📸 Фото', callback_data='photo'),
         InlineKeyboardButton(text='✍️ Текст', callback_data='Texts')],
        [InlineKeyboardButton(text='« Назад', callback_data='back_admin')]
    ])
    return bilder.as_markup()


def kb_answer_delete():
    bilder = InlineKeyboardBuilder([
        [InlineKeyboardButton(text='✅ Да', callback_data='YesDel'),
         InlineKeyboardButton(text='❌ Нет', callback_data='back_admin')],
    ])
    return bilder.as_markup()


def kb_info():
    # Безопасное получение URL с реальными запасными значениями
    channals_url = safe_get_url('channals', 'https://t.me/+u6NEVaY6PVxiZTYy')
    news_url = safe_get_url('news', 'https://t.me/+u6NEVaY6PVxiZTYy')
    command_url = safe_get_url('command_game', 'https://t.me/+u6NEVaY6PVxiZTYy')
    transfer_url = safe_get_url('transfer', 'https://t.me/+pFqhQ8D9hPFiNWU6')
    rules_url = safe_get_url('rules', 'https://t.me/+u6NEVaY6PVxiZTYy')
    
    bilder = InlineKeyboardBuilder([
        [InlineKeyboardButton(text='🎲 Играть', url=channals_url),
         InlineKeyboardButton(text='📄 Новости', url=news_url)],
        # Закомментируйте эту строку если command_game не URL
        # [InlineKeyboardButton(text='✍️ Ключевые слова', url=command_url)],
        [InlineKeyboardButton(text='💸 Выплаты', url=transfer_url),
         InlineKeyboardButton(text='❓ Правила', url=rules_url)]
    ])
    return bilder.as_markup()


def kb_fake_switch(values: int):
    text_button = "🔴 Отключить" if values else '🟢 Включить'
    bilder = InlineKeyboardBuilder([
        [InlineKeyboardButton(text=text_button, callback_data=f'fake|{values}')],
        [InlineKeyboardButton(text='« Назад', callback_data=f'back_admin')]
    ])
    return bilder.as_markup()


def kb_back_admin():
    bilder = InlineKeyboardBuilder([
        [InlineKeyboardButton(text='« Назад', callback_data=f'back_admin')]
    ])
    return bilder.as_markup()


def kb_edit_kef(data: dict):
    bilder = InlineKeyboardBuilder()
    # Проверяем что data не None и является словарем
    if data and isinstance(data, dict):
        for index, values in enumerate(data.items(), start=1):
            bilder.add(InlineKeyboardButton(text=f"{index}) [{values[1]}x]", callback_data=f'new_kef|{values[0]}|{values[1]}'))
    else:
        # Если data пустое, создаем пустую клавиатуру
        bilder.add(InlineKeyboardButton(text="Нет данных", callback_data="none"))
    
    bilder.adjust(3)
    bilder.row(InlineKeyboardButton(text='« Назад', callback_data=f'back_admin'), width=1)
    return bilder.as_markup()


def kb_KNB_twist(cur_value:int):
    bilder = InlineKeyboardBuilder([
        [InlineKeyboardButton(text=f'⚙️ {cur_value}%', callback_data=f'Twist_knb|{cur_value}')],
        [InlineKeyboardButton(text='« Назад', callback_data=f'back_admin')]
    ])
    return bilder.as_markup()


def kb_send_chek(url):
    checks_url = safe_get_url('checks', '#')
    bilder = InlineKeyboardBuilder([
        [InlineKeyboardButton(text=f'🎁 Забрать приз', url=url)],
        [InlineKeyboardButton(text='💸 Сделать ставку', url=checks_url)]
    ])
    return bilder.as_markup()


def kb_viev_post(url, amount):
    bilder = InlineKeyboardBuilder([
        [InlineKeyboardButton(text=f'🎁 [{round(float(amount), 2)}$]', url=url)],
    ])
    return bilder.as_markup()


def get_cashback_check(url, amount):
    keybord = InlineKeyboardBuilder([
        [InlineKeyboardButton(text=f'💸 Получить {round(float(amount), 2)}$', url=url)]
    ])
    return keybord.as_markup()


def ikb_send_post_photo():
    bilder = InlineKeyboardBuilder([
        [InlineKeyboardButton(text='✅ Запустить рассылку', callback_data='post_photo_go'),
         InlineKeyboardButton(text='❌ Отменить', callback_data='close_del')],
    ])
    return bilder.as_markup()


def ikb_send_post():
    bilder = InlineKeyboardBuilder([
        [InlineKeyboardButton(text='✅ Запустить рассылку', callback_data='post_go'),
        InlineKeyboardButton(text='❌ Отменить', callback_data='close_del')],
    ])
    return bilder.as_markup()


def kb_urls():
    bilder = InlineKeyboardBuilder([
        [InlineKeyboardButton(text='Канал', callback_data=f'UrlEdit|channals|Канал'),
         InlineKeyboardButton(text='Правила', callback_data=f'UrlEdit|rules|Правила')],
        [InlineKeyboardButton(text='Счет для оплаты', callback_data=f'UrlEdit|checks|Счет для оплаты')],
        [InlineKeyboardButton(text='Выплаты', callback_data=f'UrlEdit|transfer|Выплаты'),
         InlineKeyboardButton(text='Новости', callback_data=f'UrlEdit|news|Новости')],
        [InlineKeyboardButton(text='Как сделать ставку', callback_data=f'UrlEdit|info_stavka|Как сделать ставку')],
        [InlineKeyboardButton(text='Ключевые слова', callback_data=f'UrlEdit|command_game|Ключевые слова')],
        [InlineKeyboardButton(text='« Назад', callback_data=f'back_admin')]
    ])
    return bilder.as_markup()





