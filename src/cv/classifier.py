import time
import cv2
import os
import psutil
import threading
import queue
import json
from collections import deque
from dotenv import load_dotenv
from websocket import create_connection

load_dotenv()

# -------- CONFIG --------
DETECT_EVERY_N_FRAMES = 5
HISTORY_SIZE = 5
CPU_CORES = os.cpu_count() or 1

DOCKER_WS_URL = os.getenv("CV_URL", "ws://localhost:8000/ws/inference")

current_mode = "Working" 

latest_result = {
    "found": False,
    "label": "",
    "confidence": 0.0
}

result_lock = threading.Lock()
frame_queue = queue.Queue(maxsize=1)
running = True

label_detection_history = deque(maxlen=HISTORY_SIZE)
status_detection_history = deque(maxlen=HISTORY_SIZE)

working_labels = {"sitting", "using_laptop", "writing", "reading", "start_pomodoro", "stop_pomodoro"}

def determine_final_status(history):
    if not history: return "Working"
    
    # Simple majority voting atau thresholding
    distracted_count = sum(1 for status in history if status['label'] not in working_labels)
    threshold = len(history) - 1

    if distracted_count >= threshold:
        return "Distracted"
    return "Working"

def inference_worker():
    global latest_result, label_detection_history, status_detection_history
    
    ws = None
    
    def connect_ws():
        try:
            conn = create_connection(DOCKER_WS_URL)
            return conn
        except Exception as e:
            print(f"Failed to connect to Docker: {e}")
            return None

    while running:
        try:
            frame_data = frame_queue.get(timeout=0.1)
            frame_rgb = frame_data['img']
            
            if ws is None or not ws.connected:
                ws = connect_ws()
                if ws is None:
                    frame_queue.task_done()
                    time.sleep(1) 
                    continue

            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            _, buffer = cv2.imencode('.jpg', frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            frame_bytes = buffer.tobytes()

            ws.send_binary(frame_bytes)

            result_str = ws.recv()
            result_json = json.loads(result_str)
            
            with result_lock:
                latest_result['found'] = result_json['found']
                latest_result['label'] = result_json['label']
                latest_result['confidence'] = result_json['confidence']

            if result_json['found']:
                print(f"Docker Detected: {result_json['label']} ({result_json['confidence']:.2f})")
                label_detection_history.append({
                    "label": result_json['label'], 
                    "confidence": result_json['confidence']
                })
                
                new_status = determine_final_status(label_detection_history)
                status_detection_history.append(new_status)
            else:
                pass

            frame_queue.task_done()

        except queue.Empty:
            continue
        except Exception as e:
            print(f"Error in inference worker (WS): {e}")
            if ws:
                try: ws.close() 
                except: pass
            ws = None

class BotClassifier():
    def __init__(self, cap):
        self.prev_time = time.time()
        self.frame_count = 0
        self.cap = cap
        self.pid = os.getpid()
        self.process = psutil.Process(self.pid)

    def classifier_loop(self):
        ret, frame = self.cap.read()
        if not ret: return "Error", latest_result
        
        self.frame_count += 1
        frame_h, frame_w = frame.shape[:2]
        
        # Kirim frame ke thread worker setiap N frame
        if self.frame_count % DETECT_EVERY_N_FRAMES == 0:
            self.frame_count = 0
            
            if frame_queue.empty():
                # Convert BGR (OpenCV) ke RGB
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

            # print(f"FPS: {fps:.1f} | CPU: {cpu_usage}% | RAM: {ram_usage_mb:.1f} MB")
            # -------------

        if not status_detection_history:
            return "Working", latest_result

        distracted_count = sum(1 for status in status_detection_history if status == "Distracted")
        threshold = len(status_detection_history) - 1
        if distracted_count >= threshold:
            return "Distracted", latest_result
        return "Working", latest_result