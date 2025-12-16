from src.expression.display_face_v2 import display_face_fast, preload_images

preload_images()

while True:
    try:
        angka = int(input("Masukkan angka (1-7): "))

        # Logika percabangan
        if angka == 1:
            print("idle face")
            display_face_fast("idle")
        elif angka == 2:
            print("working face")
            display_face_fast("working")
        elif angka == 3:
            print("break face")
            display_face_fast("break")
        elif angka == 4:
            print("distracted face")
            display_face_fast("distracted")
        elif angka == 5:
            print("break-reminder face")
            display_face_fast("break-reminder")
        elif angka == 6:
            print("loading face")
            display_face_fast("loading")
        elif angka == 7:
            print("connected face")
            display_face_fast("connected")
        else:
            # Jika user memasukkan angka selain 1-5
            print("Angka tidak valid! Harap masukkan angka 1 sampai 7.")

    except ValueError:
        # Jika user memasukkan huruf atau simbol
        print("Input harus berupa angka.")