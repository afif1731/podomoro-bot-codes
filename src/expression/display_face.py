import os
import time
from PIL import Image, ImageOps
from luma.core.interface.serial import spi
from luma.lcd.device import gc9a01
from src.expression.face_map import FACE_MAPPING

# --- 1. SETUP DISPLAY ---

# Konfigurasi SPI
serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=24, speed_hz=24000000, spi_mode=0)

# Konfigurasi Device & Backlight
device = gc9a01(
    serial,
    width=240,
    height=240,
    rotate=0,
    h_offset=0,
    v_offset=0,
    bgr=True,
    gpio_LIGHT=18,      # Masukkan pin Backlight di sini
    active_low=False    # False berarti logic HIGH menyalakan layar
)

device.backlight(True)

IMAGE_CACHE = {}

def preload_images():
    """
    Membaca semua file di FACE_MAPPING, melakukan resize/fitting,
    dan menyimpannya ke dictionary IMAGE_CACHE di RAM.
    """
    print("--- Memulai Preload Aset ---")
    
    for face_id, file_path in FACE_MAPPING.items():
        if not os.path.exists(file_path):
            print(f"[SKIP] File tidak ditemukan: {file_path}")
            continue
            
        try:
            # 1. Buka Gambar
            img = Image.open(file_path).convert("RGB")
            
            # 2. Resize/Fit
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
    Menampilkan gambar dari RAM.
    """
    if face_id in IMAGE_CACHE:
        device.display(IMAGE_CACHE[face_id])
    else:
        print(f"Warning: ID '{face_id}' belum di-preload.")
        # Fallback ke mode lambat jika belum di-cache
        display_face(face_id)

def display_face(face_id):
    """
    Mode lambat (baca langsung dari disk) - berguna untuk testing/fallback
    """
    if face_id not in FACE_MAPPING:
        print(f"ID {face_id} tidak dikenal.")
        return

    path = FACE_MAPPING[face_id]
    try:
        if not os.path.exists(path):
            print(f"File {path} tidak ada.")
            return

        img = Image.open(path).convert("RGB")
        img_fitted = ImageOps.fit(
            img, 
            (device.width, device.height), 
            method=Image.LANCZOS,
            centering=(0.5, 0.5)
        )
        device.display(img_fitted)
        print(f"Wajah (Disk): {face_id}")
        
    except Exception as e:
        print(f"Error Face: {e}")