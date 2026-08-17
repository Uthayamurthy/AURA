import machine
import time
import network
from umqtt.simple import MQTTClient

# ==========================================
#              CONFIGURATION
# ==========================================
WIFI_SSID = "AURA_SIMULATION"
WIFI_PASS = "funky_monkey"
MQTT_BROKER = "10.113.229.239"
MQTT_CLIENT_ID = "esp8266_headcount"
ROOM_ID = "LH49"  # Room where this device is installed
MQTT_TOPIC = "aura/rooms/" + ROOM_ID + "/headcount"
HEALTH_TOPIC = "aura/devices/headcount/" + ROOM_ID + "/health"
# ==========================================

# Pin definitions
pin_outside = machine.Pin(5, machine.Pin.IN)
pin_inside = machine.Pin(4, machine.Pin.IN)

count = 0

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        # Wait until connected
        while not wlan.isconnected():
            time.sleep(1)
            print(".", end="")
    print("\nWiFi Connected! IP Address:", wlan.ifconfig()[0])

def connect_mqtt():
    # Connect to the broker without username/password
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
    client.connect()
    print(f"Connected to MQTT Broker at {MQTT_BROKER}!")
    return client

# --- Initialization ---
connect_wifi()
mqtt = connect_mqtt()

# Publish the initial 0 count
mqtt.publish(MQTT_TOPIC, str(count))
mqtt.publish(HEALTH_TOPIC, '{"status":"online","room_id":"' + ROOM_ID + '"}')
print("Headcount system started. Waiting for movement...")

last_health = time.ticks_ms()

while True:
    val_out = pin_outside.value()
    val_in = pin_inside.value()

    # Case 1: Entering
    if val_out == 0 and val_in == 1:
        start_time = time.ticks_ms()
        entered = False
        
        while time.ticks_diff(time.ticks_ms(), start_time) < 2000:
            if pin_inside.value() == 0:
                entered = True
                break
            time.sleep(0.01)
            
        if entered:
            count += 1
            print(f"Someone entered! Total headcount: {count}")
            try:
                mqtt.publish(MQTT_TOPIC, str(count)) # Send updated count to Pi
            except Exception as e:
                print("MQTT publish failed, reconnecting:", e)
                try:
                    mqtt = connect_mqtt()
                    mqtt.publish(MQTT_TOPIC, str(count))
                except Exception:
                    print("Reconnect failed, will retry next event")
                
            while pin_outside.value() == 0 or pin_inside.value() == 0:
                time.sleep(0.1)
                
    # Case 2: Exiting
    elif val_in == 0 and val_out == 1:
        start_time = time.ticks_ms()
        exited = False
        
        while time.ticks_diff(time.ticks_ms(), start_time) < 2000:
            if pin_outside.value() == 0:
                exited = True
                break
            time.sleep(0.01)
            
        if exited:
            if count > 0:
                count -= 1
            print(f"Someone exited! Total headcount: {count}")
            try:
                mqtt.publish(MQTT_TOPIC, str(count)) # Send updated count to Pi
            except Exception as e:
                print("MQTT publish failed, reconnecting:", e)
                try:
                    mqtt = connect_mqtt()
                    mqtt.publish(MQTT_TOPIC, str(count))
                except Exception:
                    print("Reconnect failed, will retry next event")
                
            while pin_outside.value() == 0 or pin_inside.value() == 0:
                time.sleep(0.1)

    # --- Health Heartbeat (every 5 seconds) ---
    if time.ticks_diff(time.ticks_ms(), last_health) > 5000:
        try:
            mqtt.publish(HEALTH_TOPIC, '{"status":"online","room_id":"' + ROOM_ID + '"}')
        except Exception:
            pass  # Don't disrupt sensor loop for heartbeat failures
        last_health = time.ticks_ms()

    time.sleep(0.05)
