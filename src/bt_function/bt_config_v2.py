import asyncio
import logging
import json
from bless import (
    BlessServer,
    GATTCharacteristicProperties,
    GATTAttributePermissions
)

class PodomoroBT:
    def __init__(self, service_uuid):
        self.service_uuid = service_uuid.lower()
        self.char_uuid = 'b1a2c3d4-e5f6-7890-a1b2-c3d4e5f67890'.lower()
        self.server_name = "raspi"
        self.server = None
        self._buffer = "" # Menampung potongan data

    async def run(self):
        self.server = BlessServer(name=self.server_name)
        self.server.read_request_func = self.on_read
        self.server.write_request_func = self.on_write
        
        char_flags = (GATTCharacteristicProperties.read | GATTCharacteristicProperties.write | GATTCharacteristicProperties.notify)
        permissions = (GATTAttributePermissions.readable | GATTAttributePermissions.writeable)

        await self.server.add_new_service(self.service_uuid)
        await self.server.add_new_characteristic(self.service_uuid, self.char_uuid, char_flags, bytearray("READY\n".encode('utf-8')), permissions)
        await self.server.start()
        print("📡 Bluetooth Server Aktif & Menunggu Android...")

    def on_write(self, characteristic_uuid: str, value: bytearray):
        try:
            raw_data = value.decode("utf-8")
            self._buffer += raw_data
            
            # Print potongan data tanpa newline agar terlihat progressnya
            print(f"{raw_data}", end="", flush=True)

            # Jika ada newline (\n), berarti satu pesan utuh selesai
            if "\n" in self._buffer:
                lines = self._buffer.split("\n")
                # Simpan bagian yang belum lengkap (setelah \n terakhir) kembali ke buffer
                self._buffer = lines.pop() 
                
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    
                    print(f"\n✅ Paket lengkap diterima! Memproses...")
                    data = json.loads(line)
                    event_type = data.get("event")
                    payload = data.get("payload")

                    if event_type == "SYNC_ALL":
                        print(f"🔄 SINKRONISASI: {len(payload)} tugas")
                        for task in payload:
                            print(f" >> [{task['column'].upper()}] {task['name']}")
                    
                    elif event_type == "UPDATE_TASK":
                        print(f"📌 UPDATE: Task {payload.get('task_id')} -> {payload.get('status')}")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            self._buffer = ""

    def on_read(self, characteristic_uuid: str) -> bytearray:
        return self.server.get_characteristic(self.char_uuid).value