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
        self._response_event = asyncio.Event()
        self._latest_response = None

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
        logger.info("📡 Bluetooth Server Berjalan...")

    async def _request_and_wait(self, command_dict, timeout=10):
        """Helper untuk mengirim perintah dan menunggu balasan dari HP"""
        self._latest_response = None
        self._response_event.clear()
        
        # Kirim perintah ke characteristic
        payload = json.dumps(command_dict).encode('utf-8')
        self.server.get_characteristic(self.char_uuid).value = bytearray(payload)
        
        try:
            # Tunggu sampai on_write menerima response_type
            await asyncio.wait_for(self._response_event.wait(), timeout=timeout)
            return self._latest_response
        except asyncio.TimeoutError:
            logger.warning("⏳ Timeout menunggu respon dari HP")
            return None

    # Fungsi untuk dipanggil di main.py
    async def get_podomoro_config(self):
        return await self._request_and_wait({"command": "GET_CONFIG"})

    async def get_most_recent_todo(self):
        return await self._request_and_wait({"command": "GET_RECENT_TODO"})

    async def update_task_status(self, task_id, status):
        return await self._request_and_wait({
            "command": "UPDATE_STATUS", 
            "task_id": task_id, 
            "status": status
        })

    def on_write(self, characteristic_uuid: str, value: bytearray):
        try:
            data = json.loads(value.decode("utf-8"))
            logger.info(f"📩 [DITERIMA] {data}")
            
            # Jika data mengandung key 'response_type', tandai sebagai jawaban
            if "response_type" in data:
                self._latest_response = data
                self._response_event.set()
        except Exception as e:
            logger.error(f"Gagal parse data: {e}")

    def on_read(self, characteristic_uuid: str) -> bytearray:
        return self.server.get_characteristic(self.char_uuid).value