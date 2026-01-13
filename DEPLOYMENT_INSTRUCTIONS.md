# AURA Deployment Instructions

This guide provides detailed steps to deploy the AURA system using `systemd` for auto-starting services.

## Device Overview
- **Server Node**: Raspberry Pi 5
    - Hostname suggestion: `aura-server`
    - OS: Raspberry Pi OS Lite (64-bit)
    - Runs: Mosquitto MQTT Broker, FastAPI Web Server, Beacon Controller
- **Beacon Node**: Raspberry Pi Zero 2W
    - Hostname suggestion: `aura-beacon-01`
    - OS: Raspberry Pi OS Lite (32-bit or 64-bit)
    - Runs: Beacon Client script

---

## Part 1: Server Deployment (Raspberry Pi 5)

### 1. Initial Setup & Dependencies
Update the system and install required tools.

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl ufw
```

### 2. Install & Configure Mosquitto (MQTT Broker)
The server needs an MQTT broker to communicate with beacons.

```bash
# Install Mosquitto
sudo apt install -y mosquitto mosquitto-clients

# Enable auto-start
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

**Configuration (Allow External Access):**
By default, Mosquitto assumes local-only. Create a config to allow the Beacon to connect.

```bash
sudo nano /etc/mosquitto/conf.d/aura.conf
```

Add the following content:
```text
listener 1883
allow_anonymous true
```

Restart Mosquitto:
```bash
sudo systemctl restart mosquitto
```

### 3. Install `uv`
We will use `uv` for Python package management on the server.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

### 4. Setup Application Code
Clone the repository to your home directory (assuming user is `pi`).

```bash
cd ~
git clone https://github.com/uthayamurthy/AURA.git
cd AURA/Server

# Sync dependencies
uv sync
```

### 5. Create Systemd Services
We need two services: one for the Web API (`uvicorn`) and one for the Beacon Controller.

#### A. Web API Service (`aura-web.service`)

Create the service file:
```bash
sudo nano /etc/systemd/system/aura-web.service
```

Paste the following configuration:
```ini
[Unit]
Description=AURA Web API Server
After=network.target mosquitto.service

[Service]
User=pi
WorkingDirectory=/home/pi/AURA/Server
Environment="PATH=/home/pi/.cargo/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/pi/.cargo/bin/uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### B. Beacon Controller Service (`aura-controller.service`)

Create the service file:
```bash
sudo nano /etc/systemd/system/aura-controller.service
```

Paste the following configuration. Note the working directory is set to `beacon_controller` so it can find its `config.json`.

```ini
[Unit]
Description=AURA Beacon Controller
After=network.target mosquitto.service aura-web.service

[Service]
User=pi
WorkingDirectory=/home/pi/AURA/Server/beacon_controller
Environment="PATH=/home/pi/.cargo/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/pi/.cargo/bin/uv run beacon_controller.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 6. Enable and Start Server Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable aura-web aura-controller
sudo systemctl start aura-web aura-controller
```

**Verification:**
```bash
sudo systemctl status aura-web
sudo systemctl status aura-controller
```

---

## Part 2: Beacon Deployment (Raspberry Pi Zero 2W)

### 1. Initial Setup & Dependencies
Install Python `venv`, Git, and Bluetooth tools.

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip git bluez bluez-tools
```

### 2. Setup Application Code
Clone the repository.

```bash
cd ~
git clone https://github.com/uthayamurthy/AURA.git
cd AURA/Beacon/Production
```

### 3. Create Virtual Environment
Create a virtual environment inside the beacon folder as requested.

```bash
# Create venv named .venv inside Beacon/Production
python3 -m venv .venv

# Activate and install dependencies
source .venv/bin/activate
pip install -r requirements.txt
# If requirements.txt is missing, install manually:
pip install paho-mqtt
```

> [!IMPORTANT]
> **Missing `btmgmt` dependency**: The script imports `btmgmt`, which appears to be a custom wrapper not found in the repository or standard PyPI. Ensure you have the `btmgmt.py` file or package available in the directory. If it involves system calls to `btmgmt` (from `bluez-tools`), you might need to add that wrapper script.

### 4. Create Systemd Service (`aura-beacon.service`)
This service needs to run with root privileges (`sudo`) to control the Bluetooth hardware. By setting `User=root` effectively, it runs as root.

**Prerequisite:** Determine your Server's IP address (e.g., `192.168.1.100`) and choose a Room ID (e.g., `ROOM_01`).

Create the service file:
```bash
sudo nano /etc/systemd/system/aura-beacon.service
```

Paste the following configuration:
```ini
[Unit]
Description=AURA Beacon Client
After=network.target bluetooth.target

[Service]
Type=simple
# Runs as root to allow low-level Bluetooth control
User=root
WorkingDirectory=/home/pi/AURA/Beacon/Production
# Environment Variables
Environment="MQTT_BROKER=YOUR_SERVER_IP_HERE"
Environment="ROOM_ID=YOUR_ROOM_ID_HERE"
# ExecStart points to the python executable INSIDE the venv
ExecStart=/home/pi/AURA/Beacon/Production/.venv/bin/python beacon_client.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

*> **Important**: Replace `YOUR_SERVER_IP_HERE` with the actual IP address of your Pi 5 Server.*

### 5. Enable and Start Beacon Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable aura-beacon
sudo systemctl start aura-beacon
```

**Verification:**
```bash
sudo systemctl status aura-beacon
```

You can view logs with:
```bash
journalctl -u aura-beacon -f
```
