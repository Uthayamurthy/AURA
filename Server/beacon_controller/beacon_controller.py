import paho.mqtt.client as mqtt
import json
import time
import sys
import threading
import random
import string

# --- Global State Management ---
# This dictionary will hold our active session threads and stop signals
# We use a lock to make sure access to it is thread-safe
active_sessions = {}
session_lock = threading.Lock()

# --- Configuration Loading ---
def load_config(config_path='config.json'):
    """Reads and parses the JSON configuration file."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            print("Configuration loaded successfully.")
            return config
    except FileNotFoundError:
        print(f"FATAL: Configuration file not found at '{config_path}'")
        sys.exit(1)
    return None

# --- Session Worker Function (runs in a separate thread) ---
def session_worker(classroom_id, duration_seconds, config, client, stop_event):
    """
    Manages a single attendance session, generating and publishing codes
    in a loop until duration is over or a stop signal is received.
    """
    print(f"[Session {classroom_id}]: Starting for {duration_seconds} seconds.")
    
    classroom_config = config['classrooms'][classroom_id]
    beacon_topic = classroom_config['beacon_topic']
    classroom_topic = classroom_config['classroom_topic']
    
    end_time = time.time() + duration_seconds
    
    # The main loop for the session
    while time.time() < end_time and not stop_event.is_set():
        # 1. Generate a new 6-character random code
        new_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # 2. Publish to the beacon
        beacon_payload = json.dumps({"command": "broadcast", "code": new_code})
        client.publish(beacon_topic, beacon_payload, qos=1)
        
        # 3. Publish to the server-side classroom topic
        client.publish(classroom_topic, new_code, qos=1, retain=True)
        
        print(f"[Session {classroom_id}]: Published new code '{new_code}'.")
        
        # Wait 30 seconds, but check for the stop signal every second
        stop_event.wait(30)

    # --- Cleanup after the loop ends ---
    print(f"[Session {classroom_id}]: Session finished. Sending stop command.")
    
    # Tell the beacon to stop broadcasting
    stop_payload = json.dumps({"command": "stop"})
    client.publish(beacon_topic, stop_payload, qos=1)
    
    # Clear the retained message on the server topic
    client.publish(classroom_topic, "", qos=1, retain=True)

    # Remove self from the active sessions dictionary (thread-safe)
    with session_lock:
        if classroom_id in active_sessions:
            del active_sessions[classroom_id]

# --- MQTT Callback Functions ---
def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        command_topic = userdata['server_command_topic']
        print(f"Connected to MQTT Broker!")
        client.subscribe(command_topic)
        print(f"Subscribed to server command topic: '{command_topic}'")

def on_message(client, userdata, msg):
    """
    Handles incoming commands from the FastAPI server.
    """
    if msg.topic != userdata['server_command_topic']:
        return

    print(f"\nReceived command: {msg.payload.decode()}")
    try:
        command_data = json.loads(msg.payload.decode())
        command = command_data.get("command")
        classroom_id = command_data.get("classroom_id")

        if not command or not classroom_id:
            print("  [ERROR] Command is missing 'command' or 'classroom_id'.")
            return

        with session_lock:
            # --- START A NEW SESSION ---
            if command == "start_session":
                if classroom_id in active_sessions:
                    print(f"  [WARNING] Session for '{classroom_id}' is already active. Ignoring start command.")
                    return

                duration = command_data.get("duration_minutes", 5) * 60
                stop_event = threading.Event()
                
                thread = threading.Thread(
                    target=session_worker,
                    args=(classroom_id, duration, userdata, client, stop_event)
                )
                
                active_sessions[classroom_id] = {"thread": thread, "stop_event": stop_event}
                thread.start()
                print(f"  -> Started new session thread for '{classroom_id}'.")

            # --- STOP AN EXISTING SESSION ---
            elif command == "stop_session":
                if classroom_id in active_sessions:
                    print(f"  -> Sending stop signal to session '{classroom_id}'.")
                    active_sessions[classroom_id]["stop_event"].set()
                else:
                    print(f"  [WARNING] No active session found for '{classroom_id}' to stop.")

    except Exception as e:
        print(f"  [ERROR] Could not process command. Error: {e}")


# --- Main Execution ---
if __name__ == "__main__":
    config = load_config()
    if not config:
        sys.exit(1)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata=config)
    client.on_connect = on_connect
    client.on_message = on_message

    broker = config['mqtt_broker']
    client.connect(broker['host'], broker['port'], 60)

    try:
        print("Starting MQTT bridge controller. This will manage attendance sessions.")
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nShutting down controller... stopping all active sessions.")
        with session_lock:
            for session in active_sessions.values():
                session["stop_event"].set()
        # Give threads a moment to clean up
        time.sleep(2) 
        client.disconnect()