### Stuff you need to start and setup before you work on the app
#### 1. Backend Server
In a new Terminal instance, Go to Server directory and run uv sync once:
```bash
cd Server
uv sync
```

Now, start the backend Server:
```bash
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
#### 2. Beacon Controller Bridge
In a new Terminal instance, Go to Server/beacon_controller directory
```bash
cd Server/beacon_controller/ 
```

Run the beacon controller script:
```bash
uv run beacon_controller.py
```
#### 3. Run Frontend of professor app
In a new Terminal instance, Go to Frontend/Professor

```bash
cd Frontend/Professor 
```
Run the app
```bash
npm run dev
```

#### 4. Run Admin APP (Optional)
In a new Terminal instance, Go to Frontend/Admin

```bash
cd Frontend/Admin
```
Run the app
```bash
npm run dev
```

#### 5. Setup and Run the Beacon:
Go into Beacon/Production folder:
```bash
cd Beacon/Production
```
Create an Environment, Activate and Install Stuff:
```bash
sudo python3 -m venv .venv
source .venv/bin/activate
.venv/bin/python -m pip install btmgmt paho-mqtt
```
Run beacon_client.py file:
```bash
.venv/bin/python beacon_client.py
```

Now, go to the professor's web portal, login (prof@aura.com/pass) and then Press Start Attendance on Classroom.
Try the student sim script inside the Server folder
```bash
uv run student_sim.py
```
Start Building the app !!

### Student App Workflow Guide

The student app is a "Remote Control" for attendance. It connects the physical world (Beacon) to the digital world (Server).

#### 1. Authentication (Login)

* **Trigger:** App Launch / User Input.
* **Goal:** Obtain a JWT Bearer Token to sign future requests.
* **Endpoint:** `POST /api/v1/login/access-token`
* **Content-Type:** `application/x-www-form-urlencoded`
* **Body:**
* `username`: "john@student.com"
* `password`: "student123"


* **Response:**
```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer"
}

```


* **Action:** Save `access_token` in secure storage (Keychain/Keystore).

#### 2. Dashboard (Home Screen)

* **Trigger:** Post-login or App Resume.
* **Goal:** Check connectivity and show past stats.
* **Endpoint:** `GET /api/v1/student/my-attendance`
* **Header:** `Authorization: Bearer <token>`
* **Response:** List of past attendance records.

#### 3. Scanning & Detection (The Core Logic)

* **Trigger:** Student clicks **"Mark Attendance"** button.
* **BLE Logic:**
1. Start Bluetooth LE Scan.
2. **Filter:** Look for Manufacturer Data with ID `0xFFFF`.
3. **Parse:** Convert the hex payload to ASCII (e.g., `435345...` -> `CSE49838051`).
4. **Stop Scan:** As soon as a valid format code is found.



#### 4. Submission (The Handshake)

* **Trigger:** Valid code found.
* **Endpoint:** `POST /api/v1/student/attendance/submit`
* **Header:** `Authorization: Bearer <token>`
* **Body (JSON):**
```json
{
  "code": "CSE49838051",       // The decoded beacon string
  "device_uuid": "unique-id",  // A persistent ID for this phone (Anti-Cheat)
  "rssi": -65                  // Signal strength (Optional but good for analytics)
}

```


* **Response:**
* `200 OK`: Attendance marked.
* `403 Forbidden`: Student is in the wrong class.
* `404 Not Found`: Code is invalid or session expired.
* `401 Unauthorized`: Device ID mismatch (Student switched phones).
