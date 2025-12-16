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
        self.char_uuid = 'f000aa01-0451-4000-b000-000000000000'.lower()
        self.server_name = "raspi"
        self.server = None
        
    async def run(self):
        # 1. Init Server
        self.server = BlessServer(name=self.server_name)
        self.server.read_request_func = self.on_read
        self.server.write_request_func = self.on_write
        
        # 2. Add Service
        try:
            await self.server.add_new_service(self.service_uuid)
        except Exception as e:
            logger.error(f"Error adding service: {e}")
            return

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
        except Exception as e:
            logger.error(f"Error adding characteristic: {e}")
            return

        # 4. Start Advertising
        # PENTING: Kita start server dan menunggu (await) di sini
        logger.info(f"✅ Service registered: {self.service_uuid}")
        
        # Mulai server
        await self.server.start()
        logger.info("📡 Advertising dimulai... Tekan Ctrl+C untuk stop.")
        
        # 5. Keep Alive (Looping di dalam async function ini)
        while True:
            await asyncio.sleep(1)

    # --- Callback Write ---
    def on_write(self, characteristic_uuid: str, value: bytearray):
        try:
            payload = value.decode("utf-8")
            logger.info(f"📩 [TERIMA] {payload}")
            
            data = json.loads(payload)
            if data.get("action") == "UPDATE_TASK":
                print(f"👉 TASK UPDATE: {data.get('task_id')} -> {data.get('status')}")
                
        except Exception as e:
            logger.error(f"Gagal parse data: {e}")

    # --- Callback Read ---
    def on_read(self, characteristic_uuid: str) -> bytearray:
        logger.info("📖 [BACA] Request masuk")
        return json.dumps({"msg": "Hello Pi"}).encode("utf-8")

    def send_notification(self, data_dict):
        if self.server:
            payload = json.dumps(data_dict).encode("utf-8")
            self.server.get_characteristic(self.char_uuid).value = payload
            self.server.update_value(self.service_uuid, self.char_uuid)