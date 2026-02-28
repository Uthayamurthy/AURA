import json
import logging
import paho.mqtt.publish as publish
from app.core.config import settings

logger = logging.getLogger(__name__)

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
        logger.info(f"MQTT Command Sent: {payload}")
    except Exception as e:
        logger.error(f"Error sending MQTT command: {e}", exc_info=True)
        raise e # We raise the exception so that the professor router can handle it appropriately
