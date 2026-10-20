# Pinout — water dispenser

Board: ESP32 DevKit V1, 30-pin (HW-394 clone, USB-C). Keep this table in sync with
`src/main.cpp`, `diagram.json` and `docs/wiring.yml`.

| GPIO | Board label | Direction | Connected to | Notes |
|------|-------------|-----------|--------------|-------|
| 34 | D34 | in (ADC) | Volume pot, wiper | Input-only pin. Pot ends to 3V3 and GND. |
| 35 | D35 | in (ADC) | Flow-rate pot, wiper (optional) | Simulator only, `HAS_RATE_POT=1`. |
| 26 | D26 | in, pull-up | START button → GND | Start, pause, resume. |
| 13 | D13 | in, pull-up | RESET button → GND | Abort, clear count, back to idle. |
| 27 | D27 | in, pull-up, IRQ | Flow sensor signal | **3.3 V max.** YF-S201 outputs 5 V: use a divider (10k/20k) or a level shifter. |
| 32 | D32 | out | Jumper → D27 | Simulator output. Remove jumper with the real sensor. |
| 25 | D25 | out | Valve LED (red) + 220 Ω → GND | Real device: also the D4184 module TRIG input. |
| 33 | D33 | out | Flow LED (green) + 220 Ω → GND | Lit while pulses arrive. |
| 21 | D21 | I2C SDA | OLED SDA | SSD1306 128×64, addr 0x3C. |
| 22 | D22 | I2C SCL | OLED SCL | |
| — | 3V3 | power | Pot, OLED VCC | |
| — | GND | power | Everything | All GND pins are common. |

## Free pins worth knowing about

- **GPIO2 (D2)** drives the onboard blue LED. Usable as a spare indicator.
- Avoid for inputs at boot: GPIO0, 2, 12, 15 (strapping pins).
- GPIO34–39 are input-only and have no internal pull-ups.

## Real device (decided 12 V plan)

Build with `pio run -e real`. No D32 → D27 jumper. Step-by-step guide for the electrician:
[docs/INSTALL.md](docs/INSTALL.md); diagrams: `docs/schematic-real.svg` (overview), `docs/wiring-power.yml`, `docs/wiring-valve.yml`, `docs/wiring-esp.yml`.

| Function | Plan | Notes |
|----------|------|-------|
| Power | 12 V DC PSU, ≥ 2 A, inline 2 A fuse on +12 V | |
| 5 V rail | Buck module (LM2596 or MP1584) 12 V → 5.0 V into ESP32 VIN + GND | Set to 5.0 V with a multimeter **before** connecting the ESP32. |
| Valve | 12 V DC normally-closed solenoid, 1/2" | **Open:** type depends on supply. Pressurized line: pilot-operated is ok. Gravity tank / low pressure: direct-acting (zero-pressure). Check its current against the driver. |
| Driver | D4184 dual-MOSFET module, TRIG from D25 | 3.3 V logic ok. Load: +12 V → valve → module OUT-. Do not use IRF520 modules. |
| Flyback diode | 1N4007 or 1N5819 across the valve coil | Cathode (stripe) to +12 V. Skip only if the module has one. |
| Flow sensor | YF-S201 or YF-B5: red → 5 V, black → GND, yellow → D27 via divider | Divider: 10k (signal to D27) + 20k (D27 to GND). Calibrate `PULSES_PER_LITER`. |
| OLED | SSD1306 on 3V3, SDA D21, SCL D22 | |
| Controls | Pot D34 (ends 3V3 / GND), START D26 → GND, RESET D13 → GND | Internal pull-ups, no resistors. |
| LEDs | Valve D25, flow D33, each with 220 Ω to GND | Optional, recommended. |
| Grounds | PSU −, buck out −, ESP GND, driver GND, sensor black | All common. |
