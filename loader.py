import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

# Попробуем импортировать aiocryptopay
try:
    from aiocryptopay import AioCryptoPay, Networks
    CRYPTO_AVAILABLE = True
except ImportError as e:
    print(f"❌ aiocryptopay не установлен: {e}")
    AioCryptoPay = None
    Networks = None
    CRYPTO_AVAILABLE = False

from database import DataBase

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Импорт конфигурации
from config import BOT_TOKEN, CRYPTO_PAY_TOKEN, ADMIN

# Инициализация бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Инициализация базы данных
db = DataBase('database.db')

# Инициализация Crypto Pay
crypto = None
if CRYPTO_AVAILABLE and CRYPTO_PAY_TOKEN:
    try:
        crypto = AioCryptoPay(
            token=CRYPTO_PAY_TOKEN,
            network=Networks.MAIN_NET
        )
        print("✅ Crypto Pay инициализирован")
    except Exception as e:
        print(f"❌ Ошибка инициализации Crypto Pay: {e}")
        crypto = None
else:
    print("⚠️ Crypto Pay отключен")

# Импорт административного роутера
try:
    from admin import admin
except ImportError:
    print("⚠️ Админ модуль не найден")
    admin = None

# Блокировка для предотвращения гонки условий
lock = asyncio.Lock()
