import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiocryptopay import CryptoPay, Networks
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
try:
    crypto = CryptoPay(
        token=CRYPTO_PAY_TOKEN,
        network=Networks.MAIN_NET  # Используйте Networks.TEST_NET для тестов
    )
    print("✅ Crypto Pay инициализирован")
except Exception as e:
    print(f"❌ Ошибка инициализации Crypto Pay: {e}")
    crypto = None

# Импорт административного роутера
from admin import admin

# Блокировка для предотвращения гонки условий
lock = asyncio.Lock()
