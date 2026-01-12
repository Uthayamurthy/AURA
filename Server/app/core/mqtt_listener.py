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
    try:
        payload_code = msg.payload.decode("utf-8")
        topic = msg.topic
        
        # Match topic: aura/classrooms/{Composite_ID}/active_code
        match = re.search(r"aura/classrooms/(.*?)/active_code", topic)
        if not match:
            return
            
        beacon_classroom_id_str = match.group(1) # e.g., "CSE A_49" or "AURA_CSE A_49"
        
        # 1. Clean up prefix if exists
        clean_id = beacon_classroom_id_str.replace("AURA_", "") # "CSE A_49"
        
        # 2. Extract Class Name by removing the Room Number suffix
        # We split by the LAST underscore to separate Class from Room
        if "_" in clean_id:
            classroom_name, room_number = clean_id.rsplit("_", 1)
        else:
            # Fallback if no room number provided
            classroom_name = clean_id

        # Now classroom_name is "CSE A", which matches your DB!
        print(f"Received code '{payload_code}' for Class '{classroom_name}' in Room '{room_number}'")
        
        update_active_code(classroom_name, payload_code)
        
    except Exception as e:
        print(f"Error: {e}")

def update_active_code(classroom_name: str, code: str):
    """
    Updates the active session in the database with the new code.
    """
    db: Session = database.SessionLocal()
    try:
        # 1. Find ClassGroup
        class_group = db.query(models.ClassGroup).filter(models.ClassGroup.name == classroom_name).first()
        if not class_group:
            print(f"ClassGroup '{classroom_name}' not found in DB.")
            return

        # 2. Find active session
        # NEW LOGIC: Join TeachingAssignment to filter by class_group_id
        session = db.query(models.AttendanceSession).join(models.TeachingAssignment).filter(
            models.TeachingAssignment.class_group_id == class_group.id,
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