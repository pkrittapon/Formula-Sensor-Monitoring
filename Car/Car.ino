
#include <SPI.h>
#include <LoRa.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <QMC5883LCompass.h>
#include <TinyGPS++.h>

#define GPS_BAUDRATE 9600  // The default baudrate of NEO-6M is 9600

//define pin for LoRa module
#define ss 5
#define rst 14
#define dio0 27

// init task for duo core
TaskHandle_t Task1;
TaskHandle_t Task2;

Adafruit_MPU6050 mpu; //mpu6050 object
QMC5883LCompass compass; // compass pbject
TinyGPSPlus gps;  // the TinyGPS++ object

// initial mpu value
float accelOffsetX = 0.0;
float accelOffsetY = 0.0;
float accelOffsetZ = 0.0;

float gyroOffsetX = 0.0;
float gyroOffsetY = 0.0;
float gyroOffsetZ = 0.0;

void setup() {
  delay(1000);
  Serial.begin(115200);
  Serial2.begin(GPS_BAUDRATE);

  // LoRa setup
  LoRa.setPins(ss, rst, dio0);
  while (!LoRa.begin(433E6)) {
    Serial.println(".");
    delay(500);
  }
  LoRa.setSyncWord(0x16);
  LoRa.setSpreadingFactor(9);
  LoRa.setSignalBandwidth(250E3);
  Serial.println("LoRa Initializing OK!");

  // mpu setup
   if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) {
      delay(10);
    }
  }
  mpu.setAccelerometerRange(MPU6050_RANGE_16_G);
  mpu.setGyroRange(MPU6050_RANGE_2000_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);

  // compass setup
  compass.init();
  compass.setCalibrationOffsets(-289.00, -15.00, -135.00);
  compass.setCalibrationScales(0.93, 0.91, 1.22);

  //offset
  for (int i = 0; i < 200; i++) {
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);
    accelOffsetX += a.acceleration.x;
    accelOffsetY += a.acceleration.y;
    gyroOffsetX += g.gyro.x;
    gyroOffsetY += g.gyro.y;
    gyroOffsetZ += g.gyro.z;
    delay(5);
  }
  accelOffsetX /= 200.0;
  accelOffsetY /= 200.0;
  gyroOffsetX /= 200.0;
  gyroOffsetY /= 200.0;
  gyroOffsetZ /= 200.0;

  // create task for sendLoRa data, executed on core 1
  xTaskCreatePinnedToCore(
    sendLoRa, /* Task function. */
    "Task1",  /* name of task. */
    10000,    /* Stack size of task */
    NULL,     /* parameter of the task */
    1,        /* priority of the task */
    &Task1,   /* Task handle to keep track of created task */
    1);       /* pin task to core 1 */
  delay(500);

  // create task for read data, executed on core 0
  xTaskCreatePinnedToCore(
    readData, /* Task function. */
    "Task2",  /* name of task. */
    10000,    /* Stack size of task */
    NULL,     /* parameter of the task */
    1,        /* priority of the task */
    &Task2,   /* Task handle to keep track of created task */
    0);       /* pin task to core 0 */
  delay(500);

}
unsigned long prev_send = 0;

float gyroX, gyroY, gyroZ, accX, accY, accZ;
float yaw, pitch, roll = 0;
float heading;

double lat, lon = 0.0;
float gps_speed = 0.0;

void sendLoRa(void* pvParameters) {
  Serial.println("sending");
  while (true) {
    if (millis() - prev_send >= 10) {// sending every 10 ms
      LoRa.beginPacket();
      LoRa.print(String(accX,2) + "," + String(accY,2) + "," + String(accZ,2) + "," 
                + String(yaw,2) + "," + String(pitch,2) + "," + String(roll,2) + "," 
                + String(heading,2)+ "," + String(lat,7) + "," + String(lon,7) + "," + String(gps_speed,2));
      LoRa.endPacket();
      prev_send = millis();
    }
  }
}


unsigned long prevTime, prev_time = millis();
void readData(void* pvParameters) {
  Serial.println("reading");
  while (true) {
    if (millis() - prev_time >= 5) {//reading every 5 ms
      if (Serial2.available() > 0) {//read gps data
        if (gps.encode(Serial2.read())) {
          if (gps.location.isValid()) {
            lat = gps.location.lat();
            lon = gps.location.lng();
          }
          if (gps.speed.isValid()) {
            gps_speed = gps.speed.kmph();
          }
        }
      }
      sensors_event_t a, g, temp;
      mpu.getEvent(&a, &g, &temp);

      //read mpu6050 data
      gyroX = g.gyro.x - gyroOffsetX;
      gyroY = g.gyro.y - gyroOffsetY;
      gyroZ = g.gyro.z - gyroOffsetZ;
      accX = a.acceleration.x - accelOffsetX;
      accY = a.acceleration.y - accelOffsetY;
      accZ = a.acceleration.z;

      //read compass data
      int x, y, z;  
      // Read compass values
      compass.read();
      // Return XYZ readings
      x = compass.getX();
      y = compass.getY();
      z = compass.getZ();

      // Calculate heading
      heading = atan2(y, x) * 180 / M_PI;  // Convert radians to degrees

      if (heading < 0) {
        heading += 360;  // Ensure heading is within 0 to 360 degrees
      }

      //calculate yaw pitch roll
      yaw += gyroZ * ((float)(millis() - prevTime) / 1000);
      pitch = atan2(-accX, sqrt(accY * accY + accZ * accZ));
      roll = atan2(accY, accZ);
      
      prevTime = millis();
      prev_time = millis();
    }
  }
}

void loop() {
}