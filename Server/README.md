# Aura Server
> It is expected to run on a Raspberry Pi 5 ... Docs also available to run on a developer's machine (Arch Linux)

## Different Components of the Server and it's Uses
### Beacon Controller
Beacon controller is a dedicated background process that runs in the background. It acts as a bridge between the main aura server process and the beacon. The main server needs to send a json load in the form of string encoded json like:
```json
{"command": "start_session", "classroom_id": "CSC2", "duration_minutes": 2}
```
to a specific command topic. It then activates code publishing to that specific beacon once in every 30 seconds for the mentioned duration of time.

### Aura Server (Not Yet Implemented)
This is the main server process that is responsible for communication between the mobile devices, prof's web app and admin's web app.
It also can communicate with the beacon controller

## Installation Instructions
### General
- Cd into Server Directory
```bash
cd Server
```
- Make sure uv package manager is installed in your system and install dependencies by:
```bash
uv sync
```

### Beacon Controller
- Install and Configire Mosquitto Mqtt Broker on your system
- Create a **config.json** file and add the necessary details. Here is an example version:
```json
{
  "mqtt_broker": {
    "host": "localhost",
    "port": 1883
  },
  "server_command_topic": "aura/server/commands",
  "classrooms": {
    "CSC2": {
      "beacon_id": "AURA_CSC2",
      "beacon_topic": "aura/beacons/AURA_CSC2/commands",
      "classroom_topic": "aura/classrooms/AURA_CSC2/active_code"
    }
  }
}
```

## Running Instructions
### Beacon Controller
- Change to the **beacon_controller** directory:
```bash
cd beacon_controller
```
- Run the *beacon_controller.py* script:
```bash
uv run beacon_controller.py
```