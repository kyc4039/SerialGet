#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <DHT.h>
#include <DHT_U.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_ADDRESS 0x3C
#define DHTPIN 4
#define DHTTYPE DHT11

Adafruit_SSD1306 oled(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
DHT dht(DHTPIN, DHTTYPE);

const int pinSwitch = 2;
const int pinCds = A0;
const int pinFlame = A1;
const int pinWater = A2;
const int pinSound = 5;
const int pinReed = 6;
const int pinTrig = 7;
const int pinEcho = 8;
const int pinHit = 9;

int lastSwitchState = HIGH;
int currentPage = 0;
const int totalPages = 9;  // 0: 인트로, 1~8: 센서별

// ── 최신 센서값을 저장해두는 전역 변수 (화면 갱신용) ──
int cdsValue, flameValue, waterValue, soundValue, reedValue, hitValue;
long distance;
float temp, hum;

void setup() {
  Serial.begin(115200);

  pinMode(pinSwitch, INPUT_PULLUP);
  pinMode(pinSound, INPUT);
  pinMode(pinReed, INPUT_PULLUP);
  pinMode(pinTrig, OUTPUT);
  pinMode(pinEcho, INPUT);
  pinMode(pinHit, INPUT_PULLUP);

  dht.begin();
  oled.begin(SSD1306_SWITCHCAPVCC, OLED_ADDRESS);
  renderPage();
}

long readDistanceCm() {
  digitalWrite(pinTrig, LOW);
  delayMicroseconds(2);
  digitalWrite(pinTrig, HIGH);
  delayMicroseconds(10);
  digitalWrite(pinTrig, LOW);
  long duration = pulseIn(pinEcho, HIGH, 30000);
  return duration * 0.034 / 2;
}

void readAllSensors() {
  cdsValue = analogRead(pinCds);
  flameValue = analogRead(pinFlame);
  waterValue = analogRead(pinWater);
  soundValue = digitalRead(pinSound);
  reedValue = digitalRead(pinReed);
  hitValue = digitalRead(pinHit);
  distance = readDistanceCm();
  temp = dht.readTemperature();
  hum = dht.readHumidity();
}

void drawBar(const char* label, int value, int minV, int maxV) {
  oled.setTextSize(1);
  oled.setCursor(0, 0);
  oled.print(label);

  oled.setTextSize(2);
  oled.setCursor(0, 16);
  oled.print(value);

  int barWidth = map(constrain(value, minV, maxV), minV, maxV, 0, 128);
  oled.drawRect(0, 45, 128, 14, SSD1306_WHITE);
  oled.fillRect(0, 45, barWidth, 14, SSD1306_WHITE);
}

void drawStatus(const char* label, bool active, const char* onText, const char* offText) {
  oled.setTextSize(1);
  oled.setCursor(0, 0);
  oled.print(label);

  oled.setTextSize(2);
  oled.setCursor(10, 30);
  oled.print(active ? onText : offText);
}

void renderPage() {
  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);

  switch (currentPage) {
    case 0:
      oled.setTextSize(2);
      oled.setCursor(28, 16);
      oled.println("Sensor");
      oled.setCursor(40, 36);
      oled.println("Menu");
      break;
    case 1:
      drawBar("1. CdS (Ill)", cdsValue, 0, 1023);
      break;
    case 2:
      drawBar("2. Flame", flameValue, 0, 1023);
      break;
    case 3:
      drawBar("3. Water Level", waterValue, 0, 1023);
      break;
    case 4:
      oled.setTextSize(1);
      oled.setCursor(0, 0);
      oled.print("4. Temp / Humi");
      if (isnan(temp) || isnan(hum)) {
        oled.setCursor(0, 30);
        oled.print("Read Error");
      } else {
        oled.setTextSize(2);
        oled.setCursor(0, 20);
        oled.print(temp, 1);
        oled.print("C");
        oled.setCursor(0, 42);
        oled.print(hum, 0);
        oled.print("%");
      }
      break;
    case 5:
      drawBar("5. Distance(cm)", (int)distance, 0, 100);
      break;
    case 6:
      drawStatus("6. Sound", soundValue == HIGH, "DETECTED", "quiet");
      break;
    case 7:
      drawStatus("7. Door/Reed", reedValue == HIGH, "OPEN", "CLOSED");
      break;
    case 8:
      drawStatus("8. Vibration", hitValue == LOW, "HIT!", "idle");
      break;
  }

  oled.display();
}

void sendSerialData() {
  Serial.print("switch:"); Serial.print(currentPage);
  Serial.print(",cds:"); Serial.print(cdsValue);
  Serial.print(",flame:"); Serial.print(flameValue);
  Serial.print(",water:"); Serial.print(waterValue);
  Serial.print(",sound:"); Serial.print(soundValue);
  Serial.print(",reed:"); Serial.print(reedValue);
  Serial.print(",hit:"); Serial.print(hitValue);
  Serial.print(",dist:"); Serial.print(distance);

  if (isnan(temp) || isnan(hum)) {
    Serial.print(",temp:NaN,hum:NaN");
  } else {
    Serial.print(",temp:"); Serial.print(temp);
    Serial.print(",hum:"); Serial.print(hum);
  }
  Serial.println();
}

void loop() {
  // ── 스위치: 눌리는 순간만 감지해서 다음 페이지로 ──
  int switchState = digitalRead(pinSwitch);
  if (switchState == LOW && lastSwitchState == HIGH) {
    currentPage = (currentPage + 1) % totalPages;
  }
  lastSwitchState = switchState;

  // ── 센서는 항상 수집 (화면 상태와 무관) ──
  readAllSensors();
  renderPage();
  sendSerialData();

  delay(150);
}