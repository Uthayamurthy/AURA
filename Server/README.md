# Aura Server
> It is expected to run on a Raspberry Pi 5. Docs also available to run on a developer's machine (Arch Linux).

## Different Components of the Server and its Uses
### Beacon Controller
The Beacon Controller is a dedicated background process. It acts as a bridge between the main aura server process and the physical beacons. The main server sends a JSON payload to a specific command topic, for example:
```json
{"command": "start_session", "classroom_id": "CSC2", "duration_minutes": 2}
````

The controller then activates code publishing to that specific beacon once every 30 seconds for the specified duration.

### Aura Server

This is the main server process (FastAPI) responsible for communication between mobile devices, the professor's web app, and the admin's web app. It manages authentication, attendance records, and communicates with the beacon controller.

## Installation Instructions

### General

1.  Change into the Server directory:

```bash
cd Server
```

2.  Make sure the uv package manager is installed on your system, then install dependencies:

```bash
uv sync
```

3.  **Configuration (.env)**:
    You must create a .env file in the Server directory to configure the application. This file must contain a secure secret key for authentication.

    Generate a key using Python:

    ```bash
    python -c "import secrets; print(secrets.token_hex(32))"
    ```

    Create a file named `.env` and add the following:

    ```bash
    SECRET_KEY=your_generated_key_here
    BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:8000"]
    DATABASE_URL=sqlite:///./aura.db
    ```

### Beacon Controller

1.  Install and Configure the Mosquitto MQTT Broker on your system.

2.  Create a **config.json** file inside the `beacon_controller` directory and add the necessary details. Example:

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

### Seed Test Data

Before running the server, you should seed the database with test data. This creates a default Admin, Professor, and Student account.

```bash
uv run seed_test_data.py
```

### Default Credentials

These are the accounts created by the seed script.

| Role      | Username / Email    | Password     | Device ID (if applicable) |
|-----------|---------------------|--------------|---------------------------|
| Admin     | admin               | admin        | N/A                       |
| Professor | prof@aura.com       | pass         | N/A                       |
| Student   | john@student.com    | student123   | device-uuid-123           |

> **Warning**: These credentials are for testing ONLY. We need to change this in production

### Running the System

You need to run the MQTT broker, the Beacon Controller, and the Main Server simultaneously.

1.  **Start the Beacon Controller**:
    Open a terminal, change to the beacon controller directory, and run the script:

    ```bash
    cd beacon_controller
    uv run beacon_controller.py
    ```

2.  **Start the Main Server**:
    Open a separate terminal in the `Server` directory and start the FastAPI app:

    ```bash
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```

### Verification

You can verify the entire flow (Login -\> Start Session -\> Submit Attendance) using the included test script. This script simulates the beacon hardware to test the API logic.

Ensure the server is running, then execute:

```bash
uv run verify_system.py
```

> *Note:* For sake of simplicity, beacon controller is not necessary for this. This script simulates the beacon controller and publishes a hardcoded code to check if everything is working.