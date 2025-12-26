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
        self._buffer = ""

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
        
        # Beri nilai awal agar characteristic terdaftar dengan benar di DBus Linux
        initial_val = bytearray("READY\n".encode('utf-8'))
        
        await self.server.add_new_characteristic(
            self.service_uuid, self.char_uuid, char_flags, initial_val, permissions
        )
        await self.server.start()
        print("📡 Bluetooth Server Aktif & Menunggu Android...", flush=True)

    def on_write(self, characteristic_uuid: str, value: bytearray):
        try:
            raw_data = value.decode("utf-8")
            self._buffer += raw_data
            
            # Print setiap potongan data (Force Flush agar muncul di terminal)
            print(f"DEBUG: Data masuk -> {raw_data}", end="", flush=True)

            if self._buffer.endswith("\n"):
                print("\nDEBUG: Paket lengkap diterima!", flush=True)
                complete_data = self._buffer.strip()
                self._buffer = ""

                data = json.loads(complete_data)
                event_type = data.get("event")
                payload = data.get("payload")

                if event_type == "SYNC_ALL":
                    print(f"\n🔄 SINKRONISASI BERHASIL: {len(payload)} tugas", flush=True)
                    for task in payload:
                        print(f" >> [{task['column'].upper()}] {task['name']}", flush=True)
                
                elif event_type == "UPDATE_TASK":
                    print(f"✅ UPDATE: Task {payload['id']} ke {payload['column']}", flush=True)

        except Exception as e:
            print(f"\n❌ ERROR: {e}", flush=True)
            self._buffer = ""

    def on_read(self, characteristic_uuid: str) -> bytearray:
        return self.server.get_characteristic(self.char_uuid).value