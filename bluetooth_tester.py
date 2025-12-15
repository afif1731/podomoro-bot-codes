from src.bt_function.bt_config import PodomoroBT

BT_UUID="a9ddf3dd-4642-46e0-b8a6-8151f88f843f"
BT_BUFFER_SIZE="1024"

bot_bt = PodomoroBT(BT_UUID, BT_BUFFER_SIZE)

bot_bt.start_server()

while True:
    try:
        angka = int(input("Masukkan angka (1-4): "))

        if angka == 1:
            print("Get Podomoro Config")
            response = bot_bt.get_podomoro_config()
            print(response)
        elif angka == 2:
            print("Get Recent TODO Task")
            response = bot_bt.get_most_recent_todo()
            print(response)
        elif angka == 3:
            print("Update Status")
            task_id = int(input("Masukkan task id: "))
            task_status = int(input("Masukkan status (TODO / ONGOING / FINISHED): "))
            response = bot_bt.update_task_status(task_id, task_status)
            print(response)
        elif angka == 4:
            print("Shut down, press Ctrl + C after this")
            bot_bt.close_connection()
        else:
            # Jika user memasukkan angka selain 1-4
            print("Angka tidak valid! Harap masukkan angka 1 sampai 4.")
                
    except ValueError:
        # Jika user memasukkan huruf atau simbol
        print("Input harus berupa angka.")