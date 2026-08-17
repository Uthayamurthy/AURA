/*
 * AURA Auxiliary BLE Beacon
 * Hardware: ESP8266 (NodeMCU) + HM-10 BLE Module
 *
 * Configures the HM-10 as an iBeacon that broadcasts continuously.
 * The ESP8266 sends AT commands over SoftwareSerial to set up the HM-10,
 * then the HM-10 handles all BLE broadcasting independently.
 *
 * Wiring:
 *   HM-10 TXD → D5 (GPIO14)
 *   HM-10 RXD → D6 (GPIO12)
 *   HM-10 VCC → 3V3
 *   HM-10 GND → GND
 */

#include <SoftwareSerial.h>

// --- Pin Definitions ---
#define HM10_RX_PIN D5 // ESP8266 receives on this pin (connect to HM-10 TXD)
#define HM10_TX_PIN D6 // ESP8266 transmits on this pin (connect to HM-10 RXD)

SoftwareSerial hm10(HM10_RX_PIN, HM10_TX_PIN);

// --- Beacon Configuration ---
// Change these to give each auxiliary beacon a unique identity!

// iBeacon UUID (split into 4 chunks for AT commands)
// Default: 74278BDA-B644-4520-8F0C-720EAF059935 (Example AURA UUID)
#define BEACON_UUID_0 "74278BDA"
#define BEACON_UUID_1 "B6444520"
#define BEACON_UUID_2 "8F0C720E"
#define BEACON_UUID_3 "AF059935"

// Major: Use this to identify the ROOM (e.g., 0x0001 = Room 1)
#define BEACON_MAJOR "0x0001"

// Minor: Use this to identify THIS SPECIFIC BEACON within the room
// Beacon 1 (Pi Zero) = implicit, Beacon 2 = 0x0002, Beacon 3 = 0x0003
#define BEACON_MINOR "0x0002"

// Beacon Name (max 12 chars)
#define BEACON_NAME "AURA-AUX-01"

// --- Helper Functions ---

/**
 * Sends an AT command to the HM-10 and waits for a response.
 * Returns the response string.
 */
String sendATCommand(const String &command, unsigned long timeout = 1000) {
  // Clear any leftover data in the buffer
  while (hm10.available()) {
    hm10.read();
  }

  Serial.print("  >> Sending: ");
  Serial.println(command);

  hm10.print(command);

  // Wait for response
  String response = "";
  unsigned long startTime = millis();

  while (millis() - startTime < timeout) {
    if (hm10.available()) {
      char c = hm10.read();
      response += c;
      startTime = millis(); // Reset timeout on each received char
    }
  }

  response.trim();
  Serial.print("  << Response: ");
  Serial.println(response.length() > 0 ? response : "(no response)");

  return response;
}

/**
 * Sends a command and checks if the response contains an expected substring.
 */
bool sendAndVerify(const String &command, const String &expectedContains,
                   unsigned long timeout = 1000) {
  String response = sendATCommand(command, timeout);
  bool success = response.indexOf(expectedContains) >= 0;
  if (!success) {
    Serial.print("  !! WARNING: Expected '");
    Serial.print(expectedContains);
    Serial.println("' in response");
  }
  return success;
}

// --- Setup ---

void setup() {
  Serial.begin(9600);
  hm10.begin(9600);

  delay(1000);

  Serial.println();
  Serial.println("===================================");
  Serial.println(" AURA Auxiliary Beacon Configurator");
  Serial.println("===================================");
  Serial.println();

  // Step 0: Test connection
  Serial.println("[1/10] Testing connection...");
  if (!sendAndVerify("AT", "OK")) {
    Serial.println("ERROR: HM-10 not responding! Check wiring.");
    Serial.println("  - Is HM-10 powered? (LED should be blinking)");
    Serial.println("  - Are TX/RX crossed correctly?");
    Serial.println("  - Try swapping D5 and D6 connections.");
    Serial.println("Halting.");
    while (true) {
      delay(1000);
    }
  }

  // Step 1: Factory reset (optional but recommended for clean state)
  Serial.println("[2/10] Factory reset...");
  sendAndVerify("AT+RENEW", "OK+RENEW", 2000);
  delay(1000);

  // Step 2: Reset module
  Serial.println("[3/10] Resetting module...");
  sendAndVerify("AT+RESET", "OK+RESET", 2000);
  delay(1000);

  // Re-test after reset
  sendAndVerify("AT", "OK");

  // Step 3: Set beacon name
  Serial.println("[4/10] Setting name...");
  sendAndVerify(String("AT+NAME") + BEACON_NAME, "OK+Set", 1000);

  // Step 4: Set iBeacon UUID
  Serial.println("[5/10] Setting UUID...");
  sendAndVerify(String("AT+IBE0") + BEACON_UUID_0, "OK+Set");
  sendAndVerify(String("AT+IBE1") + BEACON_UUID_1, "OK+Set");
  sendAndVerify(String("AT+IBE2") + BEACON_UUID_2, "OK+Set");
  sendAndVerify(String("AT+IBE3") + BEACON_UUID_3, "OK+Set");

  // Step 5: Set Major and Minor
  Serial.println("[6/10] Setting Major/Minor...");
  sendAndVerify(String("AT+MARJ") + BEACON_MAJOR, "OK+Set");
  sendAndVerify(String("AT+MINO") + BEACON_MINOR, "OK+Set");

  // Step 6: Set advertising interval
  // Values: 0=100ms, 1=152.5ms, 2=211.25ms, 3=318.75ms, 4=417.5ms
  //         5=546.25ms, 6=760ms, 7=852.5ms, 8=1022.5ms, 9=1285ms
  // Lower = faster discovery but more power. 5 is a good balance.
  Serial.println("[7/10] Setting advertising interval...");
  sendAndVerify("AT+ADVI5", "OK+Set");

  // Step 7: Set to non-connectable (saves power, pure beacon mode)
  Serial.println("[8/10] Setting non-connectable mode...");
  sendAndVerify("AT+ADTY3", "OK+Set");

  // Step 8: Enable iBeacon mode
  Serial.println("[9/10] Enabling iBeacon mode...");
  sendAndVerify("AT+IBEA1", "OK+Set");

  // Step 9: Set broadcast-only + auto-sleep for low power
  Serial.println("[10/10] Enabling low-power broadcast...");
  sendAndVerify("AT+DELO2", "OK+Set");
  sendAndVerify("AT+PWRM0", "OK+Set");

  // Final reset to apply all settings
  Serial.println();
  Serial.println("Applying settings (final reset)...");
  sendAndVerify("AT+RESET", "OK+RESET", 2000);
  delay(2000);

  // --- Done! ---
  Serial.println();
  Serial.println("============================================");
  Serial.println(" BEACON CONFIGURED SUCCESSFULLY!");
  Serial.println("============================================");
  Serial.println();
  Serial.println("  Name:  " BEACON_NAME);
  Serial.println("  UUID:  " BEACON_UUID_0 "-" BEACON_UUID_1 "-" BEACON_UUID_2
                 "-" BEACON_UUID_3);
  Serial.println("  Major: " BEACON_MAJOR);
  Serial.println("  Minor: " BEACON_MINOR);
  Serial.println();
  Serial.println("The HM-10 is now broadcasting as an iBeacon.");
  Serial.println("It will continue broadcasting even if the");
  Serial.println("ESP8266 is disconnected or powered off.");
  Serial.println();
  Serial.println("To verify: Use a BLE scanner app like");
  Serial.println("'nRF Connect' (Nordic) on your phone.");
  Serial.println("============================================");
}

void loop() {
  // Nothing to do! The HM-10 handles broadcasting independently.
  //
  // The ESP8266 can go to deep sleep to save power, or you can
  // use this loop for other tasks (e.g., reading sensors,
  // communicating with the server over Wi-Fi, etc.)

  // Forward any HM-10 output to Serial Monitor (for debugging)
  if (hm10.available()) {
    Serial.write(hm10.read());
  }
  if (Serial.available()) {
    hm10.write(Serial.read());
  }
}
