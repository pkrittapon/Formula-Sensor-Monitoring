#include <SPI.h>
#include <LoRa.h>
#include <HTTPClient.h>

#define ss 5
#define rst 14
#define dio0 27
#define status_led 2
#define button_pin 26
TaskHandle_t Task1;
TaskHandle_t Task2;

// replace with your wifi ssid and wpa2 key
const char* ssid = "********";
const char* pass = "********";

const char* serverName = "http://api.thingspeak.com/update";
String apiKey = "********";

WiFiClient client;

bool isSend = false;

void toggle_sending() {
  if (digitalRead(button_pin) == HIGH) {
    isSend = true;
  } else {
    isSend = false;
  }
  digitalWrite(status_led, isSend);
}


void httpPostToThingSpeak(float argumentCount, char* values[]) {
  HTTPClient http;
  // Your Domain name with URL path or IP address with path
  http.begin(client, serverName);
  // Specify content-type header
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");

  // Data to send with HTTP POST
  String httpRequestData = "api_key=" + apiKey;
  for (int i = 1; i <= argumentCount; i++) {
    httpRequestData = httpRequestData + "&field" + String(i) + "=" + values[i-1];
  }
  // Send HTTP POST request
  int httpResponseCode = http.POST(httpRequestData);
  // Free resources
  http.end();
}

portMUX_TYPE bufferMutex = portMUX_INITIALIZER_UNLOCKED;

void setup() {
  pinMode(status_led, OUTPUT);
  pinMode(button_pin, INPUT_PULLUP);
  pinMode(4, OUTPUT);
  //start buzzer
  digitalWrite(status_led, HIGH);
  delay(500);
  digitalWrite(status_led, LOW);
  delay(200);
  digitalWrite(status_led, HIGH);
  delay(500);
  digitalWrite(status_led, LOW);

  attachInterrupt(button_pin, toggle_sending, CHANGE);
  toggle_sending();
  Serial.begin(115200);

  while (!Serial)
    ;

  LoRa.setPins(ss, rst, dio0);
  while (!LoRa.begin(433E6)) {
    Serial.println(".");
    delay(500);
  }

  LoRa.setSyncWord(0x16);
  LoRa.setSpreadingFactor(9);
  LoRa.setSignalBandwidth(250E3);

  //create a task that will be executed in the Task1code() function, with priority 1 and executed on core 0
  xTaskCreatePinnedToCore(
    RxLoRa,  /* Task function. */
    "Task1", /* name of task. */
    10000,   /* Stack size of task */
    NULL,    /* parameter of the task */
    1,       /* priority of the task */
    &Task1,  /* Task handle to keep track of created task */
    0);      /* pin task to core 0 */
  delay(500);

  //create a task that will be executed in the Task2code() function, with priority 1 and executed on core 1
  xTaskCreatePinnedToCore(
    Thinkspeak, /* Task function. */
    "Task2",    /* name of task. */
    10000,      /* Stack size of task */
    NULL,       /* parameter of the task */
    1,          /* priority of the task */
    &Task2,     /* Task handle to keep track of created task */
    1);         /* pin task to core 1 */
  delay(500);
}

char buffer[256];
char thingSpeakBuffer[256];
bool LoRaIsRead = false;
//Task1code: blinks an LED every 1000 ms
void RxLoRa(void* pvParameters) {
  while (true) {
    int packetSize = LoRa.parsePacket();
    if (packetSize) {
      String LoRaData;
      while (LoRa.available()) {
        LoRaData = LoRa.readString();
      }
      portENTER_CRITICAL(&bufferMutex);
      sprintf(buffer, "%s,%d,%d", LoRaData.c_str(), LoRa.packetRssi(), isSend);
      portEXIT_CRITICAL(&bufferMutex);

      LoRaIsRead = true;
      Serial.println(buffer);
    } else {
      vTaskDelay(1);
    }
  }
}

void Thinkspeak(void* pvParameters) {
  float prevTime = millis();
  while (true) {
    if (LoRaIsRead) {
      if (isSend) {
        if (WiFi.status() == WL_CONNECTED) {
          //Post http get to ThingSpeak Every 15 seconds
          if (millis() - prevTime >= 15000) {
            portENTER_CRITICAL(&bufferMutex);
            for (int i = 0; i < sizeof(buffer) / sizeof(char); i++) {
              thingSpeakBuffer[i] = buffer[i];
            }
            portEXIT_CRITICAL(&bufferMutex);
            //Reset Timer
            prevTime = millis();

            char* accx = strtok(thingSpeakBuffer, ",");
            char* accy = strtok(NULL, ",");
            //Skip non-ThingSpeak-relevant fields
            for (int i = 0; i < 5; i++) {
              strtok(NULL, ",");
            }
            char* latitude = strtok(NULL, ",");
            char* longitude = strtok(NULL, ",");
            char* speed = strtok(NULL, ",");
            char* values[5] = { accx, accy, latitude, longitude, speed };
            httpPostToThingSpeak(5, values);
          }
        } else {  //Reconnecting to Router
          WiFi.begin(ssid, pass);                //Connect ESP32 to home network
          while (WiFi.status() != WL_CONNECTED)  //Wait until Connection is complete
          {
            delay(500);
          }
        }
      }
      LoRaIsRead = false;
    } else {
      vTaskDelay(1);
    }
  }
}


void loop() {
}