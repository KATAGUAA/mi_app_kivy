import sqlite3
from hashlib import sha256
from kivy.uix.popup import Popup
from kivy.uix.label import Label

class AuthSystem:
    def __init__(self):
        self.conn = sqlite3.connect('models/users.db')
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                face_id INTEGER
            )
        ''')
        self.conn.commit()

    def register_user(self, username, password, face_id=None):
        try:
            hashed_password = sha256(password.encode()).hexdigest()
            self.cursor.execute(
                'INSERT INTO users (username, password, face_id) VALUES (?, ?, ?)',
                (username, hashed_password, face_id)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def login_user(self, username, password):
        hashed_password = sha256(password.encode()).hexdigest()
        self.cursor.execute(
            'SELECT * FROM users WHERE username=? AND password=?',
            (username, hashed_password)
        )
        return self.cursor.fetchone()

    def login_with_face(self, face_id):
        self.cursor.execute(
            'SELECT * FROM users WHERE face_id=?',
            (face_id,)
        )
        return self.cursor.fetchone()

    def show_error_popup(self, message):
        popup = Popup(title='Error',
                     content=Label(text=message),
                     size_hint=(None, None), size=(400, 200))
        popup.open()

    def __del__(self):
        self.conn.close()