import json
import bluetooth

class PodomoroBT:
  def __init__(self, uuid, buffer_size):
    self.BT_UUID = uuid
    self.BT_BUFFER_SIZE = buffer_size
    self.client_sock = None
    self.server_sock = None
    self.connected = False
  
  def start_server(self):
    self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    self.server_sock.bind(("", bluetooth.PORT_ANY))
    self.server_sock.listen(1)

    port = self.server_sock.getsockname()[1]

    bluetooth.advertise_service(self.server_sock, "Podomoro Bot",
                                service_id=self.BT_UUID,
                                service_classes=[self.BT_UUID, bluetooth.SERIAL_PORT_CLASS],
                                profiles=[bluetooth.SERIAL_PORT_PROFILE])

    print(f"[BT] Menunggu koneksi pada channel {port}...")
    
    # Program akan berhenti di sini sampai HP connect
    self.client_sock, client_info = self.server_sock.accept()
    self.connected = True
    print(f"[BT] Terhubung dengan {client_info}")

  def _send_and_wait(self, command_dict):
    """
    Fungsi internal: Kirim JSON ke HP -> Tunggu Balasan -> Return JSON
    """
    if not self.connected or not self.client_sock:
      print("[BT Error] Tidak ada perangkat terhubung.")
      return None

    try:
      msg_str = json.dumps(command_dict)
      self.client_sock.send(msg_str)
      print(f"[BT Sent] {msg_str}")

      data = self.client_sock.recv(self.BT_BUFFER_SIZE) # HP harus diprogram untuk langsung membalas setelah terima request ini
      
      if not data:
        return None

      response_str = data.decode("utf-8")
      response_json = json.loads(response_str)
      return response_json

    except Exception as e:
        print(f"[BT Error] Komunikasi gagal: {e}")
        self.connected = False
        return None

  def get_podomoro_config(self):
    print("[BT] Meminta config dari HP...")
    
    payload = {"action": "GET_CONFIG"} 
    
    response = self._send_and_wait(payload)

    if response and "work_time" in response:
      return {
          "work_time": response["work_time"],
          "break_time": response["break_time"]
      }
    else:
      print("[BT] Gagal ambil config, gunakan default.")
      return None

  def update_task_status(self, task_id, status):
    payload = {
        "action": "UPDATE_TASK",
        "task_id": task_id,
        "status": status
    }
    
    response = self._send_and_wait(payload)
    return response.get("status") == "success" if response else False

  def request_get_most_recent_task(self):
    print("meminta app untuk menigirm task di urutan paling atas")

  def close_connection(self):
    if self.client_sock:
      self.client_sock.close()
    if self.server_sock:
      self.server_sock.close()
    print("[BT] Koneksi ditutup.")