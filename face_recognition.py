import cv2
import os
import numpy as np
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.label import Label

class FaceRecognition:
    def __init__(self):
        """Inicializa el sistema de reconocimiento facial"""
        self._initialize_directories()
        self._load_face_cascade()
        self._initialize_recognizer()
        self._initialize_camera()
        self.is_training = False

    def _initialize_directories(self):
        """Crea los directorios necesarios si no existen"""
        os.makedirs('models', exist_ok=True)
        os.makedirs('data', exist_ok=True)

    def _load_face_cascade(self):
        """Carga el clasificador de rostros de Haar"""
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if not os.path.exists(cascade_path):
            raise Exception(f"Archivo clasificador no encontrado en: {cascade_path}")
        
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            raise Exception("No se pudo cargar el clasificador de rostros")

    def _initialize_recognizer(self):
        """Inicializa el reconocedor LBPH"""
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.model_path = 'models/recognizer.yml'
        self.model_loaded = False
        
        # Intentar cargar modelo existente
        if os.path.exists(self.model_path) and os.path.getsize(self.model_path) > 0:
            try:
                self.recognizer.read(self.model_path)
                self.model_loaded = True
                print("Modelo cargado exitosamente")
            except Exception as e:
                print(f"Error cargando modelo: {str(e)}")
                self.model_loaded = False

    def _initialize_camera(self):
        """Inicializa la cámara con múltiples intentos"""
        for i in range(3):  # Probar hasta 3 cámaras diferentes
            self.capture = cv2.VideoCapture(i)
            if self.capture.isOpened():
                # Configurar resolución óptima
                self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                return
        raise Exception("No se pudo abrir ninguna cámara disponible")

    def capture_face_samples(self, user_id, samples=20):
        """
        Captura muestras faciales para un usuario específico
        Args:
            user_id: ID del usuario
            samples: Número de muestras a capturar
        Returns:
            bool: True si se capturaron muestras exitosamente
        """
        samples_path = f'data/user_{user_id}'
        os.makedirs(samples_path, exist_ok=True)
        
        count = 0
        while count < samples:
            ret, frame = self.capture.read()
            if not ret:
                print("Error: No se pudo capturar frame de la cámara")
                continue
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) == 0:
                print("Advertencia: No se detectaron rostros en el frame")
                continue
            
            # Tomar solo el primer rostro detectado
            (x, y, w, h) = faces[0]
            
            # Validar región de interés
            if w <= 20 or h <= 20:  # Tamaño mínimo del rostro
                continue
            
            try:
                face_roi = gray[y:y+h, x:x+w]
                
                # Guardar la imagen del rostro
                img_path = os.path.join(samples_path, f"{count}.jpg")
                if not cv2.imwrite(img_path, face_roi):
                    raise Exception(f"No se pudo guardar la imagen {img_path}")
                
                count += 1
                print(f"Muestra {count}/{samples} capturada")
                
                # Mostrar feedback visual
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, f"Muestras: {count}/{samples}", (10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
            except Exception as e:
                print(f"Error procesando rostro: {str(e)}")
                continue
        
        return count > 0  # Retorna True si se capturó al menos una muestra

    def detect_faces(self, frame):
        """
        Detecta y reconoce rostros en un frame
        Args:
            frame: Imagen donde detectar rostros
        Returns:
            int or None: ID del rostro reconocido o None si no se reconoce
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        for (x, y, w, h) in faces:
            roi = gray[y:y+h, x:x+w]
            
            if self.model_loaded:
                try:
                    label, confidence = self.recognizer.predict(roi)
                    if confidence < 85:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        cv2.putText(frame, f'Usuario: {label}', (x, y-10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        return label
                    
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
                    cv2.putText(frame, 'Desconocido', (x, y-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    
                except Exception as e:
                    print(f"Error en reconocimiento: {str(e)}")
                    self.model_loaded = False
            
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
        
        return None

    def frame_to_texture(self, frame):
        """
        Convierte un frame de OpenCV a textura Kivy
        Args:
            frame: Imagen a convertir
        Returns:
            Texture: Textura para mostrar en Kivy
        """
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            buf = cv2.flip(frame_rgb, 0).tobytes()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
            texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
            return texture
        except Exception as e:
            print(f"Error convirtiendo frame a textura: {str(e)}")
            return None

    def release_camera(self):
        """Libera los recursos de la cámara"""
        if hasattr(self, 'capture') and self.capture and self.capture.isOpened():
            self.capture.release()
            print("Cámara liberada correctamente")

    def train_model(self, faces, labels):
        """
        Entrena el modelo con las caras y etiquetas proporcionadas
        Args:
            faces: Lista de imágenes de rostros
            labels: Lista de etiquetas correspondientes
        Returns:
            bool: True si el entrenamiento fue exitoso
        """
        try:
            self.recognizer.train(faces, np.array(labels))
            os.makedirs("models", exist_ok=True)
            self.recognizer.save(self.model_path)
            self.model_loaded = True
            print(f"Modelo entrenado y guardado en {self.model_path}")
            return True
        except Exception as e:
            print(f"Error entrenando modelo: {str(e)}")
            return False