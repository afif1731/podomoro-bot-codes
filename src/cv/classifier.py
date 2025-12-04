import cv2
import torch
from ultralytics import YOLO
import os

from mobilenet_model import MobileNetHAR

# -------- CONFIG --------
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

YOLO_WEIGHTS = "../../model/yolo11n.pt"
MODEL_WEIGHTS = "../../model/mobilenet_lstm_har.pth"
LABEL_PATH = "../../model/class_names.pth"

CONF_THRESH = 0.25
LABEL_CONF_THRESH = 0.6
IMG_SIZE = 224
YOLO_IMGSZ = 320

FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.6
THICKNESS = 2
CPU_CORES = os.cpu_count() or 1

DETECT_EVERY_N_FRAMES = 5 # Lakukan deteksi setiap N frame (untuk performa)
HISTORY_SIZE = 5          # Smoothing hasil prediksi

# Mode kerja
current_mode = "Working"
# Sesuaikan himpunan ini dengan nama kelas yang ada di dataset Anda
working_labels = {"calling", "listening_music", "sitting", "using_laptop"}

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

# ------------------------

# Logic Here
