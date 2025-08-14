from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
import os
import shutil
from auth import AuthSystem
from face_recognition import FaceRecognition


# -------------------- LOGIN --------------------
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth = AuthSystem()
        self.layout = BoxLayout(orientation='vertical', padding=50, spacing=20)

        self.username = TextInput(hint_text='Usuario', multiline=False)
        self.password = TextInput(hint_text='Contraseña', password=True, multiline=False)
        self.login_btn = Button(text='Iniciar Sesión')
        self.register_btn = Button(text='Registrarse')
        self.face_login_btn = Button(text='Iniciar con Reconocimiento Facial')

        self.login_btn.bind(on_press=self.login)
        self.register_btn.bind(on_press=self.go_to_register)
        self.face_login_btn.bind(on_press=self.face_login)

        self.layout.add_widget(Label(text='Inicio de Sesión', font_size=24))
        self.layout.add_widget(self.username)
        self.layout.add_widget(self.password)
        self.layout.add_widget(self.login_btn)
        self.layout.add_widget(self.register_btn)
        self.layout.add_widget(self.face_login_btn)

        self.add_widget(self.layout)

    def login(self, instance):
        user = self.auth.login_user(self.username.text, self.password.text)
        if user:
            main_screen = self.manager.get_screen('main')
            main_screen.current_user = user
            self.manager.current = 'main'
        else:
            self.auth.show_error_popup('Usuario o contraseña incorrectos')

    def face_login(self, instance):
        self.manager.current = 'face_login'

    def go_to_register(self, instance):
        self.manager.current = 'register'


# -------------------- REGISTER SCREEN --------------------
class RegisterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth = AuthSystem()
        self.layout = BoxLayout(orientation='vertical', padding=50, spacing=20)

        self.username = TextInput(hint_text='Usuario', multiline=False)
        self.password = TextInput(hint_text='Contraseña', password=True, multiline=False)
        self.confirm_password = TextInput(hint_text='Confirmar Contraseña', password=True, multiline=False)
        self.register_btn = Button(text='Registrarse')
        self.back_btn = Button(text='Volver al Login')

        self.register_btn.bind(on_press=self.register)
        self.back_btn.bind(on_press=self.go_to_login)

        self.layout.add_widget(Label(text='Registro', font_size=24))
        self.layout.add_widget(self.username)
        self.layout.add_widget(self.password)
        self.layout.add_widget(self.confirm_password)
        self.layout.add_widget(self.register_btn)
        self.layout.add_widget(self.back_btn)

        self.add_widget(self.layout)

    def register(self, instance):
        if self.password.text != self.confirm_password.text:
            self.auth.show_error_popup('Las contraseñas no coinciden')
            return

        if len(self.password.text) < 6:
            self.auth.show_error_popup('La contraseña debe tener al menos 6 caracteres')
            return

        if self.auth.register_user(self.username.text, self.password.text):
            self.manager.current = 'face_enrollment'
        else:
            self.auth.show_error_popup('El usuario ya existe')

    def go_to_login(self, instance):
        self.manager.current = 'login'


# -------------------- FACE Inicio --------------------
class FaceLoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        self.image = Image()
        self.status_label = Label(text='Mire a la cámara para reconocimiento facial')
        self.back_btn = Button(text='Cancelar')

        self.back_btn.bind(on_press=self.go_to_login)

        self.layout.add_widget(self.image)
        self.layout.add_widget(self.status_label)
        self.layout.add_widget(self.back_btn)

        self.add_widget(self.layout)
        self.face_event = None
        self.face_recognition = None

    def on_enter(self):
        try:
            self.face_recognition = FaceRecognition()
            self.face_event = Clock.schedule_interval(self.update, 1.0 / 30.0)
            self.status_label.text = "Cámara iniciada correctamente"
        except Exception as e:
            self.status_label.text = f"Error: {str(e)}"
            if self.face_event:
                self.face_event.cancel()

    def update(self, dt):
        if not self.face_recognition:
            return

        ret, frame = self.face_recognition.capture.read()
        if ret:
            if self.face_recognition.model_loaded:
                face_id = self.face_recognition.detect_faces(frame)
                if face_id is not None:
                    auth = AuthSystem()
                    user = auth.login_with_face(face_id)
                    if user:
                        main_screen = self.manager.get_screen('main')
                        main_screen.current_user = user
                        self.manager.current = 'main'
                        return

            texture = self.face_recognition.frame_to_texture(frame)
            if texture:
                self.image.texture = texture

    def on_leave(self):
        if self.face_event:
            self.face_event.cancel()
        if self.face_recognition:
            self.face_recognition.release_camera()

    def go_to_login(self, instance):
        self.manager.current = 'login'


# -------------------- FACE regis --------------------
class FaceEnrollmentScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth = AuthSystem()
        self.layout = BoxLayout(orientation='vertical', spacing=20, padding=50)

        self.image = Image(size_hint=(1, 0.7))
        self.status_label = Label(text="Posicione su rostro frente a la cámara", size_hint=(1, 0.1))
        self.progress_label = Label(text="Esperando para comenzar...", size_hint=(1, 0.1))
        self.start_btn = Button(text="Comenzar Captura", size_hint=(1, 0.1))
        self.back_btn = Button(text="Cancelar", size_hint=(1, 0.1))

        self.start_btn.bind(on_press=self.start_capture)
        self.back_btn.bind(on_press=self.go_back)

        self.layout.add_widget(self.image)
        self.layout.add_widget(self.status_label)
        self.layout.add_widget(self.progress_label)
        self.layout.add_widget(self.start_btn)
        self.layout.add_widget(self.back_btn)

        self.add_widget(self.layout)

        self.face_recognition = None
        self.capture_event = None
        self.capturing = False
        self.samples_captured = 0
        self.total_samples = 5

    def on_enter(self):
        try:
            self.face_recognition = FaceRecognition()
            self.capture_event = Clock.schedule_interval(self.update_camera, 1.0 / 30.0)
        except Exception as e:
            self.show_error(f"No se pudo iniciar la cámara: {str(e)}")
            self.status_label.text = "Error de cámara"

    def on_leave(self):
        if self.capture_event:
            self.capture_event.cancel()
        if self.face_recognition:
            self.face_recognition.release_camera()

    def update_camera(self, dt):
        ret, frame = self.face_recognition.capture.read()
        if ret:
            texture = self.face_recognition.frame_to_texture(frame)
            if texture:
                self.image.texture = texture

    def start_capture(self, instance):
        if self.capturing:
            return

        username = self.manager.get_screen('register').username.text
        if not username:
            self.show_error("No se ha especificado un nombre de usuario")
            return

        user = self.auth.cursor.execute(
            'SELECT id FROM users WHERE username=?', (username,)
        ).fetchone()

        if not user:
            self.show_error("Usuario no encontrado en la base de datos")
            return

        user_id = user[0]
        self.capturing = True
        self.start_btn.disabled = True
        self.status_label.text = "Capturando muestras de su rostro..."
        self.progress_label.text = f"Progreso: 0/{self.total_samples}"

        Clock.schedule_once(lambda dt: self._capture_samples(user_id))

    def _capture_samples(self, user_id):
        success = self.face_recognition.capture_face_samples(user_id, self.total_samples)
        if success:
            self.progress_label.text = "Entrenando modelo..."
            self.train_model(user_id)
        else:
            self.show_error("No se pudieron capturar suficientes muestras")
            self.reset_capture_state()

    def train_model(self, user_id):
        import subprocess
        result = subprocess.run(['python', 'train_faces.py'], capture_output=True, text=True)
        if result.returncode == 0:
            self.auth.cursor.execute('UPDATE users SET face_id=? WHERE id=?', (user_id, user_id))
            self.auth.conn.commit()

            main_screen = self.manager.get_screen('main')
            user = self.auth.get_user_by_username(self.manager.get_screen('register').username.text)
            main_screen.current_user = user

            self.status_label.text = "¡Registro completado con éxito!"
            self.progress_label.text = "Modelo actualizado correctamente"
            Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'main'), 2.0)
        else:
            self.show_error("Error en entrenamiento")
            self.reset_capture_state()

    def reset_capture_state(self):
        self.capturing = False
        self.start_btn.disabled = False
        self.samples_captured = 0
        self.status_label.text = "Posicione su rostro frente a la cámara"
        self.progress_label.text = "Esperando para comenzar..."

    def show_error(self, message):
        Popup(title='Error', content=Label(text=message), size_hint=(None, None), size=(400, 200)).open()

    def go_back(self, instance):
        self.manager.current = 'register'


# -------------------- MAIN --------------------
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth = AuthSystem()
        self.current_user = None

        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.welcome_label = Label(text='Bienvenido a la aplicación!', font_size=24)
        self.layout.add_widget(self.welcome_label)

        self.user_input = TextInput(hint_text="Usuario destino", multiline=False)
        self.layout.add_widget(self.user_input)

        self.msg_input = TextInput(hint_text="Escribe un mensaje", multiline=False)
        self.layout.add_widget(self.msg_input)

        self.send_btn = Button(text="Enviar mensaje")
        self.send_btn.bind(on_press=self.send_message)
        self.layout.add_widget(self.send_btn)

        self.upload_btn = Button(text="Subir imagen")
        self.upload_btn.bind(on_press=self.upload_file)
        self.layout.add_widget(self.upload_btn)

        self.inbox_btn = Button(text="Ver bandeja de entrada")
        self.inbox_btn.bind(on_press=self.view_inbox)
        self.layout.add_widget(self.inbox_btn)

        self.logout_btn = Button(text="Cerrar sesión", background_color=(1, 0, 0, 1))
        self.logout_btn.bind(on_press=self.logout)
        self.layout.add_widget(self.logout_btn)

        self.add_widget(self.layout)

    def on_enter(self):
        if self.current_user:
            self.welcome_label.text = f"Bienvenido, {self.current_user[1]}!"

    def send_message(self, instance):
        receiver = self.user_input.text.strip()
        message = self.msg_input.text.strip()
        if receiver and message:
            if self.auth.send_message(self.current_user[0], receiver, message):
                Popup(title="Éxito", content=Label(text="Mensaje enviado"), size_hint=(None, None), size=(400, 200)).open()
                self.msg_input.text = ""
            else:
                self.auth.show_error_popup("Usuario destino no encontrado")
        else:
            self.auth.show_error_popup("Debes escribir el usuario y el mensaje")

    def upload_file(self, instance):
        chooser = FileChooserIconView(filters=['*.png', '*.jpg', '*.jpeg'])
        popup = Popup(title="Seleccionar imagen", content=chooser, size_hint=(0.9, 0.9))

        def select_file(instance, selection, touch):  # ← FIX: agregamos touch
            if selection:
                file_path = selection[0]
                receiver = self.user_input.text.strip()
                if receiver:
                    os.makedirs("uploads", exist_ok=True)
                    filename = os.path.basename(file_path)
                    dest_path = os.path.join("uploads", filename)
                    shutil.copy(file_path, dest_path)
                    if self.auth.save_file(self.current_user[0], receiver, dest_path):
                        Popup(title="Éxito", content=Label(text="Imagen enviada"), size_hint=(None, None), size=(400, 200)).open()
                    else:
                        self.auth.show_error_popup("Usuario destino no encontrado")
                else:
                    self.auth.show_error_popup("Debes escribir el usuario destino")
            popup.dismiss()

        chooser.bind(on_submit=select_file)
        popup.open()

    def view_inbox(self, instance):
        messages = self.auth.get_messages_for_user(self.current_user[0])
        files = self.auth.get_files_for_user(self.current_user[0])

        layout = GridLayout(cols=1, spacing=15, padding=[10, 10, 10, 10], size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        layout.add_widget(Label(text="Mensajes:", font_size=20, bold=True, size_hint_y=None, height=40))
        for sender, msg, time in messages:
            lbl = Label(text=f"{time} - {sender}: {msg}", size_hint_y=None, height=40, halign="left", valign="middle")
            lbl.bind(size=lbl.setter('text_size'))
            layout.add_widget(lbl)

        layout.add_widget(Label(text="Imágenes:", font_size=20, bold=True, size_hint_y=None, height=40))
        for sender, path, time in files:
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=80, spacing=10)

            if os.path.exists(path):
                img = Image(source=path, size_hint_x=None, width=80)

                def show_full_image(instance, p=path):
                    popup_img = Image(source=p, allow_stretch=True, keep_ratio=True)
                    popup_layout = BoxLayout(orientation='vertical')
                    popup_layout.add_widget(popup_img)
                    close_btn = Button(text="Cerrar", size_hint_y=None, height=50)
                    popup_layout.add_widget(close_btn)
                    popup = Popup(title=os.path.basename(p), content=popup_layout, size_hint=(0.9, 0.9))
                    close_btn.bind(on_press=popup.dismiss)
                    popup.open()

                img.bind(on_touch_down=lambda inst, touch, p=path: show_full_image(inst, p) if inst.collide_point(*touch.pos) else None)
            else:
                img = Label(text="(No encontrada)", size_hint_x=None, width=80)

            file_label = Label(text=f"{time} - {sender} envió: {os.path.basename(path)}", halign="left", valign="middle")
            file_label.bind(size=file_label.setter('text_size'))

            download_btn = Button(text="Descargar", size_hint_x=None, width=120)

            def download_image(inst, p=path):
                try:
                    os.makedirs("downloads", exist_ok=True)
                    dest = os.path.join("downloads", os.path.basename(p))
                    shutil.copy(p, dest)
                    Popup(title="Descargado", content=Label(text=f"Imagen guardada en {dest}"), size_hint=(None, None), size=(400, 200)).open()
                except Exception as e:
                    Popup(title="Error", content=Label(text=f"No se pudo descargar: {str(e)}"), size_hint=(None, None), size=(400, 200)).open()

            download_btn.bind(on_press=download_image)

            row.add_widget(img)
            row.add_widget(file_label)
            row.add_widget(download_btn)

            layout.add_widget(row)

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(layout)
        Popup(title="Bandeja de entrada", content=scroll, size_hint=(0.9, 0.9)).open()

    def logout(self, instance):
        self.manager.current = 'login'


# -------------------- APP --------------------
class FaceRecognitionApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(RegisterScreen(name='register'))
        sm.add_widget(FaceLoginScreen(name='face_login'))
        sm.add_widget(FaceEnrollmentScreen(name='face_enrollment'))
        sm.add_widget(MainScreen(name='main'))
        return sm


if __name__ == '__main__':
    FaceRecognitionApp().run()
