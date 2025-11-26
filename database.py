import sqlite3
import logging

logger = logging.getLogger(__name__)

class DataBase:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        logger.info("База данных подключена")

    def db_start(self):
        """Инициализация всех таблиц"""
        try:
            # Таблица пользователей
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    refer_id INTEGER,
                    reg_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица настроек
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY,
                    fake INTEGER DEFAULT 0
                )
            ''')
            
            # Таблица коэффициентов
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS kef (
                    id INTEGER PRIMARY KEY,
                    KEF1 REAL DEFAULT 2.0, KEF2 REAL DEFAULT 6.0, KEF3 REAL DEFAULT 2.0,
                    KEF4 REAL DEFAULT 4.0, KEF5 REAL DEFAULT 2.0, KEF6 REAL DEFAULT 64.0,
                    KEF7 REAL DEFAULT 5.0, KEF8 REAL DEFAULT 3.0, KEF9 REAL DEFAULT 2.0,
                    KEF10 REAL DEFAULT 2.0, KEF11 REAL DEFAULT 2.0, KEF12 REAL DEFAULT 2.0,
                    KEF13 REAL DEFAULT 2.0, KEF14 REAL DEFAULT 5.0, KEF15 REAL DEFAULT 2.0,
                    KEF16 REAL DEFAULT 2.0, KEF17 REAL DEFAULT 14.0
                )
            ''')
            
            # Таблица URL
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS url (
                    id INTEGER PRIMARY KEY,
                    channals TEXT DEFAULT "https://t.me/telegram",
                    checks TEXT DEFAULT "https://t.me/telegram",
                    rules TEXT DEFAULT "https://t.me/telegram",
                    transfer TEXT DEFAULT "https://t.me/telegram",
                    command_game TEXT DEFAULT "https://t.me/telegram",
                    info_stavka TEXT DEFAULT "https://t.me/telegram",
                    news TEXT DEFAULT "https://t.me/telegram"
                )
            ''')
            
            # Таблица статистики
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS stats (
                    id INTEGER PRIMARY KEY,
                    games INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    loses INTEGER DEFAULT 0,
                    payouts REAL DEFAULT 0,
                    income REAL DEFAULT 0,
                    users_count INTEGER DEFAULT 0
                )
            ''')
            
            self.conn.commit()
            logger.info("Таблицы инициализированы")
        except Exception as e:
            logger.error(f"Ошибка инициализации таблиц: {e}")

    def db_settings(self):
        """Инициализация настроек по умолчанию"""
        try:
            self.cursor.execute("INSERT OR IGNORE INTO settings (id, fake) VALUES (1, 0)")
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка инициализации настроек: {e}")

    def db_stats(self):
        """Инициализация статистики"""
        try:
            self.cursor.execute("INSERT OR IGNORE INTO stats (id) VALUES (1)")
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка инициализации статистики: {e}")

    def db_urls(self):
        """Инициализация URL"""
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO url (id) VALUES (1)
            ''')
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка инициализации URL: {e}")

    def user_exists(self, user_id):
        """Проверка существования пользователя"""
        try:
            self.cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
            return self.cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Ошибка user_exists: {e}")
            return False

    def add_users(self, user_id, refer_id=None):
        """Добавление пользователя"""
        try:
            if refer_id:
                self.cursor.execute(
                    "INSERT OR IGNORE INTO users (user_id, refer_id) VALUES (?, ?)", 
                    (user_id, refer_id)
                )
            else:
                self.cursor.execute(
                    "INSERT OR IGNORE INTO users (user_id) VALUES (?)", 
                    (user_id,)
                )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка add_users: {e}")

    def count_ref(self, user_id):
        """Подсчет рефералов"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE refer_id = ?", (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Ошибка count_ref: {e}")
            return 0

    def all_user(self):
        """Получение всех пользователей"""
        try:
            self.cursor.execute("SELECT user_id FROM users")
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка all_user: {e}")
            return []

    def get_URL(self):
        """Получение всех URL"""
        try:
            self.cursor.execute("SELECT * FROM url WHERE id = 1")
            result = self.cursor.fetchone()
            if result:
                return {
                    'channals': result[1],
                    'checks': result[2],
                    'rules': result[3],
                    'transfer': result[4],
                    'command_game': result[5],
                    'info_stavka': result[6],
                    'news': result[7]
                }
        except Exception as e:
            logger.error(f"Ошибка get_URL: {e}")
        
        # ВСЕ значения должны быть валидными URL
        return {
            'channals': "https://t.me/+u6NEVaY6PVxiZTYy",
            'checks': "https://t.me/+pFqhQ8D9hPFiNWU6",
            'rules': "https://t.me/+u6NEVaY6PVxiZTYy",
            'transfer': "https://t.me/+pFqhQ8D9hPFiNWU6", 
            'command_game': "https://t.me/+u6NEVaY6PVxiZTYy",
            'info_stavka': "https://t.me/+u6NEVaY6PVxiZTYy",
            'news': "https://t.me/+u6NEVaY6PVxiZTYy"                                                                        
        }

    def update_url(self, column, values):
        """Обновление URL"""
        try:
            self.cursor.execute(f"UPDATE url SET {column} = ? WHERE id = 1", (values,))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка update_url: {e}")

    def get_all_KEF(self):
        """Получение всех коэффициентов"""
        try:
            self.cursor.execute("SELECT * FROM kef WHERE id = 1")
            result = self.cursor.fetchone()
            if result:
                return {
                    'KEF1': result[1], 'KEF2': result[2], 'KEF3': result[3],
                    'KEF4': result[4], 'KEF5': result[5], 'KEF6': result[6],
                    'KEF7': result[7], 'KEF8': result[8], 'KEF9': result[9],
                    'KEF10': result[10], 'KEF11': result[11], 'KEF12': result[12],
                    'KEF13': result[13], 'KEF14': result[14], 'KEF15': result[15],
                    'KEF16': result[16], 'KEF17': result[17]
                }
        except Exception as e:
            logger.error(f"Ошибка get_all_KEF: {e}")
        
        return {
            'KEF1': 2.0, 'KEF2': 6.0, 'KEF3': 2.0, 'KEF4': 4.0, 'KEF5': 2.0,
            'KEF6': 64.0, 'KEF7': 5.0, 'KEF8': 3.0, 'KEF9': 2.0, 'KEF10': 2.0,
            'KEF11': 2.0, 'KEF12': 2.0, 'KEF13': 2.0, 'KEF14': 5.0, 'KEF15': 2.0,
            'KEF16': 2.0, 'KEF17': 14.0
        }

    def update_kef(self, column, values):
        """Обновление коэффициента"""
        try:
            self.cursor.execute(f"UPDATE kef SET {column} = ? WHERE id = 1", (values,))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка update_kef: {e}")

    def get_cur_KEF(self, column):
        """Получение конкретного коэффициента"""
        try:
            self.cursor.execute(f"SELECT {column} FROM kef WHERE id = 1")
            result = self.cursor.fetchone()
            return result[0] if result else 50
        except Exception as e:
            logger.error(f"Ошибка get_cur_KEF: {e}")
            return 50

    def get_fake_values(self):
        """Получение значения фейк-ставок"""
        try:
            self.cursor.execute("SELECT fake FROM settings WHERE id = 1")
            result = self.cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Ошибка get_fake_values: {e}")
            return 0

    def update_fake(self, value):
        """Обновление фейк-ставок"""
        try:
            self.cursor.execute("UPDATE settings SET fake = ? WHERE id = 1", (value,))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка update_fake: {e}")

    def all_stats(self):
        """Получение общей статистики"""
        try:
            self.cursor.execute("SELECT * FROM stats WHERE id = 1")
            result = self.cursor.fetchone()
            if result:
                return result
        except Exception as e:
            logger.error(f"Ошибка all_stats: {e}")
        
        return [0, 0, 0, 0, 0, 0]

    def all_stats_day(self):
        """Получение дневной статистики"""
        return [0, 0, 0, 0, 0]

    def all_stats_users(self, user_id):
        """Получение статистики пользователя"""
        return [0, 0, 0, 0, 0, 0]

    def refka_cheks_money(self, user_id):
        """Заработок с рефералов"""
        return 0

    def add_count_pay(self, user_id, text, amount):
        """Добавление статистики платежей"""
        pass

    def add_count_pay_stats_day(self, text, amount):
        """Добавление дневной статистики"""
        pass

    def __del__(self):
        """Закрытие соединения при удалении объекта"""
        try:
            self.conn.close()
        except:
            pass
