# Headcount Device - Prototype 1

This folder contains the MicroPython script (`main.py`) for the Headcount device running on an ESP8266 (NodeMCU).

## Purpose
The device tracks people entering and exiting a room using two IR (infrared) sensors. It connects to Wi-Fi and publishes the current headcount to an MQTT broker (Mosquitto) running on a Raspberry Pi.

## MQTT Topic Convention

The device publishes to:
```
aura/rooms/{ROOM_ID}/headcount
```

This follows the AURA project's topic hierarchy:
- `aura/server/commands` — Server → Beacon Controller
- `aura/classrooms/{classroom_id}/active_code` — Beacon Controller → Server
- `aura/beacons/{beacon_id}/commands` — Beacon Controller → Hardware
- **`aura/rooms/{room_id}/headcount`** — Headcount Device → Server

The `ROOM_ID` (e.g., `LH49`) matches the room number format used across all AURA devices.

## Physical Connections (ESP8266 to IR Sensors)

### IR Sensor 1 (Outside — placed just outside the entrance)
- **VCC:** Connected to a **3V3** pin on the ESP8266
- **GND:** Connected to a **GND** pin on the ESP8266
- **OUT:** Connected to the **D1** pin (GPIO 5) on the ESP8266

### IR Sensor 2 (Inside — placed just inside the entrance)
- **VCC:** Connected to another **3V3** pin on the ESP8266
- **GND:** Connected to another **GND** pin on the ESP8266
- **OUT:** Connected to the **D2** pin (GPIO 4) on the ESP8266

## Configuration

Edit the following variables at the top of `main.py`:

| Variable | Description | Example |
|----------|-------------|---------|
| `WIFI_SSID` | Wi-Fi network name | `"AURA_SIMULATION"` |
| `WIFI_PASS` | Wi-Fi password | `"funky_monkey"` |
| `MQTT_BROKER` | Raspberry Pi IP address | `"10.113.229.239"` |
| `ROOM_ID` | Room where the device is installed | `"LH49"` |

## Requirements
- ESP8266 flashed with MicroPython
- `umqtt.simple` library (included with standard ESP8266 MicroPython builds)
- 2x FC-51 or MH-B IR Obstacle Avoidance Sensors
- Mosquitto MQTT broker running on the Raspberry Pi
