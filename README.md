# AURA

**Attendance Using Realtime Authentication** - A smart classroom attendance system using Bluetooth Low Energy (BLE) beacons.

## Project Overview

Beacons are physical hardware devices (based on ESP32 or similar) deployed in classrooms. They broadcast a time-limited, rotating code.
Students' mobile devices detect these beacons and submit the code to the server to verify their physical presence in the classroom.
Professors and Admins have web portals to manage the system.

## Directory Structure

### [Server](Server/)
The backbone of the AURA system.
-   **Tech Stack**: Python, FastAPI, SQLite, Paho MQTT.
-   **Role**: Handles all API requests, authentication, and communication with Beacon Controllers via MQTT.
-   **Documentation**: [Server README](Server/README.md)

### Frontend
Web interfaces for managing the system.
-   **[Admin Portal](Frontend/Admin/)**: For system administrators to manage users, classrooms, and devices.
-   **[Professor Portal](Frontend/Professor/)**: For professors to start classes and view attendance.
-   **Tech Stack**: React, Vite, Tailwind CSS, Shadcn UI.

### [Beacon](Beacon/)
Hardware and controller verification logic.
-   **Beacon Controller**: Bridge between the physical beacons and the main server. Located at `Server/beacon_controller` but conceptually part of the hardware layer.
-   **Prototypes**: Contains prototype code for the beacon hardware.

## Quick Start

### Prerequisites
-   Python 3.13+
-   Node.js & npm
-   Mosquitto MQTT Broker

### Setup
Please verify the individual READMEs in each subdirectory for detailed setup instructions.

1.  **Server**: `cd Server` -> `uv sync` -> configure `.env` -> `uv run uvicorn app.main:app`
2.  **Frontend**: `cd Frontend/Admin` (or Professor) -> `npm install` -> `npm run dev`