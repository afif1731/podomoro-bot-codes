import time
import cv2
import torch
import numpy as np
from pathlib import Path
from ultralytics import YOLO
from torchvision import transforms
import torch.nn.functional as F
from PIL import Image
import os
import psutil
import threading
import queue
from collections import deque

from mobilenet_model import MobileNetHAR
from classifier_helper import determine_final_status

# -------- CONFIG --------
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

YOLO_WEIGHTS = "../../model/yolo11n.pt"
MODEL_WEIGHTS = "../../model/mobilenet_lstm_har.pth"
LABEL_PATH = "../../model/class_names.pth"

CONF_THRESH = 0.25
LABEL_CONF_THRESH = 0.6
IMG_SIZE = 224
YOLO_IMGSZ = 224

DETECT_EVERY_N_FRAMES = 5
HISTORY_SIZE = 5
CPU_CORES = os.cpu_count() or 1

# Mode kerja
current_mode = "Working" 

# Shared Variables untuk Threading
latest_result = {
    "found": False,
    "label": "",
    "confidence": 0.0
}

result_lock = threading.Lock()
frame_queue = queue.Queue(maxsize=1)
running = True

label_detection_history = deque(maxlen=HISTORY_SIZE) # deque detected label
status_detection_history = deque(maxlen=HISTORY_SIZE) # deque detected status (working / distracted)

print(f"Loading models on {DEVICE}...")

# Load YOLO
try:
    yolo = YOLO(YOLO_WEIGHTS)
except Exception as e:
    print(f"Error loading YOLO: {e}. Downloading default yolo11n.pt...")
    yolo = YOLO("yolo11n.pt")

# Load Label Encoder (List of Strings)
if os.path.exists(LABEL_PATH):
    class_names = torch.load(LABEL_PATH)
    print(f"Loaded {len(class_names)} classes: {class_names}")
else:
    print(f"⚠️ Label file not found at {LABEL_PATH}! Creating dummy classes.")
    class_names = ["Unknown"] # Fallback

num_classes = len(class_names)

# Load Classification Model
har_model = MobileNetHAR(num_classes=num_classes)

if os.path.exists(MODEL_WEIGHTS):
    state_dict = torch.load(MODEL_WEIGHTS, map_location=DEVICE)
    har_model.load_state_dict(state_dict)
    print("HAR Model weights loaded successfully.")
else:
    print(f"⚠️ Model weights not found at {MODEL_WEIGHTS}!")

har_model.to(DEVICE)
har_model.eval()

to_tensor = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# ------------------------

# Logic Here

def inference_worker():
    global latest_result, label_detection_history, status_detection_history
    
    while running:
        try:
            frame_data = frame_queue.get(timeout=0.1) 

            frame_rgb = frame_data['img']
            frame_h, frame_w = frame_data['size']

            # --- A. DETEKSI OBJEK (YOLO) ---
            # Cari hanya class 0 (person)
            results = yolo(frame_rgb, imgsz=YOLO_IMGSZ, conf=CONF_THRESH, classes=[0], verbose=False)
            
            found_person = False
            best_box = None
            max_area = 0
            
            if results:
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        area = (x2 - x1) * (y2 - y1)
                        
                        if area > max_area:
                            max_area = area
                            best_box = [int(x1), int(y1), int(x2), int(y2)]

            if best_box is not None:
                x1, y1, x2, y2 = best_box
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(frame_w, x2), min(frame_h, y2)
                found_person = True

            # --- B. KLASIFIKASI AKTIVITAS ---
            if found_person:
                crop = frame_rgb[y1:y2, x1:x2]
                
                if crop.size > 0 and crop.shape[0] > 10 and crop.shape[1] > 10:
                    pil_crop = Image.fromarray(crop)
                    
                    inp = to_tensor(pil_crop).unsqueeze(0).to(DEVICE)

                    with torch.no_grad():
                        output = har_model(inp)
                        probs = F.softmax(output, dim=1).cpu().numpy()[0]
                        top_idx = int(np.argmax(probs))
                        top_conf = float(probs[top_idx])

                    raw_label = class_names[top_idx] if top_idx < len(class_names) else "Unknown"
                    display_label = raw_label

                    print(f"Frame detected. Label: {raw_label}, Confidence: {top_conf}.")

                    label_detection_history.append({"label" : display_label, "confidence" : top_conf})

                    new_status = determine_final_status(label_detection_history)

                    status_detection_history.append(new_status)

                    with result_lock:
                        latest_result['found'] = True
                        latest_result['label'] = display_label
                        latest_result['confidence'] = top_conf
                else:
                    with result_lock: latest_result['found'] = False

            else:
                with result_lock:
                    latest_result['found'] = False

            frame_queue.task_done()

        except queue.Empty:
            continue
        except Exception as e:
            print(f"Error in worker thread: {e}")

class BotClassifier():
    def __init__(self, cap):
        self.prev_time = time.time()
        self.frame_count = 0
        self.cap = cap
        self.pid = os.getpid()
        self.process = psutil.Process(self.pid)

    def classifier_loop(self):
        ret, frame = self.cap.read()
        if not ret: return
        
        frame_count += 1
        frame_h, frame_w = frame.shape[:2]
        
        # Kirim frame ke thread worker setiap N frame
        if frame_count % DETECT_EVERY_N_FRAMES == 0:
            frame_count = 0
            
            if frame_queue.empty():
                # Convert BGR (OpenCV) ke RGB (untuk Model & PIL)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                frame_data = {
                    'img': rgb_frame,
                    'size': (frame_h, frame_w),
                    'mode': current_mode
                }
                frame_queue.put(frame_data)
            
            # --- Debug ---
            cur_time = time.time()
            fps = 1.0 / (cur_time - self.prev_time) if (cur_time - self.prev_time) > 0 else 0.0
            self.prev_time = cur_time

            cpu_usage = self.process.cpu_percent(interval=None)
            ram_usage_mb = self.process.memory_info().rss / (1024 * 1024)

            print(f"FPS: {fps} | CPU: {cpu_usage} %, AVG: {cpu_usage / CPU_CORES} % | RAM: {ram_usage_mb} MB")
            # -------------

        if not status_detection_history:
            return "Working", latest_result

        distracted_count = sum(1 for status in status_detection_history if status == "Distracted")
        threshold = len(status_detection_history) - 1
        if distracted_count >= threshold:
            return "Distracted", latest_result
        return "Working", latest_result
