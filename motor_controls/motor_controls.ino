#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <ESP32Servo.h>

// ==============================================================================
// WIFI CREDENTIALS
// Must match sensors.ino and AI_THINKER_CAM.ino — all three boards join the
// same LAN.
// ==============================================================================

const char *ssid = "YOUR_WIFI_SSID";
const char *password = "YOUR_WIFI_PASSWORD";

// Reachable on the LAN as agrinova-robot.local regardless of the DHCP-
// assigned IP — set this as Farm.robot_host in AgriNova's Settings page.
const char *MDNS_HOSTNAME = "agrinova-robot";

// ==============================================================================
// HARDWARE PINS
// ==============================================================================

// Motor Left - BTS7960 #1
const int LEFT_RPWM = 5;
const int LEFT_LPWM = 4;

// Motor Right - BTS7960 #2
const int RIGHT_RPWM = 6;
const int RIGHT_LPWM = 7;

// Robot tools
const int PUMP_PIN = 8;
const int SEED_PIN = 9;
const int PLOW_PIN = 10;
const int CAM_PIN = 11;

// ==============================================================================
// ROBOT STATE
// ==============================================================================

int motorSpeed = 100;

bool pumpState = false;
bool seedActive = false;
bool plowState = false;

int seedAngle = 0;
int plowAngle = 0;
int camAngle = 90;

// ==============================================================================
// SEED DISPENSER
// ==============================================================================

unsigned long lastSeedMove = 0;

const int seedDelay = 15;

int seedDir = 1;

// ==============================================================================
// OBJECTS
// ==============================================================================

WebServer server(80);

Servo seedServo;
Servo plowServo;
Servo camServo;

// ==============================================================================
// MOTOR CONTROL
// ==============================================================================

void setMotors(
  int leftFwd,
  int leftRev,
  int rightFwd,
  int rightRev
) {

  analogWrite(LEFT_RPWM, leftFwd);
  analogWrite(LEFT_LPWM, leftRev);

  analogWrite(RIGHT_RPWM, rightFwd);
  analogWrite(RIGHT_LPWM, rightRev);
}

// ==============================================================================
// MOVE FORWARD
// ==============================================================================

void moveForward() {

  setMotors(
    motorSpeed,
    0,
    motorSpeed,
    0
  );
}

// ==============================================================================
// MOVE BACKWARD
// ==============================================================================

void moveBackward() {

  setMotors(
    0,
    motorSpeed,
    0,
    motorSpeed
  );
}

// ==============================================================================
// TURN LEFT
// ==============================================================================

void moveLeft() {

  setMotors(
    0,
    motorSpeed,
    motorSpeed,
    0
  );
}

// ==============================================================================
// TURN RIGHT
// ==============================================================================

void moveRight() {

  setMotors(
    motorSpeed,
    0,
    0,
    motorSpeed
  );
}

// ==============================================================================
// STOP
// ==============================================================================

void moveStop() {

  setMotors(
    0,
    0,
    0,
    0
  );
}

// ==============================================================================
// SEED DISPENSER MOVEMENT
// ==============================================================================

void processSeedMovement() {

  if (seedActive) {

    if (millis() - lastSeedMove >= seedDelay) {

      lastSeedMove = millis();

      seedAngle += seedDir;

      if (seedAngle >= 90) {

        seedAngle = 90;
        seedDir = -1;
      }

      else if (seedAngle <= 0) {

        seedAngle = 0;
        seedDir = 1;
      }

      seedServo.write(seedAngle);
    }
  }

  else {

    if (seedAngle != 0) {

      seedAngle = 0;
      seedDir = 1;

      seedServo.write(0);
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
  json += "\"wifi\":true,";

  json += "\"motor_speed\":" + String(motorSpeed) + ",";

  json += "\"pump\":";
  json += pumpState ? "true," : "false,";

  json += "\"seed\":";
  json += seedActive ? "true," : "false,";

  json += "\"seed_angle\":" + String(seedAngle) + ",";

  json += "\"plow\":";
  json += plowState ? "true," : "false,";

  json += "\"plow_angle\":" + String(plowAngle) + ",";

  json += "\"camera_angle\":" + String(camAngle);

  json += "}";

  server.send(
    200,
    "application/json",
    json
  );
}

// ==============================================================================
// ROBOT COMMAND API
// ==============================================================================

void handleCommand() {

  if (!server.hasArg("action")) {

    server.send(
      400,
      "text/plain",
      "Missing action"
    );

    return;
  }

  String action = server.arg("action");

  // --------------------------------------------------------------------------
  // MOVEMENT
  // --------------------------------------------------------------------------

  if (action == "move_forward") {

    moveForward();

    Serial.println("COMMAND: FORWARD");
  }

  else if (action == "move_back") {

    moveBackward();

    Serial.println("COMMAND: BACKWARD");
  }

  else if (action == "move_left") {

    moveLeft();

    Serial.println("COMMAND: LEFT");
  }

  else if (action == "move_right") {

    moveRight();

    Serial.println("COMMAND: RIGHT");
  }

  else if (action == "move_stop") {

    moveStop();

    Serial.println("COMMAND: STOP");
  }

  // --------------------------------------------------------------------------
  // MOTOR SPEED
  // --------------------------------------------------------------------------

  else if (action == "set_speed") {

    if (server.hasArg("value")) {

      motorSpeed = server.arg("value").toInt();

      motorSpeed = constrain(
        motorSpeed,
        0,
        255
      );

      Serial.print("MOTOR SPEED: ");
      Serial.println(motorSpeed);
    }
  }

  // --------------------------------------------------------------------------
  // WATER PUMP
  // --------------------------------------------------------------------------

  else if (action == "pump_on") {

    pumpState = true;

    digitalWrite(
      PUMP_PIN,
      HIGH
    );

    Serial.println("PUMP: ON");
  }

  else if (action == "pump_off") {

    pumpState = false;

    digitalWrite(
      PUMP_PIN,
      LOW
    );

    Serial.println("PUMP: OFF");
  }

  // --------------------------------------------------------------------------
  // SEED DISPENSER
  // --------------------------------------------------------------------------

  else if (action == "seed_on") {

    seedActive = true;

    Serial.println("SEED DISPENSER: ON");
  }

  else if (action == "seed_off") {

    seedActive = false;

    Serial.println("SEED DISPENSER: OFF");
  }

  // --------------------------------------------------------------------------
  // PLOW
  // --------------------------------------------------------------------------

  else if (action == "plow_on") {

    plowState = true;

    plowAngle = 90;

    plowServo.write(
      plowAngle
    );

    Serial.println("PLOW: DOWN");
  }

  else if (action == "plow_off") {

    plowState = false;

    plowAngle = 0;

    plowServo.write(
      plowAngle
    );

    Serial.println("PLOW: UP");
  }

  // --------------------------------------------------------------------------
  // CAMERA
  // --------------------------------------------------------------------------

  else if (action == "camera_left") {

    camAngle -= 10;

    camAngle = constrain(
      camAngle,
      10,
      170
    );

    camServo.write(
      camAngle
    );

    Serial.print("CAMERA: ");
    Serial.println(camAngle);
  }

  else if (action == "camera_right") {

    camAngle += 10;

    camAngle = constrain(
      camAngle,
      10,
      170
    );

    camServo.write(
      camAngle
    );

    Serial.print("CAMERA: ");
    Serial.println(camAngle);
  }

  else if (action == "camera_center") {

    camAngle = 90;

    camServo.write(
      camAngle
    );

    Serial.println("CAMERA: CENTER");
  }

  else if (action == "camera_pan") {

    if (server.hasArg("angle")) {

      camAngle = server.arg("angle").toInt();

      camAngle = constrain(
        camAngle,
        10,
        170
      );

      camServo.write(
        camAngle
      );

      Serial.print("CAMERA ANGLE: ");
      Serial.println(camAngle);
    }
  }

  // --------------------------------------------------------------------------
  // UNKNOWN COMMAND
  // --------------------------------------------------------------------------

  else {

    server.send(
      400,
      "text/plain",
      "Unknown command"
    );

    return;
  }

  server.send(
    200,
    "text/plain",
    "OK"
  );
}

// ==============================================================================
// SETUP
// ==============================================================================

void setup() {

  Serial.begin(115200);

  delay(500);

  Serial.println();
  Serial.println("======================================");
  Serial.println("       ESP32 ROBOT CONTROLLER");
  Serial.println("======================================");

  // ==========================================================================
  // MOTOR PINS
  // ==========================================================================

  pinMode(
    LEFT_RPWM,
    OUTPUT
  );

  pinMode(
    LEFT_LPWM,
    OUTPUT
  );

  pinMode(
    RIGHT_RPWM,
    OUTPUT
  );

  pinMode(
    RIGHT_LPWM,
    OUTPUT
  );

  // Safe startup
  moveStop();

  // ==========================================================================
  // PUMP
  // ==========================================================================

  pinMode(
    PUMP_PIN,
    OUTPUT
  );

  digitalWrite(
    PUMP_PIN,
    LOW
  );

  // ==========================================================================
  // SERVO TIMERS
  // ==========================================================================

  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  // ==========================================================================
  // SEED SERVO
  // ==========================================================================

  seedServo.setPeriodHertz(50);

  seedServo.attach(
    SEED_PIN,
    500,
    2400
  );

  seedServo.write(0);

  // ==========================================================================
  // PLOW SERVO
  // ==========================================================================

  plowServo.setPeriodHertz(50);

  plowServo.attach(
    PLOW_PIN,
    500,
    2400
  );

  plowServo.write(0);

  // ==========================================================================
  // CAMERA SERVO
  // ==========================================================================

  camServo.setPeriodHertz(50);

  camServo.attach(
    CAM_PIN,
    500,
    2400
  );

  camServo.write(90);

  // ==========================================================================
  // WIFI
  // ==========================================================================

  WiFi.mode(WIFI_STA);
  WiFi.setHostname(MDNS_HOSTNAME);

  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);

  WiFi.begin(
    ssid,
    password
  );

  while (WiFi.status() != WL_CONNECTED) {

    delay(500);

    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi connected!");

  Serial.print("IP Address: ");
  Serial.println(
    WiFi.localIP()
  );

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

  server.on(
    "/command",
    HTTP_GET,
    handleCommand
  );

  server.on(
    "/status",
    HTTP_GET,
    handleStatus
  );

  server.begin();

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

  // Handle incoming HTTP commands
  server.handleClient();

  // Keep seed dispenser movement non-blocking
  processSeedMovement();
}