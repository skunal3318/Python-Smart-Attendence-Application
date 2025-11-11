# --------------------------------------------------------------
#  SMART ATTENDANCE – LOW LATENCY ( < 100 ms per frame )
# --------------------------------------------------------------
import cv2
import os
import numpy as np
import pandas as pd
from datetime import datetime
from deepface import DeepFace
from mtcnn import MTCNN                     # <-- fast detector
from scipy.spatial.distance import cosine
import warnings
warnings.filterwarnings("ignore")

# ---------------------------
# CONFIG
# ---------------------------
KNOWN_FOLDER   = 'ImagesAttendance'   # known faces (one clear photo per person)
CSV_FILE       = 'Attendance.csv'
RECOG_MODEL    = 'VGG-Face'          # fast & accurate
DETECTOR       = 'mtcnn'             # 'opencv' also works
FRAME_SKIP     = 5                   # recognise only every Nth frame
FACE_SIZE      = 224                 # model input size
CONF_THRESHOLD = 0.60                # cosine similarity threshold (higher = stricter)

# ---------------------------
# 1. Load known faces → embeddings (once)
# ---------------------------
print("[INFO] Loading known faces and computing embeddings...")
known_names = []
known_embeddings = []

detector = MTCNN() if DETECTOR == 'mtcnn' else None

for file in os.listdir(KNOWN_FOLDER):
    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
        path = os.path.join(KNOWN_FOLDER, file)
        img  = cv2.imread(path)
        if img is None:
            continue

        # detect face in known image (single face expected)
        if DETECTOR == 'mtcnn':
            det = detector.detect_faces(img)
            if not det:
                continue
            x, y, w, h = det[0]['box']
            face = img[y:y+h, x:x+w]
        else:   # fallback to DeepFace (slower but safe)
            face = DeepFace.extract_faces(img, detector_backend='retinaface',
                                          enforce_detection=True, grayscale=False)[0]
            fa = face['facial_area']
            face = img[fa['y']:fa['y']+fa['h'], fa['x']:fa['x']+fa['w']]

        face = cv2.resize(face, (FACE_SIZE, FACE_SIZE))
        emb  = DeepFace.represent(face, model_name=RECOG_MODEL,
                                  enforce_detection=False, detector_backend='skip')[0]['embedding']
        known_embeddings.append(emb)
        known_names.append(os.path.splitext(file)[0])

print(f"[INFO] Loaded {len(known_names)} known face(s).")

# ---------------------------
# 2. Attendance helper
# ---------------------------
def markAttendance(name):
    now = datetime.now()
    dateStr = now.strftime('%Y-%m-%d')
    timeStr = now.strftime('%H:%M:%S')
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=['Name','Date','Time']).to_csv(CSV_FILE, index=False)

    df = pd.read_csv(CSV_FILE)
    if not ((df['Name'] == name) & (df['Date'] == dateStr)).any():
        new = pd.DataFrame([{'Name':name, 'Date':dateStr, 'Time':timeStr}])
        df = pd.concat([df, new], ignore_index=True)
        df.to_csv(CSV_FILE, index=False)
        print(f"[MARKED] {name} @ {timeStr}")

# ---------------------------
# 3. Webcam loop (fast)
# ---------------------------
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

frame_counter = 0
print("[INFO] Webcam started – press 'q' to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_counter += 1
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # ---------- 3a. Detect faces (fast) ----------
    faces = []
    if DETECTOR == 'mtcnn':
        detections = detector.detect_faces(rgb)
        for d in detections:
            if d['confidence'] > 0.9:
                x, y, w, h = d['box']
                faces.append((x, y, w, h))
    else:
        # fallback DeepFace (still faster than RetinaFace every frame)
        try:
            dfaces = DeepFace.extract_faces(rgb, detector_backend='opencv',
                                            enforce_detection=False, grayscale=False)
            for f in dfaces:
                fa = f['facial_area']
                faces.append((fa['x'], fa['y'], fa['w'], fa['h']))
        except:
            pass

    # ---------- 3b. Recognise only every FRAME_SKIP ----------
    if frame_counter % FRAME_SKIP == 0 and faces:
        for (x, y, w, h) in faces:
            face_crop = rgb[y:y+h, x:x+w]
            if face_crop.size == 0:
                continue
            face_crop = cv2.resize(face_crop, (FACE_SIZE, FACE_SIZE))

            # get embedding (fast – model already loaded)
            try:
                emb_live = DeepFace.represent(face_crop, model_name=RECOG_MODEL,
                                              enforce_detection=False,
                                              detector_backend='skip')[0]['embedding']
            except:
                continue

            # cosine similarity with all known embeddings
            similarities = [1 - cosine(emb_live, known_emb) for known_emb in known_embeddings]
            max_sim = max(similarities)
            if max_sim >= CONF_THRESHOLD:
                idx = similarities.index(max_sim)
                name = known_names[idx]

                # draw
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
                cv2.putText(frame, f"{name} ({max_sim:.2f})",
                            (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

                markAttendance(name)

    # ---------- 3c. Show ----------
    cv2.imshow('Smart Attendance – Low Latency', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("[INFO] Stopped. Attendance saved to", CSV_FILE)