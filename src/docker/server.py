import cv2
import torch
import numpy as np
from fastapi import FastAPI, WebSocket
from ultralytics import YOLO
from torchvision import transforms
import torch.nn.functional as F
from PIL import Image
import os
import sys

sys.path.append("/app/external")

try:
    from mobilenet_model import ModelHAR
except ImportError:
    print("Warning: ModelHAR definition not found. Check volume mapping.")
    class ModelHAR: pass 

app = FastAPI()

# -------- CONFIG & LOAD MODEL --------
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
YOLO_WEIGHTS = "/app/external/model/yolo11n.pt"
MODEL_WEIGHTS = "/app/external/model/densenet_har.pth"
LABEL_PATH = "/app/external/model/class_names.pth"

CONF_THRESH = 0.25
IMG_SIZE = 224
YOLO_IMGSZ = 224

print(f"Server starting on {DEVICE}...")

# 1. Load YOLO
try:
    yolo = YOLO(YOLO_WEIGHTS)
except Exception as e:
    print(f"YOLO load error: {e}. Downloading default...")
    yolo = YOLO("yolo11n.pt")

# 2. Load Labels
if os.path.exists(LABEL_PATH):
    class_names = torch.load(LABEL_PATH)
    print(f"Loaded classes: {class_names}")
else:
    class_names = ["Unknown"]

num_classes = len(class_names)
hidden1 = 512
hidden2 = 256
dropout_rate = 0.3

# 3. Load HAR Model
har_model = None
try:
    har_model = ModelHAR(
        num_classes=num_classes,
        hidden1=hidden1,
        hidden2=hidden2,
        dropout_rate=dropout_rate
        )
    if os.path.exists(MODEL_WEIGHTS):
        state_dict = torch.load(MODEL_WEIGHTS, map_location=DEVICE)
        har_model.load_state_dict(state_dict)
        print("HAR Model loaded.")
    har_model.to(DEVICE)
    har_model.eval()
except Exception as e:
    print(f"Error loading HAR Model: {e}")

# 4. Transforms
to_tensor = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

@app.websocket("/ws/inference")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected.")
    
    try:
        while True:
            data = await websocket.receive_bytes()
            
            nparr = np.frombuffer(data, np.uint8)
            frame_rgb = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2RGB)
            
            frame_h, frame_w = frame_rgb.shape[:2]
            
            response = {
                "found": False,
                "label": "Unknown",
                "confidence": 0.0
            }

            # A. Deteksi YOLO
            results = yolo(frame_rgb, imgsz=YOLO_IMGSZ, conf=CONF_THRESH, classes=[0], verbose=False)
            best_box = None
            max_area = 0
            
            if results:
                for r in results:
                    for box in r.boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        area = (x2 - x1) * (y2 - y1)
                        if area > max_area:
                            max_area = area
                            best_box = [int(x1), int(y1), int(x2), int(y2)]

            # B. Klasifikasi
            if best_box is not None and har_model is not None:
                x1, y1, x2, y2 = best_box
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(frame_w, x2), min(frame_h, y2)
                
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
                    
                    response["found"] = True
                    response["label"] = raw_label
                    response["confidence"] = top_conf

            # Kirim hasil balik ke client
            await websocket.send_json(response)

    except Exception as e:
        print(f"Connection closed/error: {e}")