import RPi.GPIO as GPIO
import time

class MoveServo:
    def __init__(self, pin=18):
        """
        Inisialisasi Servo pada GPIO pin tertentu.
        Default menggunakan GPIO 18 (Pin fisik 12).
        """
        self.pin = pin
        self.taunt_speed = 0.2

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        
        # SG90 beroperasi pada frekuensi 50Hz
        self.pwm = GPIO.PWM(self.pin, 50)
        self.pwm.start(0) # Mulai dengan duty cycle 0 (diam)
        self._set_angle(180)
        self.pwm.ChangeDutyCycle(0)

    def _set_angle(self, angle):
        """
        Fungsi helper untuk mengubah sudut menjadi Duty Cycle.
        Rumus umum SG90: Duty Cycle = 2 + (Angle / 18)
        """
        duty = 2 + (angle / 18)
        self.pwm.ChangeDutyCycle(duty)
        # Kita tidak mematikan output di sini agar gerakan halus terjaga
        # selama loop work/break move.

    def work_move(self, duration: float):
        """
        Bergerak dari 0 ke 180 derajat secara bertahap
        selama durasi yang ditentukan.
        """
        print(f"Starting work_move: 0 -> 180 degrees in {duration} seconds.")
        start_angle = 180
        end_angle = 0
        
        # Hitung delay per 1 derajat pergerakan
        # Jika duration 900 detik, delay per step adalah 900/180 = 5 detik
        step_delay = duration / (start_angle - end_angle)
        
        for angle in range(start_angle, end_angle - 1, -1):
            self._set_angle(angle)
            time.sleep(step_delay)
            
        # Matikan sinyal sebentar untuk mencegah jitter setelah selesai
        self.pwm.ChangeDutyCycle(0)

    def break_move(self, duration: float):
        """
        Bergerak dari 180 ke 0 derajat (mundur/-180) secara bertahap
        selama durasi yang ditentukan.
        """
        print(f"Starting break_move: 180 -> 0 degrees in {duration} seconds.")
        start_angle = 0
        end_angle = 180
        
        step_delay = duration / (end_angle - start_angle)
        
        # Loop mundur dari 180 ke 0
        for angle in range(start_angle, end_angle + 1):
            self._set_angle(angle)
            time.sleep(step_delay)

        self.pwm.ChangeDutyCycle(0)

    def default_move(self):
        """
        Bergerak ke 180 derajat
        """
        print("Move to default")
        self._set_angle(180)
        time.sleep(0.5)
        self.pwm.ChangeDutyCycle(0)

    def zero_move(self):
        """
        Bergerak ke 0 derajat
        """
        print("Move to 0")
        self._set_angle(0)
        time.sleep(0.5)

    def taunt(self):
        """
        Gerakan mengejek: 45 derajat ke kanan dan kiri (relative to center)
        sebanyak 4 kali.
        Center = 90 derajat.
        +45 = 135 derajat
        -45 = 45 derajat
        """
        print("Taunting!")
        center = 90
        pos_high = center - 45  # 135 derajat
        pos_low = center + 45   # 45 derajat
        
        for _ in range(2):
            # Gerak ke +45
            self._set_angle(pos_high)
            time.sleep(self.taunt_speed)
            
            # Gerak ke -45
            self._set_angle(pos_low)
            time.sleep(self.taunt_speed)
            
        # Kembali ke posisi idle
        self._set_angle(180)
        time.sleep(0.8)
        self.pwm.ChangeDutyCycle(0)

    def cleanup(self):
        """Membersihkan konfigurasi GPIO saat selesai"""
        self.pwm.stop()
        GPIO.cleanup()