import json
import paho.mqtt.publish as publish
from app.core.config import settings

def send_beacon_command(command: str, classroom_id: str, duration_minutes: int = 5, session_id: int = None):
    """
    Sends a command to the Beacon Controller via MQTT.
    """
    payload = {
        "command": command,
        "classroom_id": classroom_id,
        "duration_minutes": duration_minutes,
        "session_id": session_id
    }
    
    try:
        publish.single(
            settings.MQTT_SERVER_COMMAND_TOPIC,
            payload=json.dumps(payload),
            hostname=settings.MQTT_BROKER_HOST,
            port=settings.MQTT_BROKER_PORT
        )
        print(f"MQTT Command Sent: {payload}")
    except Exception as e:
        print(f"Error sending MQTT command: {e}")
        raise e # We raise the exception so that the professor router can handle it appropriately
