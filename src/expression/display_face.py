import os
import digitalio
import board
from PIL import Image, ImageOps
from adafruit_rgb_display.st7789 import ST7789

from expression_config import FACE_MAPPING

cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = digitalio.DigitalInOut(board.D24)
spi = board.SPI()
BAUDRATE = 64000000

# Setup driver (ST7789/GC9A01)
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

CACHE_IMAGES = {}

# Panggil ini waktu setup bot!
def preload_images():
    print("Memuat aset ke RAM...")
    for f_id, f_path in FACE_MAPPING.items():
        if os.path.exists(f_path):
            img = Image.open(f_path)
            img_processed = ImageOps.fit(img, (disp.width, disp.height), method=Image.LANCZOS)
            CACHE_IMAGES[f_id] = img_processed
        else:
            print(f"Warning: {f_path} hilang.")
    print("Selesai memuat aset.")

def display_face_fast(face_id):
    """
    Menampilkan gambar berdasarkan ID yang ada di FACE_MAPPING.
    Otomatis resize dan center crop agar pas di layar.
    """

    if face_id in CACHE_IMAGES:
        disp.image(CACHE_IMAGES[face_id])
    else:
        print(f"ID {face_id} belum di-preload.")

def display_face(face_id):
    """
    Menampilkan gambar berdasarkan ID yang ada di FACE_MAPPING.
    Otomatis resize dan center crop agar pas di layar.
    """
    
    if face_id not in FACE_MAPPING:
        print(f"Error: ID '{face_id}' tidak ditemukan di mapping.")
        return

    img_path = FACE_MAPPING[face_id]

    if not os.path.exists(img_path):
        print(f"Error: File tidak ditemukan di {img_path}")
        return

    try:
        image = Image.open(img_path)

        image_fitted = ImageOps.fit(
            image, 
            (disp.width, disp.height), 
            method=Image.LANCZOS, 
            centering=(0.5, 0.5)
        )

        disp.image(image_fitted)
        print(f"Menampilkan: {face_id}")

    except Exception as e:
        print(f"Gagal memuat gambar: {e}")