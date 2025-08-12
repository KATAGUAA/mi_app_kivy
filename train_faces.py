import os
import cv2
import numpy as np
import sqlite3

def train_model():
    print("Iniciando entrenamiento del modelo...")
    
    faces = []
    labels = []
    label_map = {}
    
    try:
        conn = sqlite3.connect('models/users.db')
        cursor = conn.cursor()
        
        # Obtener usuarios registrados
        cursor.execute('SELECT id FROM users')
        user_ids = [row[0] for row in cursor.fetchall()]
        
        for user_id in user_ids:
            user_dir = f'data/user_{user_id}'
            if not os.path.exists(user_dir):
                continue
                
            for img_name in os.listdir(user_dir):
                img_path = os.path.join(user_dir, img_name)
                try:
                    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                    if img is not None:
                        faces.append(img)
                        labels.append(user_id)
                        print(f"Procesada: {img_path}")
                except Exception as e:
                    print(f"Error procesando {img_path}: {str(e)}")
        
        if len(faces) == 0:
            print("Error: No se encontraron imágenes para entrenar")
            return False
        
        # Entrenar el modelo
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.train(faces, np.array(labels))
        
        # Guardar el modelo
        os.makedirs("models", exist_ok=True)
        recognizer.save("models/recognizer.yml")
        
        print(f"Modelo entrenado con {len(faces)} imágenes de {len(set(labels))} usuarios")
        return True
        
    except Exception as e:
        print(f"Error durante el entrenamiento: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    train_model()