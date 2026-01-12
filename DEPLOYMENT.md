# AURA Deployment Guide

This guide details the steps to deploy the AURA system on Raspberry Pi hardware running **Raspberry Pi OS Lite (Trixie)**.

> [!NOTE]
> *   **Server Node**: Raspberry Pi 5 (Runs Mosquitto, API Server, Beacon Controller)
> *   **Beacon Node**: Raspberry Pi Zero 2W (Runs Beacon Client)
> *   **Networking**: Both devices must be on the same local network, or the Beacon Node must be able to reach the Server Node's IP.

---

## 1. Server Deployment (Raspberry Pi 5)

### 1.1. System Preparation
Update the system and install essential tools.
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl vnstat ufw
```

### 1.2. Install and Configure Mosquitto (MQTT Broker)
Mosquitto acts as the communication bridge between the Beacon and the Server.

1.  **Install Mosquitto**:
    ```bash
    sudo apt install -y mosquitto mosquitto-clients
    ```

2.  **Configure for Remote Access**:
    By default, Mosquitto only allows local connections. We need to enable listening on all interfaces and (for this setup) allow anonymous access.
    
    Create a new config file:
    ```bash
    sudo nano /etc/mosquitto/conf.d/external.conf
    ```
    
    Add the following lines:
    ```text
    listener 1883
    allow_anonymous true
    ```

3.  **Restart Service**:
    ```bash
    sudo systemctl restart mosquitto
    sudo systemctl enable mosquitto
    ```

> [!IMPORTANT]
> **Security Warning**: `allow_anonymous true` is for development/internal use. For production, configuring username/password authentication is highly recommended.

### 1.3. Install `uv` (Python Package Manager)
We use `uv` for fast Python dependency management.
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

### 1.4. Application Setup
1.  **Clone the Repository**:
    ```bash
    # Replace with your actual repo URL if different
    git clone https://github.com/your-username/AURA.git
    cd AURA/Server
    ```

2.  **Install Dependencies**:
    ```bash
    uv sync
    ```

3.  **Run the API Server**:
    For deployment, we'll listen on `0.0.0.0` to allow external access (e.g., from the Student App).
    ```bash
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
    ```

4.  **Run the Beacon Controller Bridge**:
    Open a new terminal session (or use `tmux`/`screen`).
    ```bash
    cd ~/AURA/Server
    uv run beacon_controller/beacon_controller.py
    ```
    *Ensure `config.json` in `server/beacon_controller` points to `localhost` for the MQTT broker.*

---

## 2. Beacon Deployment (Raspberry Pi Zero 2W)

### 2.1. System Preparation
Update system and install Bluetooth and Python dependencies.
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-full python3-pip git bluez bluez-tools
```

### 2.2. Bluetooth Configuration
Ensure the Bluetooth service is running and enabled.
```bash
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```

### 2.3. Application Setup
1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/your-username/AURA.git
    cd AURA/Beacon/Production
    ```

2.  **Setup Virtual Environment**:
    We'll use a standard `venv` here since resource constraints on the Zero might make full `uv` syncing heavier (optional, `uv` works on Pi Zero too if preferred).
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Python Libraries**:
    ```bash
    pip install btmgmt paho-mqtt
    ```

### 2.4. Run the Beacon Client
The beacon client requires **root privileges** to control the Bluetooth hardware directly for raw advertising.

1.  **Find Server IP**:
    On your Pi 5 (Server), run `hostname -I` to get its IP address (e.g., `192.168.1.100`).

2.  **Run the Client**:
    ```bash
    # Replace with your Server's IP and appropriate Room ID
    export MQTT_BROKER="192.168.1.100"
    export ROOM_ID="CSELH49"
    
    sudo -E .venv/bin/python beacon_client.py
    ```
    *(The `-E` flag preserves the environment variables for sudo)*

---

## 3. Creating Systemd Services (Optional - For Auto-start)

To have these run automatically on boot, create systemd service files.

**Example: Beacon Service (On Pi Zero)**
1.  Create file: `/etc/systemd/system/aura-beacon.service`
2.  Content:
    ```ini
    [Unit]
    Description=AURA Beacon Client
    After=network.target bluetooth.target

    [Service]
    Type=simple
    User=root
    WorkingDirectory=/home/pi/AURA/Beacon/Production
    Environment="MQTT_BROKER=192.168.1.100"
    Environment="ROOM_ID=CSELH49"
    ExecStart=/home/pi/AURA/Beacon/Production/.venv/bin/python beacon_client.py
    Restart=always
    RestartSec=5

    [Install]
    WantedBy=multi-user.target
    ```
3.  Enable it:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable aura-beacon
    sudo systemctl start aura-beacon
    ```
