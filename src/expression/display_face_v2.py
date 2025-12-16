import digitalio
import board
import RPi.GPIO as GPIO

from PIL import Image, ImageOps
from adafruit_rgb_display.st7789 import ST7789 # Kita pakai class ST7789
from src.expression.face_map import FACE_MAPPING

cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = digitalio.DigitalInOut(board.D24)

BAUDRATE = 60000000 # 60 MHz

spi = board.SPI()

disp = ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=240,
    height=240,
    x_offset=0,
    y_offset=0 
)

try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(18, GPIO.OUT)
    GPIO.output(18, GPIO.HIGH)
except:
    pass

IMAGE_CACHE = {}

def preload_images():
    print("--- Preloading Images ---")
    for f_id, f_path in FACE_MAPPING.items():
        try:
            img = Image.open(f_path).convert("RGB")
            img_processed = ImageOps.fit(img, (240, 240), method=Image.LANCZOS)
            IMAGE_CACHE[f_id] = img_processed
            print(f"Loaded: {f_id}")
        except Exception as e:
            print(f"Fail: {f_id} -> {e}")

def display_face_fast(face_id):
    if face_id in IMAGE_CACHE:
        disp.image(IMAGE_CACHE[face_id])
    else:
        print(f"ID {face_id} not found")