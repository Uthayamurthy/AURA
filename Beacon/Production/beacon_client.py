import os
import sys
import time
import json
import paho.mqtt.client as mqtt
import btmgmt

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost") 
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
ROOM_ID = os.getenv("ROOM_ID", "CSE A") # This will change depending on the class

COMMAND_TOPIC = f"aura/beacons/AURA_{ROOM_ID}/commands"

class Beacon:
    def __init__(self, uuid, max_payload_length=23, debug=False):
        self.uuid = uuid
        self.max_payload_length = max_payload_length
        self.debug = debug
        self.data_buffer = '' # Save Data Temporarily till Broadcast
    
    def debug_msg(self, msg):
        '''
        Prints msg only if debug is enabled !
        '''
        if self.debug:
            print(f"[Beacon] {msg}")

    def broadcast(self):
        '''
        Broadcasts the data in buffer after prepending the length, uuid type and uuid of the broadcast.
        '''
        self.debug_msg('Starting Broadcast ...')
        length = len(self.data_buffer)//2 # Length in Bytes (Every two character in hex takes up a byte !!)
        payload = f'{length:02x}{self.data_buffer}' # Prepend the Length to payload
        self.debug_msg(f'Payload : {payload}\nLength: {length} Bytes')
        
        # Using the library's command_str method
        response = btmgmt.command_str('add-adv', '-u', 'FEAA', '-d', payload,  '-g',  '1')
        self.debug_msg(f'Broadcast Response : {response}')

    def stop_broadcast(self):
        '''
        Clears Broadcast and resets the data buffer
        '''
        self.debug_msg('Stopping Broadcast ...')
        self.data_buffer = ''
        response = btmgmt.command_str('clr-adv')
        self.debug_msg(f'Stop Broadcast Response : {response}')

    def add_data(self, data, type='unicode-text'):
        '''
        Adds data to the data buffer based on type.
        '''
        supported_types = ('unicode-text', 'raw')

        if type not in supported_types:
            raise ValueError(f'Unsupported Type: Type must be : {supported_types}')

        if self.max_payload_length > ((len(self.data_buffer) + len(data)) // 2):
            if type == 'unicode-text':
                self.data_buffer += self.hexify(data)
            elif type == 'raw':
                self.data_buffer += data
            self.debug_msg(f'Added Data ! Buffer is now : {self.data_buffer}')
        else:
            raise ValueError(f'Payload Length Exceeded Set Limit : {self.max_payload_length}')

    def hexify(self, data):
        '''
        Converts the data to unicode and then hex.
        '''
        return ''.join('{:02x}'.format(ord(c)) for c in data)

beacon = Beacon('feaa', debug=True)

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
            code = payload.get("code")
            if code:
                print(f"Received Broadcast Command for Code: {code}")
                
                # 1. Stop any existing broadcast to be clean
                beacon.stop_broadcast()
                
                # 2. Add Eddystone Common Header (from your example.py)
                beacon.add_data('16feaa', 'raw') 
                
                # 3. Add the Code
                beacon.add_data(code, 'unicode-text')
                
                # 4. Blast it!
                beacon.broadcast()
            else:
                print("Received broadcast command but no code provided.")
                
        elif command == "stop":
            print("Received Stop Command")
            beacon.stop_broadcast()
            
    except json.JSONDecodeError:
        print(f"Invalid JSON received: {msg.payload}")
    except Exception as e:
        print(f"Error processing message: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    if os.geteuid() != 0:
        print("⚠️  WARNING: This script requires root privileges to control Bluetooth hardware.")
        print("   Please run with 'sudo python3 beacon_client.py'")
        time.sleep(2)

    print(f"--- AURA Beacon Client ({ROOM_ID}) ---")
    
    # Ensure clean state on startup
    try:
        beacon.stop_broadcast()
    except Exception as e:
        print(f"Startup cleanup warning: {e}")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        try:
            beacon.stop_broadcast()
        except:
            pass
        client.disconnect()
    except Exception as e:
        print(f"Fatal Error: {e}")
        try:
            beacon.stop_broadcast()
        except:
            pass