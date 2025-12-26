import os
from PIL import Image, ImageOps
from luma.core.interface.serial import spi
from luma.lcd.device import st7789
from src.expression.face_map import FACE_MAPPING

serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=24, speed_hz=24000000, spi_mode=0)
device = st7789(serial, width=240, height=240, rotate=0, bgr=True, gpio_LIGHT=18, active_low=False)
device.backlight(True)

IMAGE_CACHE = {}

def preload_images():
    """
    Memuat gambar ke RAM agar pergantian wajah instan.
    """
    print("--- Memuat Aset Wajah ke RAM ---")
    
    for face_id, file_path in FACE_MAPPING.items():
        if not os.path.exists(file_path):
            print(f"[SKIP] File tidak ditemukan: {file_path}")
            continue
            
        try:
            img = Image.open(file_path).convert("RGB")
            
            img_processed = ImageOps.fit(img, (240, 240), method=Image.LANCZOS, centering=(0.5, 0.5))
            
            IMAGE_CACHE[face_id] = img_processed
            print(f"[OK] {face_id}")
            
        except Exception as e:
            print(f"[ERROR] Gagal memuat {face_id}: {e}")

def display_face_fast(face_id):
    """
    Menampilkan wajah dari RAM.
    """
    if face_id in IMAGE_CACHE:
        device.display(IMAGE_CACHE[face_id])
    else:
        print(f"[WARNING] Face ID '{face_id}' tidak ada di Cache.")