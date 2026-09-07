#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>

// ====================================================================
// WIFI CREDENTIALS
// Defined in secrets.h (gitignored — copy secrets.h.example to secrets.h
// and fill in your own values). Must match motor_controls.ino and
// AI_THINKER_CAM.ino — all three boards join the same LAN.
// ====================================================================
#include "secrets.h"

// Standalone soil-moisture + NPK probe board — deliberately off the robot
// chassis (per judges' feedback) so it can be walked to a spot in the
// field, separate from motor_controls.ino which now carries the DHT22 and
// rain sensor. mDNS hostname -> reachable on the LAN as
// agrinova-probe.local, so the backend's Farm.sensor_node_host setting
// doesn't break when DHCP hands out a different IP after a reboot.
const char* MDNS_HOSTNAME = "agrinova-probe";

// ====================================================================
// PIN DEFINITIONS
// ====================================================================
#define SOIL_PIN 5

// MAX485 to RS485 Pins
#define RX_PIN 16
#define TX_PIN 17
#define RE_DE_PIN 18

// ====================================================================
// HARDWARE INITIALIZATION
// ====================================================================
HardwareSerial rs485(1);
WebServer server(80);

// ====================================================================
// NPK MODBUS QUERIES
// ====================================================================
const byte nitro[8] = {
  0x01, 0x03, 0x00, 0x1E,
  0x00, 0x01, 0xE4, 0x0C
};

const byte phosp[8] = {
  0x01, 0x03, 0x00, 0x1F,
  0x00, 0x01, 0xB5, 0xCC
};

const byte potas[8] = {
  0x01, 0x03, 0x00, 0x20,
  0x00, 0x01, 0x85, 0xC0
};

byte values[7];

// ====================================================================
// SENSOR VARIABLES
// ====================================================================
uint16_t valN = 0;
uint16_t valP = 0;
uint16_t valK = 0;

int soilPercent = 0;

// ====================================================================
// SETUP
// ====================================================================
void setup() {

  Serial.begin(115200);

  Serial.println();
  Serial.println("================================");
  Serial.println("   AGRINOVA SOIL/NPK PROBE");
  Serial.println("================================");

  // ------------------------------------------------------------------
  // RS485
  // ------------------------------------------------------------------
  rs485.begin(
    4800,
    SERIAL_8N1,
    RX_PIN,
    TX_PIN
  );

  pinMode(RE_DE_PIN, OUTPUT);

  // Start in RECEIVE mode
  digitalWrite(RE_DE_PIN, LOW);

  // ------------------------------------------------------------------
  // WIFI
  // ------------------------------------------------------------------
  WiFi.setHostname(MDNS_HOSTNAME);
  WiFi.begin(ssid, password);

  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi connected!");

  Serial.print("ESP32 IP Address: ");
  Serial.println(WiFi.localIP());

  // ------------------------------------------------------------------
  // mDNS + HTTP API
  // ------------------------------------------------------------------
  if (MDNS.begin(MDNS_HOSTNAME)) {
    Serial.print("mDNS responder started: http://");
    Serial.print(MDNS_HOSTNAME);
    Serial.println(".local/sensors");
  }

  server.on("/sensors", HTTP_GET, handleSensors);
  server.begin();

  Serial.println();
  Serial.println("Sensors ready.");
  Serial.println("================================");
}

// ====================================================================
// LOOP
// ====================================================================
void loop() {

  static unsigned long lastRead = 0;

  // Read sensors every 3 seconds
  if (millis() - lastRead >= 3000) {

    lastRead = millis();

    // ================================================================
    // READ NPK SENSOR
    // ================================================================

    valN = requestValue(nitro);

    delay(200);

    valP = requestValue(phosp);

    delay(200);

    valK = requestValue(potas);

    delay(200);

    // ================================================================
    // READ SOIL MOISTURE
    // ================================================================

    int rawSoil = analogRead(SOIL_PIN);

    soilPercent = map(
      rawSoil,
      4095,
      1500,
      0,
      100
    );

    soilPercent = constrain(
      soilPercent,
      0,
      100
    );

    // ================================================================
    // SERIAL OUTPUT
    // ================================================================

    Serial.println();
    Serial.println("--------------------------------");

    Serial.print("Nitrogen (N):   ");
    Serial.print(valN);
    Serial.println(" mg/kg");

    Serial.print("Phosphorus (P): ");
    Serial.print(valP);
    Serial.println(" mg/kg");

    Serial.print("Potassium (K):  ");
    Serial.print(valK);
    Serial.println(" mg/kg");

    Serial.print("Soil Moisture:  ");
    Serial.print(soilPercent);
    Serial.println(" %");

    Serial.println("--------------------------------");
  }

  // Serve /sensors on every loop iteration, independent of the 3-second
  // read cadence above, so HTTP clients never block waiting on a sensor read.
  server.handleClient();
}

// ====================================================================
// HTTP API — GET /sensors
// Polled by the AgriNova backend's hardware_poller service in place of the
// simulator when a farm's hardware_enabled flag is on (see
// backend/app/services/hardware_poller.py).
// ====================================================================
void handleSensors() {

  String json = "{";
  json += "\"device\":\"ESP32_PROBE_01\",";
  json += "\"soil_moisture\":" + String(soilPercent) + ",";
  json += "\"nitrogen\":" + String(valN) + ",";
  json += "\"phosphorus\":" + String(valP) + ",";
  json += "\"potassium\":" + String(valK);
  json += "}";

  server.send(200, "application/json", json);
}

// ====================================================================
// NPK MODBUS REQUEST
// ====================================================================
uint16_t requestValue(const byte* query) {

  // ------------------------------------------------------------------
  // TRANSMIT MODE
  // ------------------------------------------------------------------
  digitalWrite(RE_DE_PIN, HIGH);

  delay(10);

  // Send Modbus command
  rs485.write(query, 8);

  // Wait until transmission completes
  rs485.flush();

  // ------------------------------------------------------------------
  // RECEIVE MODE
  // ------------------------------------------------------------------
  digitalWrite(RE_DE_PIN, LOW);

  delay(10);

  // ------------------------------------------------------------------
  // READ RESPONSE
  // ------------------------------------------------------------------
  unsigned long startTime = millis();

  int index = 0;

  memset(
    values,
    0,
    sizeof(values)
  );

  while (millis() - startTime < 1000) {

    if (rs485.available()) {

      values[index] = rs485.read();

      index++;

      if (index >= 7) {
        break;
      }
    }
  }

  // ------------------------------------------------------------------
  // PARSE RESPONSE
  // ------------------------------------------------------------------
  if (index >= 7) {

    uint16_t value =
      ((uint16_t)values[3] << 8) |
      values[4];

    return value;
  }

  // No valid response
  return 0;
}