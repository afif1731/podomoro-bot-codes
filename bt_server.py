import asyncio
from src.bt_function.bt_config_v2 import PodomoroBT

# Pastikan ini SAMA dengan Frontend
BT_UUID = "a9ddf3dd-4642-46e0-b8a6-8151f88f843f"

if __name__ == "__main__":
    # Inisialisasi class
    bot = PodomoroBT(BT_UUID)
    
    try:
        # Menjalankan loop async utama
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\nBye.")