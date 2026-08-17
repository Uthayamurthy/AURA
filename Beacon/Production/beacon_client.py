import os
import sys
import time
import json
import threading
from pathlib import Path
import paho.mqtt.client as mqtt
import btmgmt

# Automatically load .env file if present in the same folder
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost") 
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
ROOM_ID = os.getenv("ROOM_ID", "CSELH51") 

COMMAND_TOPIC = f"aura/beacons/AURA_{ROOM_ID}/commands"
HEALTH_TOPIC = f"aura/devices/beacon/{ROOM_ID}/health"

class Beacon:
    def __init__(self, debug=False):
        self.debug = debug
        self.data_buffer = '' 

    def setup(self):
        '''
        Ensures the Bluetooth Controller is Powered ON and LE is enabled.
        '''
        self.debug_msg('Setting up Bluetooth Controller...')
        
        # 1. Power On the Controller
        # equivalent to: sudo btmgmt power on
        resp_power = btmgmt.command_str('power', 'on')
        self.debug_msg(f'Power On Response: {resp_power}')
        
        # 2. Enable Low Energy
        # equivalent to: sudo btmgmt le on
        resp_le = btmgmt.command_str('le', 'on')
        self.debug_msg(f'LE On Response: {resp_le}')
    
    def debug_msg(self, msg):
        if self.debug:
            print(f"[Beacon] {msg}")

    def hexify(self, data):
        '''Converts string to hex'''
        return ''.join('{:02x}'.format(ord(c)) for c in data)

    def broadcast(self):
        '''
        Broadcasts whatever is in data_buffer as a Manufacturer Specific Advertisement.
        buffer should ALREADY contain: Length + Type + CompanyID + Data
        '''
        self.debug_msg('Starting Broadcast ...')
        
        # We use -d for "data" and pass the raw hex string directly
        # -g 1 sets it to "General Discoverable"
        payload = self.data_buffer
        
        if not payload:
            print("Error: Buffer empty, nothing to broadcast.")
            return

        # Note: We removed '-u FEAA' because we are not using a Service UUID anymore
        response = btmgmt.command_str('add-adv', '-d', payload, '-g', '1')
        self.debug_msg(f'Broadcast Response : {response}')

    def stop_broadcast(self):
        self.debug_msg('Stopping Broadcast ...')
        self.data_buffer = ''
        response = btmgmt.command_str('clr-adv')
        self.debug_msg(f'Stop Response : {response}')


beacon = Beacon(debug=True)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"Connected to MQTT Broker @ {MQTT_BROKER}")
        client.subscribe(COMMAND_TOPIC)
        print(f"Listening on: {COMMAND_TOPIC}")
    else:
        print(f"Failed to connect. Return code: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        command = payload.get("command")
        
        if command == "broadcast":
            code = payload.get("code") # Expecting "CSE49123456"
            if code:
                print(f"Received Code: {code}")
                
                # 1. Clean slate
                beacon.stop_broadcast()
                
                # 2. Build the Packet
                # We want the air packet to look like:
                # [Length 1B] [Type 1B] [Company ID 2B] [Data NB]
                
                # Convert our string code to Hex
                code_hex = beacon.hexify(code)
                
                # Constants
                # Type 0xFF = Manufacturer Specific Data
                # Company ID 0xFFFF = Reserved for Testing (Perfect for us)
                header_type = "ff"
                company_id = "ffff"
                
                # Calculate Length
                # Length = 1 byte (Type) + 2 bytes (Company ID) + N bytes (Code)
                # Note: The 'Length' byte itself is NOT included in the count usually in this specific raw format context, 
                # but standard BLE packets usually structure it as [Len, Type, Value].
                # btmgmt 'add-adv -d' expects the full sequence.
                
                data_len_int = 1 + 2 + len(code)
                len_hex = f'{data_len_int:02x}'
                
                # Construct Full Payload
                # Example: 0effffff435345...
                full_payload = len_hex + header_type + company_id + code_hex
                
                # 3. Load and Fire
                beacon.data_buffer = full_payload
                beacon.broadcast()
            else:
                print("Broadcast command missing 'code'")
                
        elif command == "stop":
            print("Stopping...")
            beacon.stop_broadcast()
            
    except json.JSONDecodeError:
        print(f"Invalid JSON: {msg.payload}")
    except Exception as e:
        print(f"Error: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    if os.geteuid() != 0:
        print("⚠️  WARNING: This script requires root privileges to control Bluetooth hardware.")
        print("   Please run with 'sudo python3 beacon_client.py'")
        time.sleep(2)

    print(f"--- AURA Beacon Client ({ROOM_ID}) ---")
    
    try:
        beacon.setup()
    except Exception as e:
        print(f"⚠️ Setup failed: {e}")
        # We continue anyway, as it might already be on.

    # Ensure clean state on startup
    try:
        beacon.stop_broadcast()
    except Exception as e:
        print(f"Startup cleanup warning: {e}")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    # Start health heartbeat thread
    health_stop = threading.Event()
    def health_worker():
        """Publishes a heartbeat every 5 seconds."""
        while not health_stop.is_set():
            try:
                client.publish(HEALTH_TOPIC, json.dumps({
                    "status": "online", "device_id": ROOM_ID
                }), qos=0)
            except Exception:
                pass
            health_stop.wait(5)

    health_thread = threading.Thread(target=health_worker, daemon=True)
    health_thread.start()
    print(f"Health heartbeat started (every 5s) on: {HEALTH_TOPIC}")

    print(f"Connecting to MQTT broker at '{MQTT_BROKER}:{MQTT_PORT}'...")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        health_stop.set()
        try:
            beacon.stop_broadcast()
        except:
            pass
        client.loop_stop()
        client.disconnect()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal Connection Error: {e}")
        print(f"   Please verify that MQTT_BROKER='{MQTT_BROKER}' in .env is a reachable IP address of your Server Pi.")
        health_stop.set()
        try:
            beacon.stop_broadcast()
        except:
            pass