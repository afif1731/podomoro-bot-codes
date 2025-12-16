import asyncio
from src.bt_function.bt_config_v2 import PodomoroBT

# UUID harus SAMA
BT_UUID = "f000aa01-0451-4000-b000-000000000000"

async def main():
    bot_bt = PodomoroBT(BT_UUID)
    try:
        await bot_bt.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBye.")