# Plan: simulated water line in Wokwi

Status: **planned, not started.** Written to be executed step by step (by a person or Claude Code).
Tick the boxes as tasks land; keep this file updated if the design changes.

## Goal

Today the Wokwi bench has no water and no flow sensor: the firmware (`env:sim`) fakes its own
pulses on D32, jumpered to D27. So the simulation tests a code path that never runs on the device.

Replace that with a **custom Wokwi chip that models the water line + YF-S201 sensor**, driven by the
valve output. Then Wokwi runs the **real firmware** (`SIMULATE_FLOW=0`) and scenarios can test
things the fake can't: water running out mid-pour, changing flow, overshoot after the valve closes.

The hardware bench keeps `env:sim` + jumper until a real sensor is bought. Nothing changes for the
real device or INSTALL.md.

## Design

### The chip: `water-line`

```
            +----------------------+
  D25 ----> | VALVE         PULSE  | ----> D27   (3.3 V logic, no divider needed in Wokwi)
  pot ----> | RATE (analog)        |
  switch -> | SUPPLY               |
  3V3 ----> | VCC            GND   | ----> GND
            +----------------------+
```

| Pin | Dir | Meaning |
|-----|-----|---------|
| `VALVE` | in | HIGH = valve open (from D25) |
| `RATE` | analog in | 0–VCC → 0–`maxLpm` L/min. Wired to a regular `wokwi-potentiometer` |
| `SUPPLY` | in | HIGH = water available. Wired to a `wokwi-slide-switch` (or pushbutton) |
| `PULSE` | out | Square wave, `pulsesPerLiter` per litre, idles HIGH like the YF-S201 open collector + pull-up |
| `VCC`, `GND` | power | |

Why physical parts for rate/supply instead of chip controls: scenarios can reliably drive
`wokwi-potentiometer` (`position`) and buttons/switches. Driving a custom chip's own controls from a
scenario is unverified (see Open questions).

### Attributes (set in `diagram.json`, defaults in brackets)

| Attr | Default | Meaning |
|------|---------|---------|
| `pulsesPerLiter` | 450 | Sensor constant. Set ≠ firmware value to test calibration error |
| `maxLpm` | 30 | Flow at RATE = VCC |
| `tauOpenMs` | 150 | Flow rise time constant after the valve opens |
| `tauCloseMs` | 300 | Flow decay after the valve closes → produces overshoot |

### Behaviour model (1 ms timer)

```
target = (VALVE && SUPPLY) ? rate_from_RATE_pin : 0          // L/min
tau    = (target > flow) ? tauOpenMs : tauCloseMs
flow  += (target - flow) * dt / tau                           // first-order lag
if flow < 0.05: flow = 0
phase += flow / 60 * pulsesPerLiter * 2 * dt                  // half-periods
while phase >= 1: toggle PULSE; phase -= 1
```

Max useful rate: 30 L/min × 450 / 60 = 225 Hz → half-period ~2.2 ms. A 1 ms tick is enough;
use a 250 µs tick if jitter matters.

### Files

```
esp32-water-doser/
  chips/water-line.chip.json     pins, attrs (+ optional controls for manual play)
  chips/water-line.chip.c        model above, Wokwi Chips API (wokwi-api.h)
  chips/water-line.chip.wasm     build output (commit it, or build in CI — decide in task 2)
  wokwi.toml                     [[chip]] entry, firmware path -> env:wokwi
  diagram.json                   chip + rate pot + supply switch (+ optional relay module)
  test/*.test.yaml               scenarios moved to real firmware
```

`wokwi.toml` addition:

```toml
[[chip]]
name = 'water-line'
binary = 'chips/water-line.chip.wasm'
```

Part in `diagram.json`: `{ "type": "chip-water-line", "id": "water", ... }`.

## Tasks

### 1. Firmware and build envs
- [ ] Add `[env:wokwi]` to `platformio.ini`: same flags as `real` (`SIMULATE_FLOW=0`). Separate env so
      Wokwi builds don't collide with the device build.
- [ ] Point `wokwi.toml` firmware/elf to `.pio/build/wokwi/`.
- [ ] Optional but useful on the real device too: 1 s after every STOP/PAUSE, log
      `OVERSHOOT pulses=<n> (<litres> L)` — pulses that arrived after the valve closed.
      Scenarios assert on it; on site it tells how many pulses to stop early.

### 2. Chip
- [ ] `water-line.chip.json` with pins and attrs above.
- [ ] `water-line.chip.c`: `chip_init` → `pin_init`, `attr_init`, `timer_init` + `timer_start(…, 1000, true)`;
      read `RATE` with `pin_adc_read`, `VALVE`/`SUPPLY` with `pin_read`; write `PULSE`.
- [ ] Build to `.wasm`. Check the current official way first (Wokwi docs "Custom Chips"):
      `wokwi-cli` chip build command if available, else clang + wasi-sdk
      (`--target=wasm32-unknown-wasi -nostartfiles -Wl,--import-memory -Wl,--export-table -Wl,--no-entry`),
      or the `wokwi/wokwi-chip-clang-action` GitHub Action.
- [ ] Decide: commit the `.wasm` (simple, works in VS Code extension immediately) vs. build in CI.
      Default: commit it, plus a `chips/Makefile` or script to rebuild.

### 3. Circuit
- [ ] `diagram.json`: add `water` chip, `potRate` (→ `water:RATE`), `swSupply` (→ `water:SUPPLY`),
      `water:VALVE` ← `esp:D25`, `water:PULSE` → `esp:D27`.
- [ ] Remove the `esp:D32` → `esp:D27` jumper from the Wokwi circuit (keep it on the hardware bench).
- [ ] Optional: `wokwi-relay-module` on D25 so the "valve" clicks and lights like the real driver.
- [ ] Manual check in VS Code: knob → START → green LED, progress bar; flip supply off → `Немає води!`.

### 4. Scenarios (`test/`)
- [ ] `dispense`: set `potRate`, pour 1 L, `STOP (Готово!)`. Expected time ≈ 1 L / rate.
- [ ] `pause-resume`, `reset`: port to the new circuit (no logic change expected).
- [ ] New `no-water`: start, switch supply off mid-pour → `PAUSE (Немає води!)` after ~5 s;
      supply on, START → `RESUME` → `STOP (Готово!)`.
- [ ] New `variable-flow`: change `potRate` during a pour; poured volume must still stop at target.
- [ ] New `overshoot` (needs task 1 optional log): pour, assert `OVERSHOOT` line appears; with
      `tauCloseMs` = 300 and 6 L/min expect roughly 0.03 L. Use it to tune early-stop compensation later.
- [ ] Add a `test/README.md` or a README section listing scenarios and the run command.

### 5. Docs and conventions
- [ ] `README.md`: Wokwi section → `pio run -e wokwi`, chip, new scenarios; roadmap tick.
- [ ] `PINOUT.md`: note that in Wokwi D27 is driven by the `water-line` chip, D32 unused there;
      D35 rate pot is replaced by the chip's own rate pot in Wokwi.
- [ ] `CLAUDE.md` (repo root): add chip build command and `env:wokwi`.
- [ ] `docs/schematics-and-mockups.md`: short "Custom chips" note under Wokwi.

### 6. Verify
- [ ] `pio run -e sim`, `pio run -e real`, `pio run -e wokwi` all build.
- [ ] All scenarios pass with `wokwi-cli --scenario test/<name>.test.yaml --timeout 30000 .`
- [ ] Manual run in the VS Code extension looks right.
- [ ] Hardware bench (`env:sim` + jumper) still works unchanged.

## Open questions

1. Can a scenario `set-control` a custom chip's own controls? If yes, rate/supply can move into the
   chip and the extra pot/switch go away. Until verified, use physical parts (design above).
2. Which `set-control` the slide switch supports in scenarios; fallback is a pushbutton held
   pressed = "no water".
3. `.wasm` in git vs. CI build (task 2).
4. Should `env:sim` eventually be dropped? Keep it while the hardware bench has no real sensor.

## Out of scope

- Hardware bench with a real valve/sensor (tap or bucket + pump rig): separate plan once parts arrive.
- Changes to the real-device wiring or INSTALL.md.
