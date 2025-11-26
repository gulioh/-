import sqlite3 as sq

class DataBase:
    def __init__(self, db_file):
        self.connection = sq.connect(db_file)
        self.cur = self.connection.cursor()

    def db_start(self):
        with self.connection:
            self.cur.execute('CREATE TABLE IF NOT EXISTS users('
                             'id INTEGER PRIMARY KEY AUTOINCREMENT,'
                             'user_id INTEGER NOT NULL,'
                             'count_play INTEGER NOT NULL DEFAULT 0,'
                             'win INTEGER NOT NULL DEFAULT 0,'
                             'lose INTEGER NOT NULL DEFAULT 0,'
                             'balance_win FLOAT NOT NULL DEFAULT 0,'
                             'balance_lose FLOAT NOT NULL DEFAULT 0,'
                             'refere_id INTEGER,'
                             'balance_ref INTEGER NOT NULL DEFAULT 0,'
                             'UNIQUE(user_id))')

    def db_stats(self):
        with self.connection:
            self.cur.execute('CREATE TABLE IF NOT EXISTS stats('
                             'count_play INTEGER NOT NULL DEFAULT 0,'
                             'win INTEGER NOT NULL DEFAULT 0,'
                             'lose INTEGER NOT NULL DEFAULT 0,'
                             'balance_win FLOAT NOT NULL DEFAULT 0,'
                             'balance_lose FLOAT NOT NULL DEFAULT 0)')

    def db_settings(self):
        with self.connection:
            self.cur.execute('CREATE TABLE IF NOT EXISTS settings('
                             'fake INTEGER NOT NULL DEFAULT 0,'
                             'KEF1 FLOAT NOT NULL DEFAULT 1.7,'
                             'KEF2 FLOAT NOT NULL DEFAULT 1.3,'
                             'KEF3 FLOAT NOT NULL DEFAULT 1.7,'
                             'KEF4 FLOAT NOT NULL DEFAULT 2.7,'
                             'KEF5 FLOAT NOT NULL DEFAULT 1.7,'
                             'KEF6 FLOAT NOT NULL DEFAULT 3,'
                             'KEF7 FLOAT NOT NULL DEFAULT 5,'
                             'KEF8 FLOAT NOT NULL DEFAULT 4,'
                             'KEF9 FLOAT NOT NULL DEFAULT 7,'
                             'KEF10 FLOAT NOT NULL DEFAULT 1.7,'
                             'KEF11 FLOAT NOT NULL DEFAULT 1.2,'
                             'KEF12 FLOAT NOT NULL DEFAULT 1.2,'
                             'KEF13 FLOAT NOT NULL DEFAULT 1.7,'
                             'KEF14 FLOAT NOT NULL DEFAULT 3,'
                             'KEF15 FLOAT NOT NULL DEFAULT 2.5,'
                             'KEF16 FLOAT NOT NULL DEFAULT 1.7,'
                             'KEF17 FLOAT NOT NULL DEFAULT 5,'
                             'KNB INTEGER NOT NULL DEFAULT 100)')

def get_URL(self):
    try:
        self.cursor.execute("SELECT * FROM url")
        result = self.cursor.fetchone()
        
        if result and len(result) >= 7:
            return {
                'channals': result[0],
                'checks': result[1], 
                'rules': result[2],
                'transfer': result[3],
                'command_game': result[4],
                'info_stavka': result[5],
                'news': result[6]
            }
    except:
        pass
    
    # Если что-то пошло не так, возвращаем значения по умолчанию
    return {
        'channals': "https://t.me/+u6NEVaY6PVxiZTYy",
        'checks': "https://t.me/+pFqhQ8D9hPFiNWU6",
        'rules': "https://t.me/+u6NEVaY6PVxiZTYy",
        'transfer': "https://t.me/+pFqhQ8D9hPFiNWU6", 
        'command_game': "/game",
        'info_stavka': "Информация о ставках",
        'news': "https://t.me/+u6NEVaY6PVxiZTYy"                                                                        
    }
    def all_stats_day(self):
        with self.connection:
            return self.cur.execute('SELECT count_play, win, lose, balance_win, balance_lose FROM stats').fetchone()

    def all_stats(self):
        with self.connection:
            return self.cur.execute('SELECT sum(count_play), sum(win), sum(lose), sum(balance_win), sum(balance_lose), count(user_id) FROM users').fetchall()[0]

    def all_stats_users(self, user):
        with self.connection:
            return self.cur.execute('SELECT count_play, win, lose, balance_win, balance_lose, balance_ref FROM users WHERE user_id = ?', (user,)).fetchone()


    def add_users(self, user_id, refere_id=None):
        with self.connection:
            if refere_id != None:
                return self.cur.execute('INSERT INTO users (user_id, refere_id) VALUES (?, ?)', (user_id, refere_id))
            else:
                return self.cur.execute('INSERT INTO users (user_id) VALUES (?)', (user_id,))

    def refka_cheks_money(self, user_id):
        with self.connection:
            return self.cur.execute('SELECT balance_ref FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]

    def add_balances_ref(self, user_id, amount):
        with self.connection:
            return self.cur.execute('UPDATE users SET balance_ref = balance_ref + ? WHERE user_id = ?', (amount, user_id))


    def count_ref(self, user_id):
        with self.connection:
            return self.cur.execute("SELECT COUNT(id) as 'Количество_рефералов' FROM users WHERE refere_id = ?",
                               (user_id,)).fetchone()[0]

    def select_referi(self, user_id):
        with self.connection:
            return self.cur.execute('SELECT refere_id FROM users WHERE user_id = ?', (user_id,)).fetchone()[0]

    def user_exists(self, user_id):
        with self.connection:
            result = self.cur.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchall()
            return bool(len(result))


    def add_count_pay(self, user_id, text, amount):
        with self.connection:
            if text == 'win':
                return self.cur.execute(f'UPDATE users SET count_play = count_play + 1, win = win + 1, balance_win = balance_win + {amount} WHERE user_id = {user_id}')
            if text == 'lose':
                return self.cur.execute(f'UPDATE users SET count_play = count_play + 1, lose = lose + 1, balance_lose = balance_lose + {amount} WHERE user_id = {user_id}')

    def add_count_pay_stats_day(self, text, amount):
        with self.connection:
            if text == 'win':
                return self.cur.execute(f'UPDATE stats SET count_play = count_play + 1, win = win + 1, balance_win = balance_win + {amount}')
            if text == 'lose':
                return self.cur.execute(f'UPDATE stats SET count_play = count_play + 1, lose = lose + 1, balance_lose = balance_lose + {amount}')

    def del_stats_day(self):
        with self.connection:
            return self.cur.execute(f'UPDATE stats SET count_play = 0, win = 0, lose = 0, balance_win = 0, balance_lose = 0')



    def get_fake_values(self):
        with self.connection:
            return self.cur.execute('SELECT fake FROM settings').fetchone()[0]

    def update_fake(self, values):
        with self.connection:
            return self.cur.execute(f'UPDATE settings SET fake = ?', (values,))

    def get_all_KEF(self):
        with self.connection:
            res = self.cur.execute('SELECT * FROM settings').fetchone()
            return {'KEF1': res[1],'KEF2': res[2],'KEF3': res[3],'KEF4': res[4],'KEF5': res[5],'KEF6': res[6],'KEF7': res[7],
                    'KEF8': res[8],'KEF9': res[9],'KEF10': res[10],'KEF11': res[11],'KEF12': res[12],'KEF13': res[13],'KEF14': res[14],
                    'KEF15': res[15],'KEF16': res[16],'KEF17': res[17]}



    def update_kef(self, column, values):
        with self.connection:
            return self.cur.execute(f'UPDATE settings SET {column} = ?', (values,))

    def get_cur_KEF(self, column):
        with self.connection:
            return self.cur.execute(f'SELECT {column} FROM settings').fetchone()[0]

    def get_KNB_procent(self):
        with self.connection:
            return self.cur.execute(f'SELECT KNB FROM settings').fetchone()[0]

    def all_user(self):
        with self.connection:
            return self.cur.execute('SELECT user_id FROM users').fetchall()



    def get_URL(self):
        with self.connection:
            result = self.cur.execute(f'SELECT * FROM urls').fetchone()
            return {'channals':result[0], 'checks':result[1], 'rules':result[2], 'transfer':result[3], 'command_game':result[4], 'info_stavka':result[5], 'news':result[6]}

    def update_url(self, column, values):
        with self.connection:

            return self.cur.execute(f'UPDATE urls SET {column} = ?', (values,))


def count_ref(self, user_id):
    """Подсчет количества рефералов пользователя"""
    try:
        self.cursor.execute("SELECT COUNT(*) FROM users WHERE refer_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0
    except Exception as e:
        print(f"Ошибка в count_ref: {e}")
        return 0

def refka_cheks_money(self, user_id):
    """Подсчет заработанного с рефералов"""
    try:
        self.cursor.execute("SELECT SUM(amount) FROM ref_stats WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result and result[0] else 0
    except Exception as e:
        print(f"Ошибка в refka_cheks_money: {e}")
        return 0

def user_exists(self, user_id):
    """Проверка существования пользователя"""
    try:
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result is not None
    except Exception as e:
        print(f"Ошибка в user_exists: {e}")
        return False

def add_users(self, user_id, refer_id=None):
    """Добавление пользователя"""
    try:
        if refer_id:
            self.cursor.execute("INSERT OR IGNORE INTO users (user_id, refer_id) VALUES (?, ?)", (user_id, refer_id))
        else:
            self.cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        self.conn.commit()
    except Exception as e:
        print(f"Ошибка в add_users: {e}")

def all_user(self):
    """Получение всех пользователей"""
    try:
        self.cursor.execute("SELECT user_id FROM users")
        return self.cursor.fetchall()
    except Exception as e:
        print(f"Ошибка в all_user: {e}")
        return []

class DataBase:
    def __init__(self, db_file):
        # ваш существующий код инициализации
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
    
    def count_ref(self, user_id):
        """Подсчет количества рефералов пользователя"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE refer_id = ?", (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            print(f"Ошибка в count_ref: {e}")
            return 0
    
    def refka_cheks_money(self, user_id):
        """Подсчет заработанного с рефералов"""
        try:
            self.cursor.execute("SELECT SUM(amount) FROM ref_stats WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result and result[0] else 0
        except Exception as e:
            print(f"Ошибка в refka_cheks_money: {e}")
            return 0
    
    def user_exists(self, user_id):
        """Проверка существования пользователя"""
        try:
            self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
            return result is not None
        except Exception as e:
            print(f"Ошибка в user_exists: {e}")
            return False
    
    def add_users(self, user_id, refer_id=None):
        """Добавление пользователя"""
        try:
            if refer_id:
                self.cursor.execute("INSERT OR IGNORE INTO users (user_id, refer_id) VALUES (?, ?)", (user_id, refer_id))
            else:
                self.cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка в add_users: {e}")
    
    def all_user(self):
        """Получение всех пользователей"""
        try:
            self.cursor.execute("SELECT user_id FROM users")
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Ошибка в all_user: {e}")
            return []
    
    def get_fake_values(self):
        """Получение значения фейк-ставок"""
        try:
            self.cursor.execute("SELECT fake FROM settings")
            result = self.cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            print(f"Ошибка в get_fake_values: {e}")
            return 0
    
    def update_fake(self, value):
        """Обновление значения фейк-ставок"""
        try:
            self.cursor.execute("UPDATE settings SET fake = ?", (value,))
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка в update_fake: {e}")
    
    def get_all_KEF(self):
        """Получение всех коэффициентов"""
        try:
            self.cursor.execute("SELECT * FROM kef")
            result = self.cursor.fetchone()
            if result:
                return {
                    'KEF1': result[0], 'KEF2': result[1], 'KEF3': result[2],
                    'KEF4': result[3], 'KEF5': result[4], 'KEF6': result[5],
                    'KEF7': result[6], 'KEF8': result[7], 'KEF9': result[8],
                    'KEF10': result[9], 'KEF11': result[10], 'KEF12': result[11],
                    'KEF13': result[12], 'KEF14': result[13], 'KEF15': result[14],
                    'KEF16': result[15], 'KEF17': result[16]
                }
        except Exception as e:
            print(f"Ошибка в get_all_KEF: {e}")
        
        # Возвращаем значения по умолчанию
        return {
            'KEF1': 2.0, 'KEF2': 6.0, 'KEF3': 2.0, 'KEF4': 4.0, 'KEF5': 2.0,
            'KEF6': 64.0, 'KEF7': 5.0, 'KEF8': 3.0, 'KEF9': 2.0, 'KEF10': 2.0,
            'KEF11': 2.0, 'KEF12': 2.0, 'KEF13': 2.0, 'KEF14': 5.0, 'KEF15': 2.0,
            'KEF16': 2.0, 'KEF17': 14.0
        }
    
    def update_kef(self, column, values):
        """Обновление коэффициента"""
        try:
            self.cursor.execute(f"UPDATE kef SET {column} = ?", (values,))
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка в update_kef: {e}")
    
    def get_cur_KEF(self, column):
        """Получение конкретного коэффициента"""
        try:
            self.cursor.execute(f"SELECT {column} FROM kef")
            result = self.cursor.fetchone()
            return result[0] if result else 50
        except Exception as e:
            print(f"Ошибка в get_cur_KEF: {e}")
            return 50
    
    def update_url(self, column, values):
        """Обновление URL"""
        try:
            self.cursor.execute(f"UPDATE url SET {column} = ?", (values,))
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка в update_url: {e}")
    
    # Добавьте другие методы которые могут отсутствовать
    def db_start(self):
        """Инициализация таблиц"""
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
                    fake INTEGER DEFAULT 0
                )
            ''')
            
            # Таблица коэффициентов
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS kef (
                    KEF1 REAL, KEF2 REAL, KEF3 REAL, KEF4 REAL, KEF5 REAL,
                    KEF6 REAL, KEF7 REAL, KEF8 REAL, KEF9 REAL, KEF10 REAL,
                    KEF11 REAL, KEF12 REAL, KEF13 REAL, KEF14 REAL, KEF15 REAL,
                    KEF16 REAL, KEF17 REAL
                )
            ''')
            
            # Таблица URL
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS url (
                    channals TEXT, checks TEXT, rules TEXT, transfer TEXT,
                    command_game TEXT, info_stavka TEXT, news TEXT
                )
            ''')
            
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка в db_start: {e}")
