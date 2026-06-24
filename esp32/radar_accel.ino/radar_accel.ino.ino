#include <Wire.h>

#define ADXL345_ADDR 0x53
#define TRIG 5
#define ECHO 18

void adxl_init() {
  Wire.beginTransmission(ADXL345_ADDR);
  Wire.write(0x2D); Wire.write(0x08);
  Wire.endTransmission();
}

void readADXL(float &x, float &y, float &z) {
  Wire.beginTransmission(ADXL345_ADDR);
  Wire.write(0x32);
  Wire.endTransmission(false);
  Wire.requestFrom(ADXL345_ADDR, 6, true);
  int16_t rx = Wire.read() | Wire.read() << 8;
  int16_t ry = Wire.read() | Wire.read() << 8;
  int16_t rz = Wire.read() | Wire.read() << 8;
  x = rx * 0.004f;  // convertir a g
  y = ry * 0.004f;
  z = rz * 0.004f;
}

long getDistance() {
  digitalWrite(TRIG, LOW); delayMicroseconds(2);
  digitalWrite(TRIG, HIGH); delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  long d = pulseIn(ECHO, HIGH, 30000) * 0.034 / 2;
  return (d == 0 || d > 400) ? -1 : d;
}

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);
  adxl_init();
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  delay(500);
}

void loop() {
  float ax, ay, az;
  readADXL(ax, ay, az);
  long dist = getDistance();

  // formato: ax,ay,az,dist
  Serial.print(ax, 3); Serial.print(",");
  Serial.print(ay, 3); Serial.print(",");
  Serial.print(az, 3); Serial.print(",");
  Serial.println(dist);

  delay(50);
}
