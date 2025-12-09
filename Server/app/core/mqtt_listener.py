import paho.mqtt.client as mqtt_client
import threading
import json
from app.core.config import settings
from app.core import database
from app import models
from sqlalchemy.orm import Session
import re

# Topic pattern to match: aura/classrooms/{classroom_id}/active_code
TOPIC_PATTERN = "aura/classrooms/+/active_code"

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("MQTT Listener connected.")
        client.subscribe(TOPIC_PATTERN)
        print(f"Subscribed to {TOPIC_PATTERN}")
    else:
        print(f"Failed to connect to MQTT broker, return code {rc}")

def on_message(client, userdata, msg):
    """
    Callback when a message is received.
    Message payload should be the active code (string).
    Topic contains the classroom_id.
    """
    try:
        payload_code = msg.payload.decode("utf-8")
        topic = msg.topic
        
        # Extract classroom_id from topic
        # Topic: aura/classrooms/{classroom_id}/active_code
        match = re.search(r"aura/classrooms/(.*?)/active_code", topic)
        if not match:
            print(f"Ignoring topic format: {topic}")
            return
            
        beacon_classroom_id_str = match.group(1) # e.g. "AURA_CSC2" or just "CSC2"
        
        # Note: In config.json from beacon_controller, it says:
        # "beacon_topic": "aura/beacons/AURA_CSC2/commands",
        # "classroom_topic": "aura/classrooms/AURA_CSC2/active_code"
        # And "classroom_id": "CSC2"
        # SO the ID in the URL is likely "AURA_CSC2", but our DB ClassGroup might check "CSC2".
        # We need to map this back. 
        # For simplicity, let's assume ClassGroup.name matches the ID in the topic 
        # OR we strip "AURA_" prefix if present.
        
        classroom_name = beacon_classroom_id_str.replace("AURA_", "")
        
        print(f"Received code '{payload_code}' for classroom '{classroom_name}'")
        
        update_active_code(classroom_name, payload_code)
        
    except Exception as e:
        print(f"Error processing MQTT message: {e}")

def update_active_code(classroom_name: str, code: str):
    """
    Updates the active session in the database with the new code.
    """
    db: Session = database.SessionLocal()
    try:
        # Find the ClassGroup by name
        class_group = db.query(models.ClassGroup).filter(models.ClassGroup.name == classroom_name).first()
        if not class_group:
            # print(f"ClassGroup '{classroom_name}' not found in DB.")
            return

        # Find active session for this class
        session = db.query(models.AttendanceSession).filter(
            models.AttendanceSession.class_group_id == class_group.id,
            models.AttendanceSession.is_active == True
        ).order_by(models.AttendanceSession.start_time.desc()).first()
        
        if session:
            session.current_code = code
            db.commit()
            print(f"Updated session {session.id} code to: {code}")
        else:
             print(f"No active session found for {classroom_name}")

    except Exception as e:
        print(f"DB Error updating code: {e}")
    finally:
        db.close()

def start_mqtt_listener():
    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 60)
        client.loop_start()
        print("MQTT Listener background thread started.")
        return client
    except Exception as e:
        print(f"Could not start MQTT Listener: {e}")
        return None
