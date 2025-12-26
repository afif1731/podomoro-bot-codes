import time
import cv2
import os
import psutil
import threading
import queue
import json
from datetime import datetime
from collections import deque
from dotenv import load_dotenv
from websocket import create_connection, WebSocketTimeoutException

load_dotenv()

# -------- CONFIG --------
DETECT_EVERY_N_FRAMES = 5
HISTORY_SIZE = 5
CPU_CORES = os.cpu_count() or 1
LOG_FILE_PATH = "/home/raspberry/podomoro-bot-codes/cvlog.log"

WS_TIMEOUT = 2.0 

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
    
    distracted_count = sum(1 for status in history if status['label'] not in working_labels)
    threshold = len(history) - 1

    if distracted_count >= threshold:
        return "Distracted"
    return "Working"

def tulis_log(pesan):
    """
    Menulis pesan ke file log dengan flush paksa agar tertulis saat sudo.
    """
    try:
        sekarang = datetime.now()
        timestamp = sekarang.strftime("[%H:%M:%S %d-%m-%Y]")
        log_msg = f"{timestamp} {pesan}\n"
        
        # Mode 'a' append
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as file:
            file.write(log_msg)
            file.flush()     # Paksa write buffer internal Python ke OS
            os.fsync(file.fileno()) # Paksa OS menulis ke Disk fisik
            
    except Exception as e:
        print(f"Gagal menulis log: {e}")

def inference_worker():
    global latest_result, label_detection_history, status_detection_history
    
    ws = None
    
    def connect_ws():
        try:
            # Set timeout saat connect juga
            conn = create_connection(DOCKER_WS_URL, timeout=WS_TIMEOUT)
            print("websocket connected!")
            tulis_log("websocket connected!")
            return conn
        except Exception as e:
            # Jangan spam log jika gagal connect terus menerus
            print(f"Failed to connect to Docker: {e}")
            return None

    while running:
        try:
            # 1. Ambil frame dari queue
            frame_data = frame_queue.get(timeout=0.1)
            frame_rgb = frame_data['img']
            
            # 2. Cek koneksi WS
            if ws is None or not ws.connected:
                ws = connect_ws()
                if ws is None:
                    frame_queue.task_done()
                    time.sleep(1) 
                    continue

            # 3. Encode gambar
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            _, buffer = cv2.imencode('.jpg', frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            frame_bytes = buffer.tobytes()

            # 4. Kirim dan Terima (Critical Section)
            try:
                ws.send_binary(frame_bytes)
                
                # RECV SEKARANG AMAN KARENA ADA TIMEOUT
                result_str = ws.recv() 
                
                result_json = json.loads(result_str)

                # print(f"cv result: {result_str}")
                # tulis_log(f"cv result: {result_str}") # Opsional: matikan agar log tidak penuh
                
                with result_lock:
                    latest_result['found'] = result_json['found']
                    latest_result['label'] = result_json['label']
                    latest_result['confidence'] = result_json['confidence']

                if result_json['found']:
                    print(f"Docker Detected: {result_json['label']} ({result_json['confidence']:.2f})")
                    tulis_log(f"Docker Detected: {result_json['label']} ({result_json['confidence']:.2f})")
                    label_detection_history.append({
                        "label": result_json['label'], 
                        "confidence": result_json['confidence']
                    })
                    
                    new_status = determine_final_status(label_detection_history)
                    status_detection_history.append(new_status)

            except (TimeoutError, WebSocketTimeoutException):
                print("WebSocket Timeout - Docker lambat merespon")
                tulis_log("WebSocket Timeout")
                # Close socket agar reconnect di loop berikutnya
                try: ws.close()
                except: pass
                ws = None
                
            except Exception as e:
                print(f"Error during WS send/recv: {e}")
                tulis_log(f"Error during WS send/recv: {e}")
                try: ws.close()
                except: pass
                ws = None

            frame_queue.task_done()

        except queue.Empty:
            continue
        except Exception as e:
            print(f"Critical Error in inference worker: {e}")
            tulis_log(f"Critical Error in inference worker: {e}")
            time.sleep(1) # Sleep agar tidak cpu spike jika error loop

class BotClassifier():
    def __init__(self, cap):
        self.prev_time = time.time()
        self.frame_count = 0
        self.cap = cap
        self.pid = os.getpid()
        self.process = psutil.Process(self.pid)

    def classifier_loop(self):
        global status_detection_history, latest_result, frame_queue
        
        ret, frame = self.cap.read()
        if not ret: return "Error", latest_result
        
        self.frame_count += 1
        frame_h, frame_w = frame.shape[:2]
        
        if self.frame_count % DETECT_EVERY_N_FRAMES == 0:
            self.frame_count = 0
            
            if frame_queue.empty():
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_data = {
                    'img': rgb_frame,
                    'size': (frame_h, frame_w),
                    'mode': current_mode
                }
                frame_queue.put(frame_data)
            
            # --- Debug Performance ---
            # cur_time = time.time()
            # fps = 1.0 / (cur_time - self.prev_time) if (cur_time - self.prev_time) > 0 else 0.0
            # self.prev_time = cur_time

        if not status_detection_history:
            return "Working - nothing detected", latest_result

        distracted_count = sum(1 for status in status_detection_history if status == "Distracted")
        threshold = len(status_detection_history) - 1
        if distracted_count >= threshold:
            return "Distracted", latest_result
        return "Working", latest_result