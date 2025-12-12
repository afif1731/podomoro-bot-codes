# use: uv venv && uv pip install fastapi uvicorn pydantic && uvicorn bluetooth_server:app --host 0.0.0.0 --port 8000

import subprocess
import time
from typing import List
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Raspberry Pi Bluetooth API")

# devmode yes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BLUETOOTH_STATE = {
    "device_name": "RaspberryPi-BT",
    "mac_address": "B8:27:EB:AA:BB:CC",  # ❗ GANTI output `hciconfig hci0`
    "connected": False,
    "discovering": False,
    "connected_devices": [],
    "ip_address": "10.238.183.42",      # ❗ GANTI IP Pi (`hostname -I`)
    "signal_strength": -65,
    "last_updated": "",
    "connected_count": 0,
}

DISCOVERED_DEVICES: List[dict] = []

class ConnectRequest(BaseModel):
    mac: str
    device_id: str

class DisconnectRequest(BaseModel):
    mac: str

def get_pi_mac() -> str:
    try:
        out = subprocess.run(["hciconfig", "hci0"], capture_output=True, text=True).stdout
        for line in out.splitlines():
            if "BD Address:" in line:
                return line.split()[2]
    except:
        pass
    return "00:00:00:00:00:00"

def run_bt_command(cmd: List[str], timeout: int = 10) -> str:
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if res.returncode != 0:
            raise Exception(res.stderr.strip())
        return res.stdout
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{' '.join(cmd)}: {e}")

@app.on_event("startup")
def startup():
    BLUETOOTH_STATE["mac_address"] = get_pi_mac()
    BLUETOOTH_STATE["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")

@app.get("/api/bluetooth/health")
def health():
    return {"status": "ok"}

@app.get("/api/bluetooth/status")
def status():
    BLUETOOTH_STATE["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"status": "success", "data": BLUETOOTH_STATE.copy()}

@app.post("/api/bluetooth/discover")
def discover():
    try:
        BLUETOOTH_STATE["discovering"] = True
        run_bt_command(["bluetoothctl", "scan", "on"])
        time.sleep(8)  
        run_bt_command(["bluetoothctl", "scan", "off"])

        out = run_bt_command(["bluetoothctl", "devices"])
        devices = []
        for line in out.strip().splitlines():
            if line.startswith("Device "):
                _, mac, name = line.split(maxsplit=2)
                devices.append({
                    "id": mac.replace(":", "").lower(),
                    "name": name,
                    "mac": mac,
                    "type": "unknown",
                    "signal": -70 + len(devices),  # dummy
                    "icon": "phonePortrait" if "Phone" in name else "laptop",
                })
        global DISCOVERED_DEVICES
        DISCOVERED_DEVICES = devices
        return {"status": "success", "discovered_devices": devices, "count": len(devices)}
    finally:
        BLUETOOTH_STATE["discovering"] = False

@app.post("/api/bluetooth/connect")
def connect(req: ConnectRequest):
    try:
        run_bt_command(["bluetoothctl", "pair", req.mac])
        run_bt_command(["bluetoothctl", "trust", req.mac])
        out = run_bt_command(["bluetoothctl", "connect", req.mac])
        if "successful" not in out.lower():
            raise Exception("Connection failed")

        device = next((d for d in DISCOVERED_DEVICES if d["mac"] == req.mac), None)
        if not device:
            device = {"id": req.device_id, "name": f"Unknown ({req.mac})", "mac": req.mac,
                      "type": "unknown", "signal": -75, "icon": "bluetoothOutline"}

        connected = {
            **device,
            "connected": True,
            "connection_time": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "ip_assigned": BLUETOOTH_STATE["ip_address"],
        }
        BLUETOOTH_STATE["connected_devices"].append(connected)
        BLUETOOTH_STATE["connected"] = True
        BLUETOOTH_STATE["connected_count"] = len(BLUETOOTH_STATE["connected_devices"])
        return {"status": "success", "message": f"Connected to {req.mac}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bluetooth/disconnect")
def disconnect(req: DisconnectRequest):
    try:
        run_bt_command(["bluetoothctl", "disconnect", req.mac])
        run_bt_command(["bluetoothctl", "remove", req.mac])  
        BLUETOOTH_STATE["connected_devices"] = [
            d for d in BLUETOOTH_STATE["connected_devices"] if d["mac"] != req.mac
        ]
        BLUETOOTH_STATE["connected"] = len(BLUETOOTH_STATE["connected_devices"]) > 0
        BLUETOOTH_STATE["connected_count"] = len(BLUETOOTH_STATE["connected_devices"])
        return {"status": "success", "message": f"Disconnected from {req.mac}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bluetooth/command")
def command(req: dict):
    cmd = req.get("command", "").upper()
    if cmd in ["LED_ON", "LED_OFF"]:
        return {"status": "success", "executed": cmd}
    raise HTTPException(status_code=400, detail="Unknown command")