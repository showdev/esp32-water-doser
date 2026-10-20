# Pinout — water dispenser

Board: ESP32 DevKit V1, 30-pin (HW-394 clone, USB-C). Keep this table in sync with
`src/main.cpp`, `diagram.json` and `docs/wiring.yml`.

| GPIO | Board label | Direction | Connected to | Notes |
|------|-------------|-----------|--------------|-------|
| 34 | D34 | in (ADC) | Volume pot, wiper | Input-only pin. Pot ends to 3V3 and GND. |
| 35 | D35 | in (ADC) | Flow-rate pot, wiper (optional) | Simulator only, `HAS_RATE_POT=1`. |
| 26 | D26 | in, pull-up | Start/stop button → GND | Second press = emergency stop. |
| 27 | D27 | in, pull-up, IRQ | Flow sensor signal | **3.3 V max.** YF-S201 outputs 5 V: use a divider (10k/20k) or a level shifter. |
| 32 | D32 | out | Jumper → D27 | Simulator output. Remove jumper with the real sensor. |
| 25 | D25 | out | Valve LED (red) + 220 Ω → GND | Later: relay / MOSFET module input. |
| 33 | D33 | out | Flow LED (green) + 220 Ω → GND | Lit while pulses arrive. |
| 21 | D21 | I2C SDA | OLED SDA | SSD1306 128×64, addr 0x3C. |
| 22 | D22 | I2C SCL | OLED SCL | |
| — | 3V3 | power | Pot, OLED VCC | |
| — | GND | power | Everything | All GND pins are common. |

## Free pins worth knowing about

- **GPIO2 (D2)** drives the onboard blue LED. Usable as a spare indicator.
- Avoid for inputs at boot: GPIO0, 2, 12, 15 (strapping pins).
- GPIO34–39 are input-only and have no internal pull-ups.

## Later stage (on site, not decided yet)

| Function | Plan | Open question |
|----------|------|---------------|
| Valve | 12 V NC solenoid, driven from D25 | Pressure in the line? Tank without pressure needs a direct-acting valve. |
| Driver | D4184 MOSFET module or opto relay | Depends on valve current and voltage. |
| Flow sensor | YF-S201 or YF-B5 (brass) on D27 | Calibrate `PULSES_PER_LITER`. |
| Power | 12 V 2 A PSU + buck to 5 V for ESP32 VIN | |
