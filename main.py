from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from auth import AuthSystem
from face_recognition import FaceRecognition

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
            self.manager.current = 'main'
        else:
            self.auth.show_error_popup('Usuario o contraseña incorrectos')
    
    def face_login(self, instance):
        self.manager.current = 'face_login'
    
    def go_to_register(self, instance):
        self.manager.current = 'register'

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
        """Se ejecuta cuando se muestra la pantalla"""
        try:
            self.face_recognition = FaceRecognition()
            self.face_event = Clock.schedule_interval(self.update, 1.0/30.0)
            self.status_label.text = "Cámara iniciada correctamente"
        except Exception as e:
            self.status_label.text = f"Error: {str(e)}"
            if hasattr(self, 'face_event') and self.face_event:
                self.face_event.cancel()
    
    def update(self, dt):
        """Actualiza la vista de la cámara"""
        if not hasattr(self, 'face_recognition') or not self.face_recognition:
            return
            
        ret, frame = self.face_recognition.capture.read()
        if ret:
            # Solo intentar reconocimiento si hay modelo cargado
            if self.face_recognition.model_loaded:
                face_id = self.face_recognition.detect_faces(frame)
                if face_id is not None:
                    auth = AuthSystem()
                    user = auth.login_with_face(face_id)
                    if user:
                        self.manager.current = 'main'
                        return
            
            # Mostrar la imagen de la cámara
            texture = self.face_recognition.frame_to_texture(frame)
            if texture:
                self.image.texture = texture
    
    def on_leave(self):
        """Se ejecuta cuando se abandona la pantalla"""
        if self.face_event:
            self.face_event.cancel()
        if hasattr(self, 'face_recognition') and self.face_recognition:
            self.face_recognition.release_camera()
    
    def go_to_login(self, instance):
        """Regresa a la pantalla de login"""
        self.manager.current = 'login'

class FaceEnrollmentScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth = AuthSystem()  # Inicializar el sistema de autenticación
        self.layout = BoxLayout(orientation='vertical', spacing=20, padding=50)
        
        # Componentes de la UI
        self.image = Image(size_hint=(1, 0.7))
        self.status_label = Label(text="Posicione su rostro frente a la cámara", 
                               size_hint=(1, 0.1),
                               halign='center')
        self.progress_label = Label(text="Esperando para comenzar...",
                                 size_hint=(1, 0.1))
        self.start_btn = Button(text="Comenzar Captura",
                              size_hint=(1, 0.1))
        self.back_btn = Button(text="Cancelar",
                             size_hint=(1, 0.1))
        
        # Configuración de eventos
        self.start_btn.bind(on_press=self.start_capture)
        self.back_btn.bind(on_press=self.go_back)
        
        # Agregar componentes al layout
        self.layout.add_widget(self.image)
        self.layout.add_widget(self.status_label)
        self.layout.add_widget(self.progress_label)
        self.layout.add_widget(self.start_btn)
        self.layout.add_widget(self.back_btn)
        
        self.add_widget(self.layout)
        
        # Variables de estado
        self.face_recognition = None
        self.capture_event = None
        self.capturing = False
        self.samples_captured = 0
        self.total_samples = 5

    def on_enter(self):
        """Se ejecuta cuando se muestra esta pantalla"""
        try:
            self.face_recognition = FaceRecognition()
            self.capture_event = Clock.schedule_interval(self.update_camera, 1.0/30.0)
        except Exception as e:
            self.show_error(f"No se pudo iniciar la cámara: {str(e)}")
            self.status_label.text = "Error de cámara"

    def on_leave(self):
        """Se ejecuta cuando se abandona esta pantalla"""
        if self.capture_event:
            self.capture_event.cancel()
        if hasattr(self, 'face_recognition') and self.face_recognition:
            self.face_recognition.release_camera()

    def update_camera(self, dt):
        """Actualiza la vista previa de la cámara"""
        if not hasattr(self, 'face_recognition') or not self.face_recognition:
            return
            
        ret, frame = self.face_recognition.capture.read()
        if ret:
            texture = self.face_recognition.frame_to_texture(frame)
            if texture:
                self.image.texture = texture

    def start_capture(self, instance):
        """Inicia el proceso de captura de muestras faciales"""
        if self.capturing:
            return
            
        username = self.manager.get_screen('register').username.text
        if not username:
            self.show_error("No se ha especificado un nombre de usuario")
            return
            
        # Obtener el ID del usuario desde la base de datos
        user = self.auth.cursor.execute(
            'SELECT id FROM users WHERE username=?', (username,)
        ).fetchone()
        
        if not user:
            self.show_error("Usuario no encontrado en la base de datos")
            return
            
        user_id = user[0]
        
        # Cambiar el estado a "capturando"
        self.capturing = True
        self.start_btn.disabled = True
        self.status_label.text = "Capturando muestras de su rostro..."
        self.progress_label.text = f"Progreso: 0/{self.total_samples}"
        
        # Usar un hilo separado para la captura
        Clock.schedule_once(lambda dt: self._capture_samples(user_id))

    def _capture_samples(self, user_id):
        """Método que maneja la captura de muestras en segundo plano"""
        try:
            success = self.face_recognition.capture_face_samples(
                user_id, self.total_samples)
            
            if success:
                self.progress_label.text = "Entrenando modelo..."
                self.train_model(user_id)
            else:
                self.show_error("No se pudieron capturar suficientes muestras")
                self.reset_capture_state()
                
        except Exception as e:
            self.show_error(f"Error durante la captura: {str(e)}")
            self.reset_capture_state()

    def train_model(self, user_id):
        """Entrena el modelo con las nuevas muestras"""
        try:
            # Ejecutar el entrenamiento en un hilo separado
            from threading import Thread
            def train_thread():
                try:
                    import subprocess
                    result = subprocess.run(
                        ['python', 'train_faces.py'],
                        capture_output=True,
                        text=True
                    )
                    
                    # Actualizar UI en el hilo principal
                    Clock.schedule_once(
                        lambda dt: self._handle_train_result(result, user_id))
                except Exception as e:
                    Clock.schedule_once(
                        lambda dt: self.show_error(f"Error en entrenamiento: {str(e)}"))
            
            Thread(target=train_thread, daemon=True).start()
            
        except Exception as e:
            self.show_error(f"Error iniciando entrenamiento: {str(e)}")
            self.reset_capture_state()

    def _handle_train_result(self, result, user_id):
        """Maneja el resultado del entrenamiento"""
        if result.returncode == 0:
            # Actualizar la base de datos
            self.auth.cursor.execute(
                'UPDATE users SET face_id=? WHERE id=?', 
                (user_id, user_id))
            self.auth.conn.commit()
            
            self.status_label.text = "¡Registro completado con éxito!"
            self.progress_label.text = "Modelo actualizado correctamente"
            
            # Volver a la pantalla principal después de 2 segundos
            Clock.schedule_once(
                lambda dt: setattr(self.manager, 'current', 'main'), 
                2.0)
        else:
            error_msg = result.stderr or "Error desconocido durante el entrenamiento"
            self.show_error(f"Error en entrenamiento: {error_msg}")
            self.reset_capture_state()

    def reset_capture_state(self):
        """Restablece el estado de captura"""
        self.capturing = False
        self.start_btn.disabled = False
        self.samples_captured = 0
        self.status_label.text = "Posicione su rostro frente a la cámara"
        self.progress_label.text = "Esperando para comenzar..."

    def show_error(self, message):
        """Muestra un mensaje de error en un popup"""
        popup = Popup(title='Error',
                     content=Label(text=message),
                     size_hint=(None, None), 
                     size=(400, 200))
        popup.open()

    def go_back(self, instance):
        """Regresa a la pantalla anterior"""
        self.manager.current = 'register'

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        self.layout.add_widget(Label(text='Bienvenido a la aplicación!'))
        self.add_widget(self.layout)

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