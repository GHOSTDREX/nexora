#include "esp_camera.h"
#include <WiFi.h>
#include <ESPmDNS.h>
#include "esp_http_server.h"

// ====================================================================
// WIFI CREDENTIALS
// Must match sensors.ino and motor_controls.ino — all three boards join
// the same LAN.
// ====================================================================
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Reachable on the LAN as agrinova-cam.local regardless of the DHCP-assigned
// IP — set this as Farm.camera_host in AgriNova's Settings page.
const char* MDNS_HOSTNAME = "agrinova-cam";

// ====================================================================
// AI-THINKER ESP32-CAM PINOUT
// ====================================================================
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5

#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

#define FLASH_LED_PIN      4

// ====================================================================
// CAMERA SERVER
// ====================================================================
httpd_handle_t camera_httpd = NULL;

#define PART_BOUNDARY "123456789000000000000987654321"

static const char* STREAM_CONTENT_TYPE =
    "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;

static const char* STREAM_BOUNDARY =
    "\r\n--" PART_BOUNDARY "\r\n";

static const char* STREAM_PART =
    "Content-Type: image/jpeg\r\n"
    "Content-Length: %u\r\n\r\n";

// ====================================================================
// STREAM HANDLER
// ====================================================================
static esp_err_t stream_handler(httpd_req_t *req)
{
    camera_fb_t *fb = NULL;
    esp_err_t res = ESP_OK;

    char part_buf[64];

    res = httpd_resp_set_type(req, STREAM_CONTENT_TYPE);

    if (res != ESP_OK) {
        return res;
    }

    while (true)
    {
        fb = esp_camera_fb_get();

        if (!fb)
        {
            Serial.println("Camera capture failed");
            res = ESP_FAIL;
        }

        if (res == ESP_OK)
        {
            size_t hlen = snprintf(
                part_buf,
                sizeof(part_buf),
                STREAM_PART,
                fb->len
            );

            res = httpd_resp_send_chunk(
                req,
                part_buf,
                hlen
            );
        }

        if (res == ESP_OK)
        {
            res = httpd_resp_send_chunk(
                req,
                (const char *)fb->buf,
                fb->len
            );
        }

        if (res == ESP_OK)
        {
            res = httpd_resp_send_chunk(
                req,
                STREAM_BOUNDARY,
                strlen(STREAM_BOUNDARY)
            );
        }

        if (fb)
        {
            esp_camera_fb_return(fb);
            fb = NULL;
        }

        if (res != ESP_OK)
        {
            break;
        }
    }

    return res;
}

// ====================================================================
// ROOT HANDLER
// ====================================================================
static esp_err_t root_handler(httpd_req_t *req)
{
    const char* message =
        "ESP32-CAM ONLINE\n"
        "Stream: /stream\n";

    httpd_resp_set_type(req, "text/plain");

    return httpd_resp_send(
        req,
        message,
        strlen(message)
    );
}

// ====================================================================
// START CAMERA SERVER
// ====================================================================
void startCameraServer()
{
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();

    config.server_port = 80;
    config.max_open_sockets = 7;
    config.lru_purge_enable = true;

    // Root endpoint
    httpd_uri_t root_uri;

    root_uri.uri = "/";
    root_uri.method = HTTP_GET;
    root_uri.handler = root_handler;
    root_uri.user_ctx = NULL;

    // Stream endpoint
    httpd_uri_t stream_uri;

    stream_uri.uri = "/stream";
    stream_uri.method = HTTP_GET;
    stream_uri.handler = stream_handler;
    stream_uri.user_ctx = NULL;

    if (httpd_start(&camera_httpd, &config) == ESP_OK)
    {
        httpd_register_uri_handler(
            camera_httpd,
            &root_uri
        );

        httpd_register_uri_handler(
            camera_httpd,
            &stream_uri
        );

        Serial.println("Camera server started");
    }
    else
    {
        Serial.println("Failed to start camera server");
    }
}

// ====================================================================
// SETUP
// ====================================================================
void setup()
{
    Serial.begin(115200);

    delay(1000);

    Serial.println();
    Serial.println("==============================");
    Serial.println("     ESP32-CAM STARTING");
    Serial.println("==============================");

    // Flash LED
    pinMode(FLASH_LED_PIN, OUTPUT);
    digitalWrite(FLASH_LED_PIN, LOW);

    // =================================================================
    // CAMERA CONFIGURATION
    // =================================================================

    camera_config_t config;

    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;

    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d7 = Y9_GPIO_NUM;

    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;

    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;

    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;

    // Camera clock
    config.xclk_freq_hz = 10000000;

    // JPEG output
    config.pixel_format = PIXFORMAT_JPEG;

    // =================================================================
    // PSRAM CONFIGURATION
    // =================================================================

    if (psramFound())
    {
        Serial.println("PSRAM detected");

        config.frame_size = FRAMESIZE_QVGA;   // 320x240
        config.jpeg_quality = 12;
        config.fb_count = 2;
        config.grab_mode = CAMERA_GRAB_LATEST;
    }
    else
    {
        Serial.println("PSRAM not detected");

        config.frame_size = FRAMESIZE_QQVGA;  // 160x120
        config.jpeg_quality = 12;
        config.fb_count = 1;
    }

    // =================================================================
    // INITIALIZE CAMERA
    // =================================================================

    esp_err_t err = esp_camera_init(&config);

    if (err != ESP_OK)
    {
        Serial.printf(
            "Camera initialization failed: 0x%x\n",
            err
        );

        return;
    }

    Serial.println("Camera initialized successfully");

    // =================================================================
    // CAMERA SENSOR SETTINGS
    // =================================================================

    sensor_t *s = esp_camera_sensor_get();

    s->set_vflip(s, 0);
    s->set_hmirror(s, 0);

    s->set_brightness(s, 1);
    s->set_contrast(s, 1);
    s->set_saturation(s, 2);

    // =================================================================
    // WIFI
    // =================================================================

    WiFi.setTxPower(WIFI_POWER_19_5dBm);
    WiFi.setHostname(MDNS_HOSTNAME);

    Serial.println();
    Serial.print("Connecting to WiFi");

    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
    }

    Serial.println();
    Serial.println("WiFi connected!");

    // =================================================================
    // mDNS
    // =================================================================

    if (MDNS.begin(MDNS_HOSTNAME))
    {
        Serial.print("mDNS responder started: http://");
        Serial.print(MDNS_HOSTNAME);
        Serial.println(".local/stream");
    }

    // =================================================================
    // START SERVER
    // =================================================================

    startCameraServer();

    Serial.println();
    Serial.println("==============================");
    Serial.println("     ESP32-CAM READY");
    Serial.println("==============================");

    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());

    Serial.print("Stream URL: http://");
    Serial.print(WiFi.localIP());
    Serial.println("/stream");

    Serial.println("==============================");
}

// ====================================================================
// LOOP
// ====================================================================
void loop()
{
    delay(10000);
}