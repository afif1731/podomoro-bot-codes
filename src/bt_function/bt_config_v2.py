import asyncio
import logging
import json
from bless import (
    BlessServer,
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
    GATTAttributePermissions
)

# Setup Logging agar terlihat di terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(name=__name__)

class PodomoroBT:
    def __init__(self, service_uuid, buffer_size=1024):
        self.service_uuid = service_uuid.lower()
        # Kita gunakan UUID yang sama untuk Characteristic agar simpel (atau bisa beda)
        # Sesuai request Ionic Anda:
        self.char_uuid = 'b1a2c3d4-e5f6-7890-a1b2-c3d4e5f67890'.lower()
        self.server_name = "raspi"  # Harus match dengan filter di Ionic
        self.server = None
        self.loop = asyncio.get_event_loop()
        
    async def init_server(self):
        # 1. Inisialisasi Server BLE
        self.server = BlessServer(name=self.server_name, loop=self.loop)
        self.server.read_request_func = self.on_read
        self.server.write_request_func = self.on_write
        
        # 2. Tambahkan Service
        try:
            await self.server.add_new_service(self.service_uuid)
        except Exception as e:
            logger.error(f"Error adding service: {e}")

        # 3. Tambahkan Characteristic (Read, Write, Notify)
        # Sifat: Bisa dibaca, Bisa ditulis (oleh Ionic), Bisa kirim notifikasi
        char_flags = (
            GATTCharacteristicProperties.read |
            GATTCharacteristicProperties.write |
            GATTCharacteristicProperties.write_without_response |
            GATTCharacteristicProperties.notify
        )
        permissions = (
            GATTAttributePermissions.readable |
            GATTAttributePermissions.writeable
        )
        
        try:
            await self.server.add_new_characteristic(
                self.service_uuid,
                self.char_uuid,
                char_flags,
                None,
                permissions
            )
            logger.info(f"✅ Service & Characteristic registered!")
            logger.info(f"   Service: {self.service_uuid}")
            logger.info(f"   Char:    {self.char_uuid}")
        except Exception as e:
            logger.error(f"Error adding characteristic: {e}")

        # 4. Mulai Advertising (Supaya HP bisa nemu)
        await self.server.start()
        logger.info("📡 Advertising dimulai... Menunggu koneksi dari Ionic.")
        
    def start_server(self):
        # Membungkus async function ke sync agar kompatibel dengan main.py lama
        self.loop.run_until_complete(self.init_server())

    # --- Callback saat Ionic MENGIRIM data ke Pi ---
    def on_write(self, characteristic_uuid: str, value: bytearray):
        try:
            payload = value.decode("utf-8")
            logger.info(f"📩 [TERIMA DARI HP] {payload}")
            
            # Parsing JSON
            data = json.loads(payload)
            action = data.get("action")
            
            if action == "UPDATE_TASK":
                t_id = data.get("task_id")
                status = data.get("status")
                print(f"👉 TASK UPDATE: ID={t_id}, STATUS={status}")
                # Lakukan logika database Anda di sini
                
        except Exception as e:
            logger.error(f"Gagal memproses data: {e}")

    # --- Callback saat Ionic MEMBACA data ---
    def on_read(self, characteristic_uuid: str) -> bytearray:
        logger.info("📖 [BACA] HP membaca data...")
        msg = json.dumps({"status": "ready", "message": "Hello from Pi"})
        return msg.encode("utf-8")

    # --- Fungsi Kirim Update ke HP (Notification) ---
    def send_notification(self, data_dict):
        if not self.server: 
            return
        
        json_str = json.dumps(data_dict)
        data_bytes = json_str.encode("utf-8")
        
        # Kirim notifikasi ke characteristic
        self.server.get_characteristic(self.char_uuid).value = data_bytes
        self.server.update_value(self.service_uuid, self.char_uuid)
        logger.info(f"📤 [KIRIM] {json_str}")

    def close_connection(self):
        if self.server:
            self.loop.run_until_complete(self.server.stop())
            logger.info("🛑 Server stopped.")