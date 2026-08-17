# ESP8266 + HM-10 BLE Beacon Setup

## Wiring

Both modules run at **3.3V logic**, so no level shifters needed.

```
  ESP8266 (NodeMCU)              HM-10
  ┌──────────────┐          ┌──────────┐
  │              │          │          │
  │     3V3  ────┼──────────┼── VCC    │
  │     GND  ────┼──────────┼── GND    │
  │     D5   ────┼──────────┼── TXD    │  (HM-10 TX → ESP RX)
  │     D6   ────┼──────────┼── RXD    │  (ESP TX → HM-10 RX)
  │              │          │          │
  └──────────────┘          └──────────┘
```

### Pin Reference

| HM-10 Pin | ESP8266 Pin | NodeMCU Label | GPIO |
|-----------|-------------|---------------|------|
| VCC       | 3.3V        | 3V3           | —    |
| GND       | GND         | GND           | —    |
| TXD       | D5          | D5            | 14   |
| RXD       | D6          | D6            | 12   |

> **Why D5/D6?** The default hardware serial (GPIO1/GPIO3) is used for USB debugging. Using SoftwareSerial on D5/D6 lets you keep the Serial Monitor for debugging while talking to the HM-10.

> **Power**: If your HM-10 is on a breakout board with a voltage regulator, you can power it from the NodeMCU's `VIN` (5V from USB) instead of 3V3. Check your specific board.

## Arduino IDE Setup

1. **Install ESP8266 board support**: In Arduino IDE → File → Preferences → Additional Board URLs, add:
   ```
   http://arduino.esp8266.com/stable/package_esp8266com_index.json
   ```
2. **Board Manager** → search "ESP8266" → install
3. **Select board**: Tools → Board → "NodeMCU 1.0 (ESP-12E Module)"
4. **Select port**: Tools → Port → your USB serial port

## Flashing

Upload the `beacon.ino` sketch. Open Serial Monitor at **9600 baud** to see debug output.
After upload, the ESP8266 will:
1. Send AT commands to configure the HM-10 as an iBeacon
2. Start broadcasting

The HM-10 remembers its settings across power cycles, so once configured, it will broadcast automatically even without the ESP8266 (though the ESP is needed if you want to change settings dynamically).
