from ultralytics import YOLO
import cv2
import numpy as np
import os

# --- INCARCARE MODEL NEURONAL ---
# Calculam calea catre models/vision/best.pt relative la acest fisier
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "vision", "best.pt")

print(f"[VISION] Incarc modelul YOLO din: {MODEL_PATH}")

try:
    # Initializam reteaua neuronala YOLOv8
    model = YOLO(MODEL_PATH)
except Exception as e:
    print(f"[EROARE CRITICA] Nu gasesc fisierul 'best.pt'! {e}")
    model = None


def process_camera(img_raw, res):
    """
    Transforma imaginea bruta (bytes) primita de la CoppeliaSim
    intr-un format pe care OpenCV il poate intelege (Matrice Numpy).
    """
    # Convertim sirul de bytes in numere intregi
    img_np = np.frombuffer(img_raw, dtype=np.uint8)

    # Reconstruim forma imaginii (Inaltime, Latime, 3 canale de culoare RGB)
    img_np = img_np.reshape((res[1], res[0], 3))

    # CoppeliaSim trimite imaginea rasturnata, asa ca o rotim (Flip Vertical)
    img = cv2.flip(img_np, 0)

    # Convertim culorile din RGB (Coppelia) in BGR (Standardul OpenCV)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    return img


def detect_objects(img):
    """
    Trimite imaginea catre YOLO si returneaza lista de obiecte gasite.
    """
    if model is None:
        return []  # Daca modelul nu e incarcat, nu returnam nimic

    # Executam predictia (Incredere minima 0.5 = 50%)
    results = model.predict(img, conf=0.5, verbose=False)

    detected_objects = []

    # Iteram prin rezultatele detectiei
    for r in results:
        boxes = r.boxes

        for box in boxes:
            # Extragem coordonatele cutiei (x1, y1, x2, y2)
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

            # Extragem ID-ul clasei si numele (ex: 'scaun')
            cls_id = int(box.cls[0])
            cls_name = model.names[cls_id]

            # Extragem scorul de incredere (ex: 0.85)
            conf = float(box.conf[0])

            # Calculam dimensiunile cutiei
            x, y = int(x1), int(y1)
            w, h = int(x2 - x1), int(y2 - y1)

            # Calculam centrul cutiei (pentru a sti unde e obiectul fata de robot)
            center_x = x + w // 2
            center_y = y + h // 2

            # Construim dictionarul cu informatiile obiectului
            obj_info = {
                'name': cls_name,
                'conf': conf,
                'box': (x, y, w, h),
                'center': (center_x, center_y),
                'area': w * h  # Aria ne ajuta sa estimam distanta (mai mare = mai aproape)
            }
            detected_objects.append(obj_info)

            # --- DESENARE (Debug) ---
            # Desenam un dreptunghi verde in jurul obiectului pe imagine
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # Scriem numele si scorul deasupra cutiei
            cv2.putText(img, f"{cls_name} {conf:.2f}", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return detected_objects