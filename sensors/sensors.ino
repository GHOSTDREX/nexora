#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <DHT.h>

// ====================================================================
// WIFI CREDENTIALS
// Must match motor_controls.ino and AI_THINKER_CAM.ino — all three boards
// join the same LAN so the AgriNova backend can reach each of them and
// motor_controls.ino's pump relay can reach this node's readings indirectly
// via the backend's hardware poller.
// ====================================================================
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// mDNS hostname -> reachable on the LAN as agrinova-sensors.local, so the
// backend's Farm.sensor_node_host setting doesn't break when DHCP hands out
// a different IP after a reboot.
const char* MDNS_HOSTNAME = "agrinova-sensors";

// ====================================================================
// PIN DEFINITIONS
// ====================================================================
#define DHTPIN 4
#define DHTTYPE DHT22

#define SOIL_PIN 5
#define RAIN_PIN 6

// MAX485 to RS485 Pins
#define RX_PIN 16
#define TX_PIN 17
#define RE_DE_PIN 18

// ====================================================================
// HARDWARE INITIALIZATION
// ====================================================================
HardwareSerial rs485(1);
DHT dht(DHTPIN, DHTTYPE);
WebServer server(80);

// Rain sensor is a resistive analog probe, not a mm rain gauge — treat
// intensity above this percent as "rain detected" for the automation logic
// on the AgriNova backend (rainwater harvesting lid, alerts).
#define RAIN_DETECTED_THRESHOLD 20

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

float temp = 0.0;
float hum = 0.0;

int soilPercent = 0;
int rainPercent = 0;

// ====================================================================
// SETUP
// ====================================================================
void setup() {

  Serial.begin(115200);

  Serial.println();
  Serial.println("================================");
  Serial.println("     SMART AGRICULTURE NODE");
  Serial.println("================================");

  // ------------------------------------------------------------------
  // DHT22
  // ------------------------------------------------------------------
  dht.begin();

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
    // READ DHT22
    // ================================================================

    temp = dht.readTemperature();
    hum = dht.readHumidity();

    if (isnan(temp)) {
      temp = 0.0;
    }

    if (isnan(hum)) {
      hum = 0.0;
    }

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
    // READ RAIN SENSOR
    // ================================================================

    int rawRain = analogRead(RAIN_PIN);

    rainPercent = map(
      rawRain,
      4095,
      1500,
      0,
      100
    );

    rainPercent = constrain(
      rainPercent,
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

    Serial.print("Temperature:    ");
    Serial.print(temp);
    Serial.println(" °C");

    Serial.print("Humidity:       ");
    Serial.print(hum);
    Serial.println(" %");

    Serial.print("Soil Moisture:  ");
    Serial.print(soilPercent);
    Serial.println(" %");

    Serial.print("Rain Intensity:  ");
    Serial.print(rainPercent);
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

  bool rainDetected = rainPercent > RAIN_DETECTED_THRESHOLD;

  String json = "{";
  json += "\"device\":\"ESP32_SENSOR_NODE\",";
  json += "\"nitrogen\":" + String(valN) + ",";
  json += "\"phosphorus\":" + String(valP) + ",";
  json += "\"potassium\":" + String(valK) + ",";
  json += "\"temperature\":" + String(temp, 1) + ",";
  json += "\"humidity\":" + String(hum, 1) + ",";
  json += "\"soil_moisture\":" + String(soilPercent) + ",";
  json += "\"rain_intensity\":" + String(rainPercent) + ",";
  json += "\"rain_detected\":";
  json += rainDetected ? "true" : "false";
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