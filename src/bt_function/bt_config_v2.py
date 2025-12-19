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
        self.char_uuid = 'b1a2c3d4-e5f6-7890-a1b2-c3d4e5f67890'.lower()
        self.server_name = "raspi"
        self.server = None

    async def run(self):
        self.server = BlessServer(name=self.server_name)
        self.server.read_request_func = self.on_read
        self.server.write_request_func = self.on_write
        
        char_flags = (
            GATTCharacteristicProperties.read |
            GATTCharacteristicProperties.write |
            GATTCharacteristicProperties.notify
        )
        permissions = (GATTAttributePermissions.readable | GATTAttributePermissions.writeable)

        await self.server.add_new_service(self.service_uuid)
        initial_val = bytearray(json.dumps({"status": "ready"}).encode('utf-8'))
        
        await self.server.add_new_characteristic(
            self.service_uuid, self.char_uuid, char_flags, initial_val, permissions
        )
        await self.server.start()
        logger.info("📡 Bluetooth Server Aktif & Menunggu Android...")

    def on_write(self, characteristic_uuid: str, value: bytearray):
        try:
            data = json.loads(value.decode("utf-8"))
            event_type = data.get("event")
            payload = data.get("payload")

            if event_type == "SYNC_ALL":
                logger.info(f"🔄 Sinkronisasi Full: {len(payload)} tugas diterima.")
            
            elif event_type == "UPDATE_TASK":
                logger.info(f"✅ Update: Task {payload['id']} pindah ke {payload['column']}")

        except Exception as e:
            logger.error(f"Gagal parse data: {e}")

    def on_read(self, characteristic_uuid: str) -> bytearray:
        return self.server.get_characteristic(self.char_uuid).value