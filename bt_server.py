import asyncio
import sys
from src.bt_function.bt_config_v2 import PodomoroBT

BT_UUID = "a9ddf3dd-4642-46e0-b8a6-8151f88f843f"

async def main():
    bot_bt = PodomoroBT(BT_UUID)
    
    # Jalankan server BLE
    await bot_bt.run()
    
    print("\n" + "="*30)
    print("ROBOT PODOMORO ONLINE")
    print("Control via Android App")
    print("="*30)

    shutdown_event = asyncio.Event()
    try:
        await shutdown_event.wait() 
    except KeyboardInterrupt:
        print("\nShutting down robot...")

if __name__ == "__main__":
    asyncio.run(main())