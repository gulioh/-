import sqlite3 as sq
import logging

logger = logging.getLogger(__name__)

class DataBase:
    def __init__(self, db_file):
        self.connection = sq.connect(db_file, check_same_thread=False)
        self.cur = self.connection.cursor()
        self.db_start()
        self.db_settings()
        self.db_stats()
        self.db_urls()

    def db_urls(self):
        """Инициализация URL"""
        try:
            self.cur.execute('''
                CREATE TABLE IF NOT EXISTS urls(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channals TEXT DEFAULT 'https://t.me/+u6NEVaY6PVxiZTYy',
                    checks TEXT DEFAULT 'https://t.me/+pFqhQ8D9hPFiNWU6',
                    rules TEXT DEFAULT 'https://t.me/+u6NEVaY6PVxiZTYy',
                    transfer TEXT DEFAULT 'https://t.me/+pFqhQ8D9hPFiNWU6',
                    command_game TEXT DEFAULT '/game',
                    info_stavka TEXT DEFAULT 'Информация о ставках',
                    news TEXT DEFAULT 'https://t.me/+u6NEVaY6PVxiZTYy'
                )
            ''')
            # Добавляем запись по умолчанию если её нет
            self.cur.execute('INSERT OR IGNORE INTO urls (id) VALUES (1)')
            self.connection.commit()
            logger.info("✅ URL таблица инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации URL: {e}")

    def db_start(self):
        with self.connection:
            self.cur.execute('''
                CREATE TABLE IF NOT EXISTS users(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    count_play INTEGER NOT NULL DEFAULT 0,
                    win INTEGER NOT NULL DEFAULT 0,
                    lose INTEGER NOT NULL DEFAULT 0,
                    balance_win FLOAT NOT NULL DEFAULT 0,
                    balance_lose FLOAT NOT NULL DEFAULT 0,
                    refere_id INTEGER,
                    balance_ref INTEGER NOT NULL DEFAULT 0,
                    balance FLOAT NOT NULL DEFAULT 0,
                    UNIQUE(user_id)
                )
            ''')
            
            # Таблица транзакций
            self.cur.execute('''
                CREATE TABLE IF NOT EXISTS transactions(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    transaction_type TEXT NOT NULL,
                    amount FLOAT NOT NULL,
                    status TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    def db_stats(self):
        with self.connection:
            self.cur.execute('''
                CREATE TABLE IF NOT EXISTS stats(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    count_play INTEGER NOT NULL DEFAULT 0,
                    win INTEGER NOT NULL DEFAULT 0,
                    lose INTEGER NOT NULL DEFAULT 0,
                    balance_win FLOAT NOT NULL DEFAULT 0,
                    balance_lose FLOAT NOT NULL DEFAULT 0
                )
            ''')
            # Добавляем запись по умолчанию
            self.cur.execute('INSERT OR IGNORE INTO stats (id) VALUES (1)')

    def db_settings(self):
        with self.connection:
            self.cur.execute('''
                CREATE TABLE IF NOT EXISTS settings(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fake INTEGER NOT NULL DEFAULT 0,
                    KEF1 FLOAT NOT NULL DEFAULT 1.7,
                    KEF2 FLOAT NOT NULL DEFAULT 1.3,
                    KEF3 FLOAT NOT NULL DEFAULT 1.7,
                    KEF4 FLOAT NOT NULL DEFAULT 2.7,
                    KEF5 FLOAT NOT NULL DEFAULT 1.7,
                    KEF6 FLOAT NOT NULL DEFAULT 3,
                    KEF7 FLOAT NOT NULL DEFAULT 5,
                    KEF8 FLOAT NOT NULL DEFAULT 4,
                    KEF9 FLOAT NOT NULL DEFAULT 7,
                    KEF10 FLOAT NOT NULL DEFAULT 1.7,
                    KEF11 FLOAT NOT NULL DEFAULT 1.2,
                    KEF12 FLOAT NOT NULL DEFAULT 1.2,
                    KEF13 FLOAT NOT NULL DEFAULT 1.7,
                    KEF14 FLOAT NOT NULL DEFAULT 3,
                    KEF15 FLOAT NOT NULL DEFAULT 2.5,
                    KEF16 FLOAT NOT NULL DEFAULT 1.7,
                    KEF17 FLOAT NOT NULL DEFAULT 5,
                    KNB INTEGER NOT NULL DEFAULT 100
                )
            ''')
            # Добавляем запись по умолчанию
            self.cur.execute('INSERT OR IGNORE INTO settings (id) VALUES (1)')

    def get_URL(self):
        try:
            self.cur.execute("SELECT * FROM urls WHERE id = 1")
            result = self.cur.fetchone()
            
            if result:
                return {
                    'channals': result[1] or "https://t.me/+u6NEVaY6PVxiZTYy",
                    'checks': result[2] or "https://t.me/+pFqhQ8D9hPFiNWU6", 
                    'rules': result[3] or "https://t.me/+u6NEVaY6PVxiZTYy",
                    'transfer': result[4] or "https://t.me/+pFqhQ8D9hPFiNWU6",
                    'command_game': result[5] or "/game",
                    'info_stavka': result[6] or "Информация о ставках",
                    'news': result[7] or "https://t.me/+u6NEVaY6PVxiZTYy"                                                                        
                }
        except Exception as e:
            logger.error(f"Ошибка получения URL: {e}")
        
        # Значения по умолчанию
        return {
            'channals': "https://t.me/+u6NEVaY6PVxiZTYy",
            'checks': "https://t.me/+pFqhQ8D9hPFiNWU6",
            'rules': "https://t.me/+u6NEVaY6PVxiZTYy",
            'transfer': "https://t.me/+pFqhQ8D9hPFiNWU6", 
            'command_game': "/game",
            'info_stavka': "Информация о ставках",
            'news': "https://t.me/+u6NEVaY6PVxiZTYy"                                                                        
        }

    def update_url(self, column, values):
        with self.connection:
            return self.cur.execute(f'UPDATE urls SET {column} = ? WHERE id = 1', (values,))

    def all_stats_day(self):
        with self.connection:
            result = self.cur.execute('SELECT count_play, win, lose, balance_win, balance_lose FROM stats WHERE id = 1').fetchone()
            return result if result else (0, 0, 0, 0, 0)

    def all_stats(self):
        with self.connection:
            # Исправленный запрос - убрали SUM из COUNT(user_id)
            result = self.cur.execute('SELECT SUM(count_play), SUM(win), SUM(lose), SUM(balance_win), SUM(balance_lose), COUNT(user_id) FROM users').fetchone()
            return result if result else (0, 0, 0, 0, 0, 0)

    def all_stats_users(self, user):
        with self.connection:
            result = self.cur.execute('SELECT count_play, win, lose, balance_win, balance_lose, balance_ref FROM users WHERE user_id = ?', (user,)).fetchone()
            return result if result else (0, 0, 0, 0, 0, 0)

    def add_users(self, user_id, refere_id=None):
        with self.connection:
            if refere_id is not None:
                return self.cur.execute('INSERT OR IGNORE INTO users (user_id, refere_id) VALUES (?, ?)', (user_id, refere_id))
            else:
                return self.cur.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))

    def refka_cheks_money(self, user_id):
        with self.connection:
            result = self.cur.execute('SELECT balance_ref FROM users WHERE user_id = ?', (user_id,)).fetchone()
            return result[0] if result else 0

    def add_balances_ref(self, user_id, amount):
        with self.connection:
            return self.cur.execute('UPDATE users SET balance_ref = balance_ref + ? WHERE user_id = ?', (amount, user_id))

    def count_ref(self, user_id):
        with self.connection:
            result = self.cur.execute("SELECT COUNT(id) FROM users WHERE refere_id = ?", (user_id,)).fetchone()
            return result[0] if result else 0

    def select_referi(self, user_id):
        with self.connection:
            result = self.cur.execute('SELECT refere_id FROM users WHERE user_id = ?', (user_id,)).fetchone()
            return result[0] if result else None

    def user_exists(self, user_id):
        with self.connection:
            result = self.cur.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchall()
            return bool(len(result))

    def add_count_pay(self, user_id, text, amount):
        with self.connection:
            if text == 'win':
                return self.cur.execute('UPDATE users SET count_play = count_play + 1, win = win + 1, balance_win = balance_win + ? WHERE user_id = ?', (amount, user_id))
            if text == 'lose':
                return self.cur.execute('UPDATE users SET count_play = count_play + 1, lose = lose + 1, balance_lose = balance_lose + ? WHERE user_id = ?', (amount, user_id))

    def add_count_pay_stats_day(self, text, amount):
        with self.connection:
            if text == 'win':
                return self.cur.execute('UPDATE stats SET count_play = count_play + 1, win = win + 1, balance_win = balance_win + ? WHERE id = 1', (amount,))
            if text == 'lose':
                return self.cur.execute('UPDATE stats SET count_play = count_play + 1, lose = lose + 1, balance_lose = balance_lose + ? WHERE id = 1', (amount,))

    def del_stats_day(self):
        with self.connection:
            return self.cur.execute('UPDATE stats SET count_play = 0, win = 0, lose = 0, balance_win = 0, balance_lose = 0 WHERE id = 1')

    def get_fake_values(self):
        with self.connection:
            result = self.cur.execute('SELECT fake FROM settings WHERE id = 1').fetchone()
            return result[0] if result else 0

    def update_fake(self, values):
        with self.connection:
            return self.cur.execute('UPDATE settings SET fake = ? WHERE id = 1', (values,))

    def get_all_KEF(self):
        with self.connection:
            res = self.cur.execute('SELECT * FROM settings WHERE id = 1').fetchone()
            if res:
                return {
                    'KEF1': res[2], 'KEF2': res[3], 'KEF3': res[4], 'KEF4': res[5], 'KEF5': res[6],
                    'KEF6': res[7], 'KEF7': res[8], 'KEF8': res[9], 'KEF9': res[10], 'KEF10': res[11],
                    'KEF11': res[12], 'KEF12': res[13], 'KEF13': res[14], 'KEF14': res[15], 'KEF15': res[16],
                    'KEF16': res[17], 'KEF17': res[18]
                }
            return {}

    def update_kef(self, column, values):
        with self.connection:
            return self.cur.execute(f'UPDATE settings SET {column} = ? WHERE id = 1', (values,))

    def get_cur_KEF(self, column):
        with self.connection:
            result = self.cur.execute(f'SELECT {column} FROM settings WHERE id = 1').fetchone()
            return result[0] if result else 1.0

    def get_KNB_procent(self):
        with self.connection:
            result = self.cur.execute('SELECT KNB FROM settings WHERE id = 1').fetchone()
            return result[0] if result else 100

    def all_user(self):
        with self.connection:
            return self.cur.execute('SELECT user_id FROM users').fetchall()

    # Новые методы для работы с балансом
    def get_user_balance(self, user_id):
        with self.connection:
            result = self.cur.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)).fetchone()
            return result[0] if result else 0.0

    def update_user_balance(self, user_id, amount):
        with self.connection:
            return self.cur.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))

    def update_user_stats(self, user_id, stat_type, value):
        with self.connection:
            if stat_type == 'total_games':
                self.cur.execute('UPDATE users SET count_play = count_play + ? WHERE user_id = ?', (value, user_id))
            elif stat_type == 'total_bet':
                self.cur.execute('UPDATE users SET balance_lose = balance_lose + ? WHERE user_id = ?', (value, user_id))
            elif stat_type == 'wins':
                self.cur.execute('UPDATE users SET win = win + ? WHERE user_id = ?', (value, user_id))
            elif stat_type == 'loses':
                self.cur.execute('UPDATE users SET lose = lose + ? WHERE user_id = ?', (value, user_id))
            elif stat_type == 'total_win':
                self.cur.execute('UPDATE users SET balance_win = balance_win + ? WHERE user_id = ?', (value, user_id))

    def add_transaction(self, user_id, transaction_type, amount, status, description=None):
        with self.connection:
            return self.cur.execute('''
                INSERT INTO transactions (user_id, transaction_type, amount, status, description) 
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, transaction_type, amount, status, description))
