import time
import asyncio
from src.bt_function.bt_config_v2 import PodomoroBT

# Pastikan UUID SAMA PERSIS dengan di Ionic
# Service UUID
BT_UUID = "a9ddf3dd-4642-46e0-b8a6-8151f88f843f"

# Inisialisasi
bot_bt = PodomoroBT(BT_UUID)

try:
    # 1. Nyalakan Bluetooth Server
    bot_bt.start_server()
    
    print("\n--- SYSTEM READY ---")
    print("Silakan buka App Ionic dan tekan 'Cari & Hubungkan'")
    print("Tekan Ctrl+C untuk berhenti.\n")

    # 2. Keep Alive (Looping kosong agar program tidak mati)
    # Server BLE berjalan di background (handled by bless/asyncio internal)
    loop = asyncio.get_event_loop()
    loop.run_forever()

except KeyboardInterrupt:
    print("\nMematikan server...")
    bot_bt.close_connection()
    print("Bye.")