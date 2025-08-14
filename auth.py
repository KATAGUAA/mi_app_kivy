import sqlite3
from hashlib import sha256
from kivy.uix.popup import Popup
from kivy.uix.label import Label
import os

class AuthSystem:
    def __init__(self):
        self.conn = sqlite3.connect('models/users.db')
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        # Tabla de usuarios
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                face_id INTEGER
            )
        ''')
        # Tabla de mensajes
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER,
                receiver_id INTEGER,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Tabla de archivos (solo imágenes en este caso)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER,
                receiver_id INTEGER,
                file_path TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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

    def get_user_by_username(self, username):
        self.cursor.execute('SELECT * FROM users WHERE username=?', (username,))
        return self.cursor.fetchone()

    def get_all_users(self):
        self.cursor.execute('SELECT username FROM users')
        return [row[0] for row in self.cursor.fetchall()]

    def send_message(self, sender_id, receiver_username, message):
        receiver = self.get_user_by_username(receiver_username)
        if not receiver:
            return False
        receiver_id = receiver[0]
        self.cursor.execute(
            'INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)',
            (sender_id, receiver_id, message)
        )
        self.conn.commit()
        return True

    def get_messages_for_user(self, user_id):
        self.cursor.execute('''
            SELECT users.username, messages.message, messages.timestamp
            FROM messages
            JOIN users ON users.id = messages.sender_id
            WHERE receiver_id=?
            ORDER BY messages.timestamp DESC
        ''', (user_id,))
        return self.cursor.fetchall()

    def save_file(self, sender_id, receiver_username, file_path):
        # Verificar que sea imagen
        if not file_path.lower().endswith((".jpg", ".jpeg", ".png")):
            return False

        receiver = self.get_user_by_username(receiver_username)
        if not receiver:
            return False

        # Guardar ruta relativa
        receiver_id = receiver[0]
        relative_path = os.path.relpath(file_path, start=os.getcwd())
        self.cursor.execute(
            'INSERT INTO files (sender_id, receiver_id, file_path) VALUES (?, ?, ?)',
            (sender_id, receiver_id, relative_path)
        )
        self.conn.commit()
        return True

    def get_files_for_user(self, user_id):
        self.cursor.execute('''
            SELECT users.username, files.file_path, files.timestamp
            FROM files
            JOIN users ON users.id = files.sender_id
            WHERE receiver_id=?
            ORDER BY files.timestamp DESC
        ''', (user_id,))
        return self.cursor.fetchall()

    def show_error_popup(self, message):
        popup = Popup(title='Error',
                     content=Label(text=message),
                     size_hint=(None, None), size=(400, 200))
        popup.open()

    def __del__(self):
        self.conn.close()
