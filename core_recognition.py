# core_recognition.py
import cv2
import os
from deepface import DeepFace
from mtcnn import MTCNN
from scipy.spatial.distance import cosine

class FaceRecognizer:
    def __init__(self, db_path="ImagesAttendance", model='VGG-Face'):
        self.model = model
        self.db_path = db_path
        self.detector = MTCNN()
        self.known_encodings = {}
        self.load_known_faces()

    def load_known_faces(self):
        if not os.path.isdir(self.db_path):
            print(f"[WARN] No folder: {self.db_path}")
            return
        loaded = 0
        for class_folder in os.listdir(self.db_path):
            class_path = os.path.join(self.db_path, class_folder)
            if not os.path.isdir(class_path):
                continue
            for img_file in os.listdir(class_path):
                if img_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    path = os.path.join(class_path, img_file)
                    name = os.path.splitext(img_file)[0]
                    img = cv2.imread(path)
                    if img is None:
                        continue
                    h, w = img.shape[:2]
                    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    try:
                        detections = self.detector.detect_faces(rgb)
                        if not detections or detections[0]['confidence'] < 0.9:
                            continue
                        x, y, fw, fh = detections[0]['box']
                        x, y = max(0, x), max(0, y)
                        fw, fh = min(fw, w - x), min(fh, h - y)
                        if fw <= 0 or fh <= 0:
                            continue
                        face = img[y:y+fh, x:x+fw]
                        face = cv2.resize(face, (224, 224))
                        emb = DeepFace.represent(face, model_name=self.model,
                                                enforce_detection=False, detector_backend='skip')[0]['embedding']
                        self.known_encodings[name] = emb
                        loaded += 1
                    except Exception as e:
                        print(f"[ERROR] {name}: {e}")
        print(f"[INFO] Loaded {loaded} known students.")

    def recognize(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        detections = self.detector.detect_faces(rgb)
        results = []
        h, w = frame.shape[:2]
        for d in detections:
            if d['confidence'] < 0.9:
                continue
            x, y, fw, fh = d['box']
            x, y = max(0, x), max(0, y)
            fw, fh = min(fw, w - x), min(fh, h - y)
            if fw <= 0 or fh <= 0:
                continue
            face = rgb[y:y+fh, x:x+fw]
            face = cv2.resize(face, (224, 224))
            try:
                emb = DeepFace.represent(face, model_name=self.model,
                                        enforce_detection=False, detector_backend='skip')[0]['embedding']
                best_name, best_sim = "Unknown", 0.0
                for name, known in self.known_encodings.items():
                    sim = 1 - cosine(emb, known)
                    if sim > best_sim:
                        best_sim, best_name = sim, name
                if best_sim > 0.45:
                    results.append((x, y, fw, fh, best_name, best_sim))
                else:
                    results.append((x, y, fw, fh, "Unknown", best_sim))
            except:
                results.append((x, y, fw, fh, "Error", 0.0))
        return results