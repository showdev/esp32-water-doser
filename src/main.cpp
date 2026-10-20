// Water dispenser — ESP32 DevKit V1
//
// Pot sets a volume, button starts dispensing, the flow sensor counts pulses,
// the valve closes when the target is reached (or on no-flow / button stop).
//
// SIMULATE_FLOW=1 (env:sim): the ESP32 generates fake flow-sensor pulses on
// SIM_OUT_PIN while the valve is open. Wire SIM_OUT_PIN -> FLOW_PIN with a
// jumper and the real interrupt-counting path is exercised end to end.
// SIMULATE_FLOW=0 (env:real): remove the jumper, connect the real sensor.
//
// Pin map: see ../PINOUT.md. Keep the two in sync.

#include <Arduino.h>
#include <U8g2lib.h>
#include <Wire.h>

#ifndef SIMULATE_FLOW
#define SIMULATE_FLOW 1
#endif
#ifndef HAS_RATE_POT
#define HAS_RATE_POT 0
#endif

// ===== Pins =====
const int POT_PIN      = 34;  // volume pot (input-only ADC pin)
const int RATE_POT_PIN = 35;  // optional flow-rate pot for the simulator
const int BUTTON_PIN   = 26;  // to GND, internal pull-up
const int FLOW_PIN     = 27;  // flow sensor signal (3.3 V level!)
const int SIM_OUT_PIN  = 32;  // simulator output, jumper to FLOW_PIN
const int VALVE_PIN    = 25;  // LED now, relay/MOSFET later
const int FLOW_LED_PIN = 33;  // "water is flowing" LED
// OLED SSD1306 I2C: SDA=21, SCL=22 (hardware I2C defaults)

// ===== Tuning =====
const float PULSES_PER_LITER = 450.0;   // YF-S201 nominal; CALIBRATE
const float MAX_LITERS       = 5.0;     // pot fully clockwise
const float DEFAULT_LPM      = 6.0;     // simulator rate without rate pot
const float MAX_LPM          = 30.0;
const unsigned long MIN_PULSES          = 10;
const unsigned long NO_FLOW_TIMEOUT_MS  = 5000;
const unsigned long FLOW_LED_HOLD_MS    = 300;
const unsigned long DEBOUNCE_MS         = 50;
const unsigned long DRAW_INTERVAL_MS    = 150;

U8G2_SSD1306_128X64_NONAME_F_HW_I2C oled(U8G2_R0, U8X8_PIN_NONE);
// If the screen stays blank, it may be an SH1106:
// U8G2_SH1106_128X64_NONAME_F_HW_I2C oled(U8G2_R0, U8X8_PIN_NONE);

portMUX_TYPE pulseMux = portMUX_INITIALIZER_UNLOCKED;
volatile unsigned long pulseCount  = 0;
volatile unsigned long lastPulseMs = 0;
volatile bool valveOpen = false;

bool running = false;
unsigned long targetPulses = 0;
const char* statusMsg = "Готово";

void IRAM_ATTR onPulse() {
  portENTER_CRITICAL_ISR(&pulseMux);
  pulseCount++;
  lastPulseMs = millis();
  portEXIT_CRITICAL_ISR(&pulseMux);
}

void readPulses(unsigned long& count, unsigned long& lastMs) {
  portENTER_CRITICAL(&pulseMux);
  count  = pulseCount;
  lastMs = lastPulseMs;
  portEXIT_CRITICAL(&pulseMux);
}

void resetPulses() {
  portENTER_CRITICAL(&pulseMux);
  pulseCount  = 0;
  lastPulseMs = millis();
  portEXIT_CRITICAL(&pulseMux);
}

float readLiters() {
  long sum = 0;
  for (int i = 0; i < 16; i++) sum += analogRead(POT_PIN);  // smoothing
  return (sum / 16.0f / 4095.0f) * MAX_LITERS;
}

void setValve(bool open) {
  valveOpen = open;
  digitalWrite(VALVE_PIN, open ? HIGH : LOW);
}

// ===== Flow simulator (core 0, so OLED redraws don't stall it) =====
#if SIMULATE_FLOW
void simTask(void*) {
  bool level = HIGH;
  unsigned long lastToggle = micros();
  for (;;) {
    if (valveOpen) {
      float lpm = DEFAULT_LPM;
#if HAS_RATE_POT
      lpm = analogRead(RATE_POT_PIN) / 4095.0f * MAX_LPM;
#endif
      if (lpm >= 0.5f) {
        unsigned long halfPeriodUs = 500000.0f / (lpm * PULSES_PER_LITER / 60.0f);
        if (micros() - lastToggle >= halfPeriodUs) {
          lastToggle = micros();
          level = !level;
          digitalWrite(SIM_OUT_PIN, level);
        }
      }
    } else {
      digitalWrite(SIM_OUT_PIN, HIGH);
      level = HIGH;
    }
    vTaskDelay(1);  // 1 tick = 1 ms -> max ~500 Hz, enough for ~66 L/min
  }
}
#endif

void startDispense() {
  float liters = readLiters();
  targetPulses = (unsigned long)(liters * PULSES_PER_LITER);
  if (targetPulses < MIN_PULSES) { statusMsg = "Замало"; return; }
  resetPulses();
  running = true;
  setValve(true);
  statusMsg = "Наливаю";
  Serial.printf("START target=%.2f L (%lu pulses)\n", liters, targetPulses);
}

void stopDispense(const char* reason) {
  setValve(false);
  running = false;
  statusMsg = reason;
  unsigned long c, lp;
  readPulses(c, lp);
  Serial.printf("STOP (%s) poured=%.2f L (%lu pulses)\n", reason, c / PULSES_PER_LITER, c);
}

// Returns true once per debounced press (HIGH -> LOW edge).
bool buttonPressed() {
  static bool stable = HIGH, lastRaw = HIGH;
  static unsigned long changedAt = 0;
  bool raw = digitalRead(BUTTON_PIN);
  if (raw != lastRaw) { lastRaw = raw; changedAt = millis(); }
  if (millis() - changedAt > DEBOUNCE_MS && raw != stable) {
    stable = raw;
    return stable == LOW;
  }
  return false;
}

void drawScreen(bool flowing, unsigned long count) {
  oled.clearBuffer();
  oled.setFont(u8g2_font_6x13_t_cyrillic);
  oled.setCursor(0, 11);
  oled.print(statusMsg);
  if (flowing) { oled.setCursor(98, 11); oled.print("~~~"); }

  float target = running ? targetPulses / PULSES_PER_LITER : readLiters();
  float poured = count / PULSES_PER_LITER;

  oled.setFont(u8g2_font_logisoso22_tn);
  oled.setCursor(0, 42);
  oled.print(running ? poured : target, 2);

  oled.setFont(u8g2_font_6x13_t_cyrillic);
  oled.setCursor(70, 42);
  if (running) { oled.print("/ "); oled.print(target, 2); }
  else oled.print("л");

  if (running && targetPulses > 0) {
    int w = (int)min(128UL, count * 128UL / targetPulses);
    oled.drawFrame(0, 52, 128, 12);
    oled.drawBox(0, 52, w, 12);
  } else {
    oled.setCursor(0, 62);
    oled.print("Кнопка = старт");
  }
  oled.sendBuffer();
}

void setup() {
  Serial.begin(115200);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(VALVE_PIN, OUTPUT);
  setValve(false);
  pinMode(FLOW_LED_PIN, OUTPUT);
  digitalWrite(FLOW_LED_PIN, LOW);
  pinMode(FLOW_PIN, INPUT_PULLUP);
#if SIMULATE_FLOW
  pinMode(SIM_OUT_PIN, OUTPUT);
  digitalWrite(SIM_OUT_PIN, HIGH);
  xTaskCreatePinnedToCore(simTask, "sim", 2048, NULL, 1, NULL, 0);
  Serial.println("Flow SIMULATOR on: jumper GPIO32 -> GPIO27");
#endif
  attachInterrupt(digitalPinToInterrupt(FLOW_PIN), onPulse, FALLING);
  oled.begin();
  oled.enableUTF8Print();
}

void loop() {
  if (buttonPressed()) {
    if (!running) startDispense();
    else stopDispense("Стоп кнопкою");
  }

  unsigned long count, lastMs;
  readPulses(count, lastMs);
  bool flowing = millis() - lastMs < FLOW_LED_HOLD_MS;
  digitalWrite(FLOW_LED_PIN, flowing ? HIGH : LOW);

  if (running) {
    if (count >= targetPulses) stopDispense("Готово!");
    else if (millis() - lastMs > NO_FLOW_TIMEOUT_MS) stopDispense("Немає води!");
  }

  static unsigned long lastDraw = 0;
  if (millis() - lastDraw > DRAW_INTERVAL_MS) {
    lastDraw = millis();
    drawScreen(flowing, count);
  }
}
