import json
import time
import random
import socket
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inisialisasi Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS untuk Ionic frontend

class BluetoothSimulator:
    """Simulator untuk Bluetooth Raspberry Pi"""
    
    def __init__(self, device_name: str = "RaspberryPi-BT"):
        """
        Inisialisasi simulator Bluetooth
        
        Args:
            device_name: Nama perangkat Bluetooth
        """
        self.device_name = device_name
        self.connected_devices = []
        self.connection_status = False
        self.ip_address = None
        self.mac_address = self._generate_mac_address()
        self.discovery_mode = False
        self.paired_devices = []
        self.running = False
        
        # Status untuk monitoring
        self.status = {
            "device_name": device_name,
            "mac_address": self.mac_address,
            "connected": False,
            "discovering": False,
            "paired_devices": [],
            "connected_devices": [],
            "signal_strength": 0,
            "last_updated": None,
            "ip_address": None,
            "connected_count": 0
        }
    
    def _generate_mac_address(self) -> str:
        """Generate MAC address acak untuk simulasi"""
        return ':'.join(['%02x' % random.randint(0, 255) for _ in range(6)])
    
    def start_discovery(self) -> Dict[str, Any]:
        """Simulasi memulai discovery perangkat Bluetooth"""
        logger.info("Memulai discovery Bluetooth...")
        self.discovery_mode = True
        
        # Simulasi menemukan beberapa perangkat
        simulated_devices = [
            {
                "id": str(uuid.uuid4()),
                "name": "iPhone-13",
                "mac": "JJ:BB:CC:DD:EE:110",
                "type": "phone",
                "signal": random.randint(-70, -30),
                "icon": "phonePortrait"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Android-Device",
                "mac": "AA:BB:CC:DD:EE:22",
                "type": "phone",
                "signal": random.randint(-75, -35),
                "icon": "phonePortrait"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Laptop-Dell",
                "mac": "AA:BB:CC:DD:EE:44",
                "type": "computer",
                "signal": random.randint(-65, -25),
                "icon": "laptop"
            }
        ]
        
        time.sleep(2)  # Simulasi waktu scanning
        
        self.discovery_mode = False
        logger.info(f"Discovery selesai. Ditemukan {len(simulated_devices)} perangkat")
        
        return {
            "status": "success",
            "discovered_devices": simulated_devices,
            "count": len(simulated_devices),
            "timestamp": datetime.now().isoformat()
        }
    
    def connect_device(self, mac_address: str, device_name: str = None) -> Dict[str, Any]:
        """Simulasi koneksi ke perangkat Bluetooth"""
        logger.info(f"Mencoba koneksi ke perangkat: {mac_address}")
        
        # Simulasi proses koneksi
        time.sleep(1.5)
        
        # 80% kemungkinan berhasil, 20% gagal
        if random.random() < 0.8:
            device_info = {
                "id": str(uuid.uuid4()),
                "name": device_name or f"Device-{mac_address[-5:].replace(':', '')}",
                "mac": mac_address,
                "type": "phone",
                "connected": True,
                "connection_time": datetime.now().isoformat(),
                "ip_assigned": f"192.168.1.{random.randint(100, 200)}",
                "signal_strength": random.randint(-50, -20),
                "icon": "phonePortrait"
            }
            
            self.connected_devices.append(device_info)
            self.connection_status = True
            
            logger.info(f"Berhasil terhubung ke {mac_address}")
            
            return {
                "status": "connected",
                "device": device_info,
                "message": "Koneksi berhasil"
            }
        else:
            logger.warning(f"Gagal terhubung ke {mac_address}")
            return {
                "status": "failed",
                "message": "Koneksi gagal. Perangkat tidak ditemukan atau tidak responsif."
            }
    
    def disconnect_device(self, mac_address: str) -> Dict[str, Any]:
        """Simulasi disconnect perangkat"""
        logger.info(f"Memutuskan koneksi dari: {mac_address}")
        
        # Hapus dari connected devices
        disconnected_device = None
        for device in self.connected_devices:
            if device.get('mac') == mac_address:
                disconnected_device = device
                break
        
        self.connected_devices = [
            dev for dev in self.connected_devices 
            if dev.get('mac') != mac_address
        ]
        
        # Update status
        self.connection_status = len(self.connected_devices) > 0
        
        return {
            "status": "disconnected",
            "device": disconnected_device,
            "message": f"Berhasil disconnect dari {mac_address}"
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Mendapatkan status Bluetooth saat ini"""
        current_ip = self._get_ip_address()
        
        self.status.update({
            "connected": self.connection_status,
            "connected_devices": self.connected_devices,
            "discovering": self.discovery_mode,
            "signal_strength": random.randint(-80, -20) if self.connection_status else 0,
            "ip_address": current_ip,
            "last_updated": datetime.now().isoformat(),
            "connected_count": len(self.connected_devices)
        })
        
        return self.status
    
    def _get_ip_address(self) -> Optional[str]:
        """Mendapatkan IP address (simulasi)"""
        try:
            # Simulasi IP address
            ips = [
                "192.168.1.100",
                "192.168.0.50",
                "10.0.0.25",
                "172.20.10.5"
            ]
            return random.choice(ips) if self.connection_status else None
        except:
            return None

# Inisialisasi simulator Bluetooth
bluetooth_simulator = BluetoothSimulator(device_name="RaspberryPi-BT-Server")

# API Endpoints
@app.route('/api/bluetooth/status', methods=['GET'])
def get_bluetooth_status():
    """Endpoint untuk mendapatkan status Bluetooth"""
    status = bluetooth_simulator.get_status()
    return jsonify({
        "status": "success",
        "data": status,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/bluetooth/discover', methods=['POST'])
def discover_devices():
    """Endpoint untuk melakukan discovery perangkat"""
    try:
        result = bluetooth_simulator.start_discovery()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in discover: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/bluetooth/connect', methods=['POST'])
def connect_device():
    """Endpoint untuk menghubungkan ke perangkat"""
    try:
        data = request.get_json()
        mac_address = data.get('mac_address')
        device_name = data.get('device_name')
        
        if not mac_address:
            return jsonify({
                "status": "error",
                "message": "MAC address is required"
            }), 400
        
        result = bluetooth_simulator.connect_device(mac_address, device_name)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in connect: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/bluetooth/disconnect', methods=['POST'])
def disconnect_device():
    """Endpoint untuk memutuskan koneksi perangkat"""
    try:
        data = request.get_json()
        mac_address = data.get('mac_address')
        
        if not mac_address:
            return jsonify({
                "status": "error",
                "message": "MAC address is required"
            }), 400
        
        result = bluetooth_simulator.disconnect_device(mac_address)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in disconnect: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/bluetooth/connected', methods=['GET'])
def get_connected_devices():
    """Endpoint untuk mendapatkan daftar perangkat terhubung"""
    status = bluetooth_simulator.get_status()
    return jsonify({
        "status": "success",
        "data": {
            "connected_devices": status["connected_devices"],
            "count": status["connected_count"]
        }
    })

@app.route('/api/bluetooth/health', methods=['GET'])
def health_check():
    """Endpoint untuk health check"""
    return jsonify({
        "status": "ok",
        "service": "bluetooth-simulator",
        "timestamp": datetime.now().isoformat(),
        "device": bluetooth_simulator.device_name
    })

# Root endpoint
@app.route('/')
def index():
    """Halaman utama"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bluetooth Simulator API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            .endpoint { background: #f4f4f4; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { display: inline-block; padding: 5px 10px; border-radius: 3px; color: white; font-weight: bold; }
            .get { background: #4CAF50; }
            .post { background: #2196F3; }
            .url { font-family: monospace; background: #e0e0e0; padding: 2px 5px; }
        </style>
    </head>
    <body>
        <h1>📡 Bluetooth Simulator API</h1>
        <p>Server berjalan dan siap menerima koneksi dari Ionic frontend.</p>
        
        <div class="endpoint">
            <span class="method get">GET</span> <span class="url">/api/bluetooth/status</span>
            <p>Mendapatkan status Bluetooth saat ini</p>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span> <span class="url">/api/bluetooth/discover</span>
            <p>Memulai discovery perangkat Bluetooth</p>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span> <span class="url">/api/bluetooth/connect</span>
            <p>Menghubungkan ke perangkat Bluetooth tertentu</p>
            <p><strong>Body:</strong> <code>{"mac_address": "AA:BB:CC:DD:EE:FF"}</code></p>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span> <span class="url">/api/bluetooth/disconnect</span>
            <p>Memutuskan koneksi dari perangkat</p>
            <p><strong>Body:</strong> <code>{"mac_address": "AA:BB:CC:DD:EE:FF"}</code></p>
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span> <span class="url">/api/bluetooth/connected</span>
            <p>Mendapatkan daftar perangkat yang terhubung</p>
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span> <span class="url">/api/bluetooth/health</span>
            <p>Health check endpoint</p>
        </div>
        
        <hr>
        <h3>Informasi Koneksi Ionic:</h3>
        <p>Di Ionic frontend, set <code>API_BASE_URL</code> ke:</p>
        <code>http://[IP-KOMPUTER-IN]:8000</code>
        
        <p><strong>Contoh:</strong></p>
        <ul>
            <li>Jika Ionic di localhost: <code>http://localhost:8000</code></li>
            <li>Jika Ionic di emulator: <code>http://10.0.2.2:8000</code> (Android)</li>
            <li>Jika Ionic di device: <code>http://[IP-KOMPUTER]:8000</code></li>
        </ul>
        
        <p><em>Server berjalan di port 8000 dengan CORS enabled.</em></p>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("=" * 60)
    print("BLUETOOTH SIMULATOR SERVER")
    print("=" * 60)
    print(f"Device Name: {bluetooth_simulator.device_name}")
    print(f"MAC Address: {bluetooth_simulator.mac_address}")
    print(f"IP Address: {socket.gethostbyname(socket.gethostname())}")
    print(f"Port: 8000")
    print("\nAvailable endpoints:")
    print("  GET  /api/bluetooth/status")
    print("  POST /api/bluetooth/discover")
    print("  POST /api/bluetooth/connect")
    print("  POST /api/bluetooth/disconnect")
    print("  GET  /api/bluetooth/connected")
    print("  GET  /api/bluetooth/health")
    print("\nServer starting...")
    print("=" * 60)
    
    # Jalankan server Flask
    app.run(host='0.0.0.0', port=8000, debug=False)