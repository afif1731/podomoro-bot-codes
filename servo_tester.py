from src.servo.mover import MoveServo

SERVO_PIN = 17

servo = MoveServo(pin=SERVO_PIN)

while True:
    try:
        angka = int(input("Masukkan angka (1-4): "))

        if angka == 1:
            print("Podomoro Hands Up for 180s")
            servo.break_move(180)
        elif angka == 2:
            print("Podomoro Hands Down for 180s")
            servo.work_move(180)
        elif angka == 3:
            print("Taunting")
            servo.taunt()
        elif angka == 4:
            print("Move to 0")
            servo.zero_move()
        elif angka == 5:
            print("Move to default")
            servo.default_move()
        elif angka == 6:
            print("Cleaned Up")
            servo.cleanup()
        else:
            # Jika user memasukkan angka selain 1-4
            print("Angka tidak valid! Harap masukkan angka 1 sampai 4.")
                
    except ValueError:
        # Jika user memasukkan huruf atau simbol
        print("Input harus berupa angka.")