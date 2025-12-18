import asyncio
import sys
from src.bt_function.bt_config_v2 import PodomoroBT

BT_UUID = "a9ddf3dd-4642-46e0-b8a6-8151f88f843f"

async def async_input(prompt):
    return await asyncio.to_thread(input, prompt)

async def main():
    bot_bt = PodomoroBT(BT_UUID)
    
    server_task = asyncio.create_task(bot_bt.run())
    
    print("\n--- Podomoro Robot CLI ---")
    print("1: Get Config | 2: Get Recent TODO | 3: Update Status | 4: Exit")

    while True:
        try:
            angka = await async_input("\nMasukkan angka (1-4): ")

            if angka == "1":
                res = await bot_bt.get_podomoro_config()
                print(f"Result Config: {res}")
            elif angka == "2":
                res = await bot_bt.get_most_recent_todo()
                print(f"Result TODO: {res}")
            elif angka == "3":
                t_id = await async_input("Masukkan task id: ")
                t_status = await async_input("Status (TODO/ONGOING/FINISHED): ")
                res = await bot_bt.update_task_status(t_id, t_status)
                print(f"Update Result: {res}")
            elif angka == "4":
                print("Shutting down...")
                break
            else:
                print("Angka tidak valid!")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Terjadi kesalahan: {e}")

    server_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())