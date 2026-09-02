#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>

// ==============================================================================
// WIFI CREDENTIALS
// Defined in secrets.h (gitignored — copy secrets.h.example to secrets.h
// and fill in your own values). Must match sensors.ino and
// AI_THINKER_CAM.ino — all three boards join the same LAN.
// ==============================================================================

#include "secrets.h"

// Reachable on the LAN as agrinova-robot.local regardless of the DHCP-
// assigned IP — set this as Farm.robot_host in AgriNova's Settings page.
const char *MDNS_HOSTNAME = "agrinova-robot";

// ==============================================================================
// HARDWARE PINS
// ==============================================================================

// Locomotion Motors (BTS7960)
const int LEFT_RPWM = 5;
const int LEFT_LPWM = 4;
const int RIGHT_RPWM = 6;
const int RIGHT_LPWM = 7;

// L298N #1 (Pump & Plow)
const int PUMP_IN1 = 8;
const int PUMP_IN2 = 12;
const int PLOW_IN3 = 10;
const int PLOW_IN4 = 13;

// L298N #2 (Camera & Seed Dispenser BO Motors)
const int CAM_IN1 = 9;
const int CAM_IN2 = 11;
const int SEED_IN3 = 14;
const int SEED_IN4 = 15;

// ==============================================================================
// ROBOT STATE
// ==============================================================================

int motorSpeed = 100;

// Last locomotion command, so a set_speed change can be re-applied to the
// motors immediately instead of only taking effect on the next move command.
String lastDirection = "move_stop";

bool pumpState = false;
bool plowState = false;

const int plowDuration = 100;

// --- Camera BO Motor ---
const int camStepDuration = 50;
const int camMaxSteps = 8;
int camCurrentStep = 0;

// --- Seed Dispenser BO Motor ---
bool seedActive = false;
long seedPosition = 0;

const int seedMaxLimit = 180;

int seedDirection = 1;
unsigned long lastSeedTime = 0;

// ==============================================================================
// OBJECTS
// ==============================================================================

WebServer server(80);

// ==============================================================================
// MOTOR CONTROL
// ==============================================================================

void setMotors(int leftFwd, int leftRev, int rightFwd, int rightRev) {

  analogWrite(LEFT_RPWM, leftFwd);
  analogWrite(LEFT_LPWM, leftRev);

  analogWrite(RIGHT_RPWM, rightFwd);
  analogWrite(RIGHT_LPWM, rightRev);
}

// Re-drives the motors using the current motorSpeed and the last direction
// command — called after every move command and after every set_speed
// change, so adjusting the slider while the robot is already moving takes
// effect immediately instead of waiting for the next move command.
void applyDirection() {

  if (lastDirection == "move_forward") {
    setMotors(0, motorSpeed, motorSpeed, 0);
  }

  else if (lastDirection == "move_back") {
    setMotors(motorSpeed, 0, 0, motorSpeed);
  }

  else if (lastDirection == "move_left") {
    setMotors(motorSpeed, 0, motorSpeed, 0);
  }

  else if (lastDirection == "move_right") {
    setMotors(0, motorSpeed, 0, motorSpeed);
  }

  else {
    setMotors(0, 0, 0, 0);
  }
}

// ==============================================================================
// SEED DISPENSER MOVEMENT
// ==============================================================================

void processSeedMovement() {

  unsigned long now = millis();

  long dt = now - lastSeedTime;

  lastSeedTime = now;

  if (seedActive) {

    // Move left/right
    seedPosition += seedDirection * dt;

    // Right limit
    if (seedPosition >= seedMaxLimit) {

      seedPosition = seedMaxLimit;

      seedDirection = -1;
    }

    // Left limit
    else if (seedPosition <= -seedMaxLimit) {

      seedPosition = -seedMaxLimit;

      seedDirection = 1;
    }

    // Motor direction
    if (seedDirection == 1) {

      digitalWrite(SEED_IN3, HIGH);
      digitalWrite(SEED_IN4, LOW);

    } else {

      digitalWrite(SEED_IN3, LOW);
      digitalWrite(SEED_IN4, HIGH);
    }

  } else {

    // Return to center
    if (seedPosition > 10) {

      digitalWrite(SEED_IN3, LOW);
      digitalWrite(SEED_IN4, HIGH);

      seedPosition -= dt;

    }

    else if (seedPosition < -10) {

      digitalWrite(SEED_IN3, HIGH);
      digitalWrite(SEED_IN4, LOW);

      seedPosition += dt;

    }

    else {

      digitalWrite(SEED_IN3, LOW);
      digitalWrite(SEED_IN4, LOW);

      seedPosition = 0;
    }
  }
}

// ==============================================================================
// ROBOT STATUS API
// ==============================================================================

void handleStatus() {

  String json = "{";

  json += "\"device\":\"ESP32_ROBOT_01\",";
  json += "\"ip\":\"" + WiFi.localIP().toString() + "\",";
  json += "\"motor_speed\":" + String(motorSpeed) + ",";
  json += "\"pump\":" + String(pumpState ? "true" : "false") + ",";
  json += "\"plow\":" + String(plowState ? "true" : "false") + ",";
  json += "\"seed\":" + String(seedActive ? "true" : "false") + ",";
  json += "\"cam_pos\":" + String(camCurrentStep);

  json += "}";

  server.send(200, "application/json", json);
}

// ==============================================================================
// ROBOT COMMAND API
// ==============================================================================

void handleCommand() {

  if (!server.hasArg("action")) {

    server.send(400, "text/plain", "Missing action");

    return;
  }

  String action = server.arg("action");

  // --------------------------------------------------------------------------
  // LOCOMOTION
  // --------------------------------------------------------------------------

  if (action == "move_forward" || action == "move_back" ||
      action == "move_left" || action == "move_right" ||
      action == "move_stop") {

    lastDirection = action;
    applyDirection();
  }

  // --------------------------------------------------------------------------
  // MOTOR SPEED
  // --------------------------------------------------------------------------

  else if (action == "set_speed") {

    if (server.hasArg("val")) {

      motorSpeed = server.arg("val").toInt();

      motorSpeed = constrain(motorSpeed, 0, 255);

      applyDirection();
    }
  }

  // --------------------------------------------------------------------------
  // WATER PUMP
  // --------------------------------------------------------------------------

  else if (action == "pump_on") {

    pumpState = true;

    digitalWrite(PUMP_IN1, HIGH);
    digitalWrite(PUMP_IN2, LOW);
  }

  else if (action == "pump_off") {

    pumpState = false;

    digitalWrite(PUMP_IN1, LOW);
    digitalWrite(PUMP_IN2, LOW);
  }

  // --------------------------------------------------------------------------
  // PLOW
  // --------------------------------------------------------------------------

  else if (action == "plow_on") {

    if (!plowState) {

      digitalWrite(PLOW_IN3, LOW);
      digitalWrite(PLOW_IN4, HIGH);

      delay(plowDuration);

      digitalWrite(PLOW_IN3, LOW);
      digitalWrite(PLOW_IN4, LOW);

      plowState = true;
    }
  }

  else if (action == "plow_off") {

    if (plowState) {

      digitalWrite(PLOW_IN3, HIGH);
      digitalWrite(PLOW_IN4, LOW);

      delay(plowDuration);

      digitalWrite(PLOW_IN3, LOW);
      digitalWrite(PLOW_IN4, LOW);

      plowState = false;
    }
  }

  // --------------------------------------------------------------------------
  // CAMERA
  // --------------------------------------------------------------------------

  else if (action == "camera_left") {

    if (camCurrentStep > -camMaxSteps) {

      digitalWrite(CAM_IN1, HIGH);
      digitalWrite(CAM_IN2, LOW);

      delay(camStepDuration);

      digitalWrite(CAM_IN1, LOW);
      digitalWrite(CAM_IN2, LOW);

      camCurrentStep--;
    }
  }

  else if (action == "camera_right") {

    if (camCurrentStep < camMaxSteps) {

      digitalWrite(CAM_IN1, LOW);
      digitalWrite(CAM_IN2, HIGH);

      delay(camStepDuration);

      digitalWrite(CAM_IN1, LOW);
      digitalWrite(CAM_IN2, LOW);

      camCurrentStep++;
    }
  }

  else if (action == "camera_center") {

    if (camCurrentStep < 0) {

      digitalWrite(CAM_IN1, LOW);
      digitalWrite(CAM_IN2, HIGH);

      delay(camStepDuration * abs(camCurrentStep));
    }

    else if (camCurrentStep > 0) {

      digitalWrite(CAM_IN1, HIGH);
      digitalWrite(CAM_IN2, LOW);

      delay(camStepDuration * camCurrentStep);
    }

    digitalWrite(CAM_IN1, LOW);
    digitalWrite(CAM_IN2, LOW);

    camCurrentStep = 0;
  }

  // --------------------------------------------------------------------------
  // SEED DISPENSER
  // --------------------------------------------------------------------------

  else if (action == "seed_on") {

    seedActive = true;
  }

  else if (action == "seed_off") {

    seedActive = false;
  }

  // --------------------------------------------------------------------------
  // UNKNOWN COMMAND
  // --------------------------------------------------------------------------

  else {

    server.send(400, "text/plain", "Unknown command");

    return;
  }

  server.send(200, "text/plain", "OK");
}

// ==============================================================================
// SETUP
// ==============================================================================

void setup() {

  Serial.begin(115200);

  delay(500);

  Serial.println();
  Serial.println("--- ESP32-S3 ROBOT CONTROLLER ---");

  // ==========================================================================
  // LOCOMOTION PINS
  // ==========================================================================

  pinMode(LEFT_RPWM, OUTPUT);
  pinMode(LEFT_LPWM, OUTPUT);

  pinMode(RIGHT_RPWM, OUTPUT);
  pinMode(RIGHT_LPWM, OUTPUT);

  setMotors(0, 0, 0, 0);

  // ==========================================================================
  // L298N #1
  // ==========================================================================

  pinMode(PUMP_IN1, OUTPUT);
  pinMode(PUMP_IN2, OUTPUT);

  pinMode(PLOW_IN3, OUTPUT);
  pinMode(PLOW_IN4, OUTPUT);

  digitalWrite(PUMP_IN1, LOW);
  digitalWrite(PUMP_IN2, LOW);

  digitalWrite(PLOW_IN3, LOW);
  digitalWrite(PLOW_IN4, LOW);

  // ==========================================================================
  // L298N #2
  // ==========================================================================

  pinMode(CAM_IN1, OUTPUT);
  pinMode(CAM_IN2, OUTPUT);

  pinMode(SEED_IN3, OUTPUT);
  pinMode(SEED_IN4, OUTPUT);

  digitalWrite(CAM_IN1, LOW);
  digitalWrite(CAM_IN2, LOW);

  digitalWrite(SEED_IN3, LOW);
  digitalWrite(SEED_IN4, LOW);

  // ==========================================================================
  // WIFI
  // ==========================================================================

  WiFi.mode(WIFI_STA);
  WiFi.setHostname(MDNS_HOSTNAME);

  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {

    delay(500);

    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi connected!");

  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // ==========================================================================
  // mDNS
  // ==========================================================================

  if (MDNS.begin(MDNS_HOSTNAME)) {
    Serial.print("mDNS responder started: http://");
    Serial.print(MDNS_HOSTNAME);
    Serial.println(".local/command");
  }

  // ==========================================================================
  // HTTP API
  // ==========================================================================

  server.on("/command", HTTP_GET, handleCommand);
  server.on("/status", HTTP_GET, handleStatus);

  server.begin();

  lastSeedTime = millis();

  Serial.println();
  Serial.println("======================================");
  Serial.println("       ROBOT CONTROLLER READY");
  Serial.println("======================================");

  Serial.println("API endpoints:");

  Serial.println("/command?action=move_forward");
  Serial.println("/command?action=move_back");
  Serial.println("/command?action=move_left");
  Serial.println("/command?action=move_right");
  Serial.println("/command?action=move_stop");
  Serial.println("/command?action=set_speed&val=<0-255>");

  Serial.println("/command?action=pump_on");
  Serial.println("/command?action=pump_off");

  Serial.println("/command?action=seed_on");
  Serial.println("/command?action=seed_off");

  Serial.println("/command?action=plow_on");
  Serial.println("/command?action=plow_off");

  Serial.println("/command?action=camera_left");
  Serial.println("/command?action=camera_right");
  Serial.println("/command?action=camera_center");

  Serial.println("/status");

  Serial.println("======================================");
}

// ==============================================================================
// LOOP
// ==============================================================================

void loop() {

  server.handleClient();

  processSeedMovement();
}
