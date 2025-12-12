# src/bluetooth/mock_bluetooth.py
class BluetoothSocket:
    def __init__(self, protocol=None):
        self.protocol = protocol
        self.data = b""

    def bind(self, addr):
        print(f"[MOCK] 🔌 bind({addr})")

    def listen(self, n=1):
        print(f"[MOCK] 🎧 listen({n})")

    def accept(self):
        print("[MOCK] 📱 Simulasi koneksi dari HP")
        return BluetoothSocket(), ("AA:BB:CC:DD:EE:FF", 1)

    def recv(self, size):
        import time
        time.sleep(0.5)
        # Simulasi pesan dari Ionic app
        return b'{"lampu":"ON","brightness":75}\n'

    def send(self, data):
        msg = data.decode().strip()
        print(f"[MOCK] 📤 Balas ke HP: '{msg}'")
        return len(data)

    def close(self):
        print("[MOCK] 🔌 Socket ditutup")

def advertise_service(sock, name, service_id=None, service_classes=None, profiles=None):
    print(f"[MOCK] 📢 Iklankan service: '{name}' (UUID: {service_id})")

# Konstanta RFCOMM — biar kompatibel dengan kode asli
RFCOMM = 3
PORT_ANY = 0
SERIAL_PORT_CLASS = "1101"
SERIAL_PORT_PROFILE = "1101"