import cv2
import time
import threading

from src.servo.mover import MoveServo
from src.expression.display_face import preload_images, display_face_fast
from src.cv.classifier import BotClassifier, inference_worker

SERVO_PIN = 17
CAMERA_WIDTH = 240
CAMERA_HEIGHT = 240
CONF_THRESH = 0.25
LABEL_CONF_THRESH = 0.6
STATUS_CONF_THRESH = 0.85
CAM_URL = "http://10.238.183.49:81/stream"

POMODORO_CONF = {
    "work_time": 25 * 60,
    "break_time": 5 * 60
}

# Preload Setup
bot_detection_status = "Idle" # Idle, Working, Break
is_pomodoro_timer_running = False
is_being_reminded = False
is_await_confirmation = False
is_on_transition = False

timer_second = 0
confirmation_delay = 0
reminder_time = 0
transition_time = 0

def start_podomoro(*servo: MoveServo):
    print("Pomodoro Work Timer Started")
    display_face_fast("working")
    servo.work_move(POMODORO_CONF["work_time"])

def break_podomoro(*servo: MoveServo):
    print("Pomodoro Break Timer Started")
    display_face_fast("break")
    servo.break_move(POMODORO_CONF["break_time"])

def stop_podomoro(*servo: MoveServo):
    print("Pomodoro Break Timer Stopped")
    display_face_fast("idle")
    servo.default_move()

def transition_podomoro(transition_type):
    if transition_type == "break":
        print("It is time to break")
        display_face_fast("idle")
        time.sleep(3)
    if transition_type == "working":
        print("It is time to working")
        display_face_fast("idle")
        time.sleep(3)

def distraction_reminder(result):
    print(f"Distraction detected! Label: {result['label']} | Confidence: {result['confidence']}")
    display_face_fast("distracted")

def break_reminder():
    print("Human detected! It is time to break")
    display_face_fast("break-reminder")

def asking_confirmation(confirm_to):
    if confirm_to == "task-done":
        print("Is your task finished?")
        display_face_fast("loading")
    if confirm_to == "end":
        print("Are you sure going to end pomodoro timer?")
        display_face_fast("loading")

# ----------------------------------------------------------------------------------------------------

def main():
    # Preload Setup
    global bot_detection_status
    global is_pomodoro_timer_running
    global is_being_reminded
    global is_await_confirmation

    global timer_second
    global confirmation_delay
    global reminder_time
    global transition_time

    servo = MoveServo(pin=SERVO_PIN)
    preload_images()

    cap = cv2.VideoCapture(CAM_URL)
    # Set resolusi kamera (opsional, sesuaikan kemampuan webcam)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

    if not cap.isOpened():
        raise RuntimeError("Cannot open webcam in cam url.")
    print("Camera setted")

    cv_classifier = BotClassifier(cap=cap)

    # Start Thread
    worker_t = threading.Thread(target=inference_worker, daemon=True)
    worker_t.start()

    # First Boot Scene
    servo.taunt()
    display_face_fast("idle")
    # Play Sound: Hallo, Podomoro siap berjalan
    time.sleep(3.5)


    # Connecting to Bluetooth
    display_face_fast("loading")
    # Play Sound: Bluetooth Connected

    # Retrieve Data
    display_face_fast("connected")

    #--- Main Loop ---
    display_face_fast("idle")
    prev_sec = 0 # time now

    while True:
        current_sec = 0 # time now

        # One Second Timer
        if prev_sec - current_sec >= 1:
            prev_sec = current_sec

            if is_pomodoro_timer_running is True and timer_second > 0:
                timer_second -= 1
            if is_await_confirmation is True and confirmation_delay < 3:
                confirmation_delay += 1
            if is_being_reminded is True and reminder_time < 3:
                reminder_time += 1
            if is_on_transition is True and transition_time < 3:
                transition_time += 1
        
        status, result = cv_classifier.classifier_loop() # status = "Working" | "Distracted". result = {"found": boolean; "label": string; "confidence": float}

        if is_on_transition is True and transition_time < 3:
            continue

        if is_on_transition is True and transition_time >= 3:
            is_on_transition = False
            transition_time = 0

        # --- Idle Logic ---
        if bot_detection_status == "Idle":
            if is_pomodoro_timer_running is False and result["label"] == "start_pomodoro" and result["confidence"] > STATUS_CONF_THRESH:
                bot_detection_status = "Working"
                is_pomodoro_timer_running = True
                timer_second = POMODORO_CONF["work_time"]
                start_podomoro(servo)
                continue
        
        # --- Working Logic ---
        if bot_detection_status == "Working":
            print("is Working")
            
            if is_being_reminded is True and reminder_time >= 3:
                is_being_reminded = False
                reminder_time = 0

            if is_await_confirmation is True:
                if confirmation_delay > 2 and confirmation_delay < 6:
                    if result["label"] == "stop_pomodoro" and result["confidence"] > STATUS_CONF_THRESH:
                        bot_detection_status = "Idle"
                        is_pomodoro_timer_running = False
                        timer_second = 0
                        stop_podomoro(servo)
                        continue

                if confirmation_delay >= 6:
                    is_await_confirmation = False
                    confirmation_delay = 0

            if result["label"] == "stop_pomodoro" and result["confidence"] > STATUS_CONF_THRESH and is_await_confirmation is False:
                is_await_confirmation = True
                asking_confirmation("end")
                continue

            if status == "Distracted":
                if is_being_reminded is False:
                    is_being_reminded = True
                    distraction_reminder(result=result)
                    continue
            
            if timer_second == 0:
                is_pomodoro_timer_running = False
                transition_podomoro("break")
                bot_detection_status = "Break"
                continue
        
        # --- Break Logic ---
        if bot_detection_status == "Break":
            print("is on break")

            if is_await_confirmation is True:
                if confirmation_delay > 2 and confirmation_delay < 6:
                    if result["label"] == "stop_pomodoro" and result["confidence"] > STATUS_CONF_THRESH:
                        # move task to todo
                        print("task returned to todo")

                    if result["label"] == "start_pomodoro" and result["confidence"] > STATUS_CONF_THRESH:
                        # move task to finished
                        print("task updated to finished")
                    
                    bot_detection_status = "Idle"
                    is_pomodoro_timer_running = False
                    timer_second = 0
                    stop_podomoro(servo)
                    continue
                
                if confirmation_delay >= 6:
                    is_await_confirmation = False
                    confirmation_delay = 0

            if result["found"] is True:
                if result["label"] == "stop_pomodoro" and result["confidence"] > STATUS_CONF_THRESH and is_await_confirmation is False:
                    is_await_confirmation = True
                    asking_confirmation("task-done")
                    continue

                if is_being_reminded is False:
                    is_being_reminded = True
                    break_reminder()
                    continue

            if timer_second == 0:
                is_pomodoro_timer_running = False
                transition_podomoro("working")
                bot_detection_status = "Working"


if __name__ == "__main__":
    main()
