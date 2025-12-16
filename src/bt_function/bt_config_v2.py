import asyncio
import logging
import json
from bless import (
    BlessServer,
    GATTCharacteristicProperties,
    GATTAttributePermissions
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(name=__name__)

class PodomoroBT:
    def __init__(self, service_uuid):
        self.service_uuid = service_uuid.lower()
        # UUID Characteristic harus SAMA dengan Frontend
        self.char_uuid = 'b1a2c3d4-e5f6-7890-a1b2-c3d4e5f67890'.lower()
        
        self.server_name = "raspi"
        self.server = None
        
    async def run(self):
        # 1. Inisialisasi Server
        self.server = BlessServer(name=self.server_name)
        self.server.read_request_func = self.on_read
        self.server.write_request_func = self.on_write
        
        # 2. Add Service
        logger.info("⏳ Mendaftarkan Service...")
        try:
            await self.server.add_new_service(self.service_uuid)
        except Exception as e:
            logger.error(f"Error adding service: {e}")

        # 3. Add Characteristic
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
            logger.info(f"✅ Service UUID: {self.service_uuid}")
            logger.info(f"✅ Char UUID:    {self.char_uuid}")
        except Exception as e:
            logger.error(f"Error adding characteristic: {e}")

        # 4. Start Advertising & Keep Alive
        try:
            await self.server.start()
            logger.info("📡 Server BERJALAN. Menunggu koneksi...")
            
            # Loop agar program tidak keluar
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
             logger.error(f"Error starting server: {e}")

    # --- Callback WRITE (Terima data dari HP) ---
    def on_write(self, characteristic_uuid: str, value: bytearray):
        try:
            payload = value.decode("utf-8")
            logger.info(f"📩 [TERIMA] {payload}")
            
            # Coba parse JSON
            data = json.loads(payload)
            if data.get("action") == "UPDATE_TASK":
                t_id = data.get("task_id")
                status = data.get("status")
                print(f"👉 UPDATE TASK: ID={t_id}, Status={status}")
                
        except Exception as e:
            logger.error(f"Gagal parse data: {e}")

    # --- Callback READ (HP minta data) ---
    def on_read(self, characteristic_uuid: str) -> bytearray:
        logger.info("📖 [BACA] HP membaca data...")
        return json.dumps({"msg": "Connected to Pi"}).encode("utf-8")