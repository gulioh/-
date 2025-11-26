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
