import os
import RPi.GPIO as GPIO
from PIL import Image, ImageOps
from luma.core.interface.serial import spi
from luma.lcd.device import st7789

from src.expression.face_map import FACE_MAPPING

serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=24, speed_hz=8000000)
device = st7789(
    serial,
    width=240,
    height=240,
    rotate=0,
    h_offset=0,
    v_offset=0,
    bgr=True
    )

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
GPIO.output(18, GPIO.HIGH)

IMAGE_CACHE = {}

def preload_images():
    """
    Membaca semua file di FACE_MAPPING, melakukan resize/fitting,
    dan menyimpannya ke dictionary IMAGE_CACHE di RAM.
    """
    print("--- Memulai Preload Aset ---")
    
    for face_id, file_path in FACE_MAPPING.items():
        # Cek apakah file ada
        if not os.path.exists(file_path):
            print(f"[SKIP] File tidak ditemukan: {file_path}")
            continue
            
        try:
            # 1. Buka Gambar
            img = Image.open(file_path).convert("RGB")
            
            # 2. Proses Resize/Fit SEKARANG (bukan saat ditampilkan nanti)
            # Menggunakan LANCZOS agar halus untuk wajah/foto.
            # Jika ini Pixel Art murni, ganti Image.LANCZOS dengan Image.NEAREST
            img_processed = ImageOps.fit(
                img, 
                (device.width, device.height), 
                method=Image.LANCZOS, 
                centering=(0.5, 0.5)
            )
            
            # 3. Simpan ke RAM
            IMAGE_CACHE[face_id] = img_processed
            print(f"[OK] Berhasil memuat: {face_id}")
            
        except Exception as e:
            print(f"[ERROR] Gagal memuat {face_id}: {e}")
            
    print(f"--- Preload Selesai. Total: {len(IMAGE_CACHE)} gambar ---")

def display_face_fast(face_id):
    """
    Menampilkan gambar dari RAM. Sangat cepat.
    """
    # Cek apakah ID ada di Cache
    if face_id in IMAGE_CACHE:
        # Langsung kirim data memori ke layar
        device.display(IMAGE_CACHE[face_id])
    else:
        print(f"Warning: ID '{face_id}' tidak ditemukan di Cache atau gagal dimuat.")

def display_face(face_id):
    """
    Menampilkan wajah dari mapping ID dengan smart fitting
    """
    if face_id not in FACE_MAPPING:
        print(f"ID {face_id} tidak dikenal.")
        return

    path = FACE_MAPPING[face_id]
    
    try:
        img = Image.open(path).convert("RGB")
        
        # ImageOps.fit sangat berguna untuk mengisi layar penuh tanpa gepeng
        # method=Image.LANCZOS untuk hasil halus (foto/wajah)
        img_fitted = ImageOps.fit(
            img, 
            (device.width, device.height), 
            method=Image.LANCZOS,
            centering=(0.5, 0.5)
        )
        
        device.display(img_fitted)
        print(f"Wajah: {face_id}")
        
    except Exception as e:
        print(f"Error Face: {e}")