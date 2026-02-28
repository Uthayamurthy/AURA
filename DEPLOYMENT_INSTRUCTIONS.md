# AURA Deployment Instructions

This guide provides detailed steps to deploy the AURA system using `systemd` for auto-starting services.

## Device Overview
- **Server Node**: Raspberry Pi 5
    - Hostname suggestion: `aura-server`
    - User: `uthayamurthy`
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
Clone the repository to your home directory.

```bash
cd /home/uthayamurthy
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
User=uthayamurthy
WorkingDirectory=/home/uthayamurthy/AURA/Server
Environment="PATH=/home/uthayamurthy/.cargo/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/uthayamurthy/.cargo/bin/uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
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
User=uthayamurthy
WorkingDirectory=/home/uthayamurthy/AURA/Server/beacon_controller
Environment="PATH=/home/uthayamurthy/.cargo/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/uthayamurthy/.cargo/bin/uv run beacon_controller.py
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

## Part 2: Frontend Deployment (Raspberry Pi 5)
Since you want to run the frontends in development mode (`npm run dev`), we will set up systemd services for them on the Server Pi.

### 1. Install Node.js and npm
Install a recent version of Node.js (e.g., v20).

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2. Install Dependencies
Navigate to each frontend directory and install dependencies.

```bash
# Admin Frontend
cd /home/uthayamurthy/AURA/Frontend/Admin
npm install

# Professor Frontend
cd /home/uthayamurthy/AURA/Frontend/Professor
npm install
```

### 3. Create Systemd Services

#### A. Admin Frontend Service (`aura-admin.service`)

Create the service file:
```bash
sudo nano /etc/systemd/system/aura-admin.service
```

Paste the following configuration. 
*Note: Vite/Next dev servers usually default to port 5173 or 3000. Ensure they don't conflict or specify ports in `package.json` scripts.*

```ini
[Unit]
Description=AURA Admin Frontend (Dev)
After=network.target

[Service]
User=uthayamurthy
WorkingDirectory=/home/uthayamurthy/AURA/Frontend/Admin
Environment="PATH=/usr/bin:/usr/local/bin"
# Host 0.0.0.0 is needed to access it from other devices
ExecStart=/usr/bin/npm run dev -- --host 0.0.0.0 --port 5173
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### B. Professor Frontend Service (`aura-professor.service`)

Create the service file:
```bash
sudo nano /etc/systemd/system/aura-professor.service
```

Paste the following configuration:

```ini
[Unit]
Description=AURA Professor Frontend (Dev)
After=network.target

[Service]
User=uthayamurthy
WorkingDirectory=/home/uthayamurthy/AURA/Frontend/Professor
Environment="PATH=/usr/bin:/usr/local/bin"
# Using port 5174 to avoid conflict with Admin
ExecStart=/usr/bin/npm run dev -- --host 0.0.0.0 --port 5174
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 4. Enable and Start Frontend Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable aura-admin aura-professor
sudo systemctl start aura-admin aura-professor
```

**Verification:**
```bash
sudo systemctl status aura-admin
sudo systemctl status aura-professor
```

---

## Part 3: Beacon Deployment (Raspberry Pi Zero 2W)

### 1. Initial Setup & Dependencies
Install Python `venv`, Git, and Bluetooth tools.

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip git bluez bluez-tools
```

### 2. Setup Application Code
Clone the repository.

```bash
cd /home/uthayamurthy
git clone https://github.com/uthayamurthy/AURA.git
cd AURA/Beacon/Production
```

### 3. Create Virtual Environment
Create a virtual environment inside the beacon folder.

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
> **Missing `btmgmt` dependency**: The script imports `btmgmt`. Ensure you have the `btmgmt.py` wrapper file available in the directory.

### 4. Create Systemd Service (`aura-beacon.service`)
This service needs to run with root privileges (`sudo`) to control the Bluetooth hardware.

**Prerequisite:** Determine your Server's IP address.

Create the service file:
```bash
sudo nano /etc/systemd/system/aura-beacon.service
```

Paste the following configuration (Adjust `User` if you are using a different user on the Pi Zero, e.g., `pi`):

```ini
[Unit]
Description=AURA Beacon Client
After=network.target bluetooth.target

[Service]
Type=simple
# Runs as root to allow low-level Bluetooth control
User=root
WorkingDirectory=/home/uthayamurthy/AURA/Beacon/Production
# Environment Variables
Environment="MQTT_BROKER=YOUR_SERVER_IP_HERE"
Environment="ROOM_ID=YOUR_ROOM_ID_HERE"
# ExecStart points to the python executable INSIDE the venv
ExecStart=/home/uthayamurthy/AURA/Beacon/Production/.venv/bin/python beacon_client.py
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
