"""Overview schematic of the REAL water dispenser (12 V plan, schemdraw).

Run:  /home/shovol/Lab/iot/elefun/.venv/bin/python docs/schematic-real.py  -> docs/schematic-real.svg
Source of truth for pins is ../PINOUT.md. Only used pins are drawn. Labels match docs/wiring-*.yml.
"""
from pathlib import Path

import schemdraw
import schemdraw.elements as elm
from schemdraw.elements import IcPin

OUT = Path(__file__).with_name("schematic-real.svg")
ROW = 1.6  # vertical pitch between ESP32 pins

schemdraw.use("svg")
with schemdraw.Drawing(file=str(OUT), show=False) as d:
    d.config(unit=3, fontsize=11)

    # Right-hand pins, top to bottom (None = empty slot kept free for wiring).
    # schemdraw numbers slots bottom to top, so slot = len - index.
    right = ["D27", None, None, "D22", "D21", None, None, "D33", "D26", "D13", "D34", None, "D25"]
    n = len(right)
    pins = [IcPin(name="VIN", side="left", slot="3/3"),
            IcPin(name="3V3", side="left", slot="2/3"),
            IcPin(name="GND", side="left", slot="1/3")]
    pins += [IcPin(name=nm, side="right", slot=f"{n - i}/{n}")
             for i, nm in enumerate(right) if nm]
    esp = elm.Ic(
        pins=pins,
        size=(3.2, ROW * n),
        pinspacing=ROW,
        leadlen=1,
        edgepadding=0.4,
        lblsize=11,
    ).label("ESP32\n(DevKit V1)", "top", fontsize=12)
    d += esp

    def row(pin):
        return esp[pin]

    # ---- Left side: 12 V in -> fuse -> buck 12->5 V -> VIN; 3V3, GND ----
    buck = elm.Ic(
        pins=[IcPin(name="IN+", side="left", slot="2/2"),
              IcPin(name="IN-", side="left", slot="1/2"),
              IcPin(name="OUT+", side="right", slot="2/2"),
              IcPin(name="OUT-", side="right", slot="1/2")],
        size=(2.8, ROW * 2 + 0.6),
        pinspacing=ROW,
        leadlen=1,
        edgepadding=0.4,
        lblsize=10,
    ).label("BUCK_5V\n12 V to 5 V", "center", fontsize=10)
    vx, vy = row("VIN")
    d += buck.at((vx - 5.0, vy)).anchor("OUT+").theta(0)
    d += elm.Line().at(buck["OUT+"]).to(row("VIN"))
    d += elm.Line().at(buck["OUT-"]).down(0.4)
    d += elm.Ground()
    d += elm.Line().at(buck["IN-"]).down(0.4)
    d += elm.Ground()
    d += elm.Line().at(buck["IN+"]).left(0.5)
    d += elm.Fuse().left().label("FUSE_2A", loc="top", fontsize=10)
    d += elm.Line().left(0.5)
    d += elm.Vdd().label("+12 V")
    px_, py_ = d.here
    d += elm.Label().at((px_ - 0.1, py_ - 0.6)).label("PSU_12V", halign="left", fontsize=10)
    d += elm.Label().at((vx - 4.2, vy + 0.9)).label("+5 V", fontsize=10)

    # 3V3 is an OUTPUT of the board: drawn as a net label, never as a supply.
    d += elm.Line().at(esp["3V3"]).left(0.6)
    d += elm.Dot(open=True)
    d += elm.Label().at((esp["3V3"][0] - 0.8, esp["3V3"][1] + 0.35)).label(
        "3V3 (ESP32 output)", halign="right", fontsize=10)
    d += elm.Label().at((esp["3V3"][0] - 0.8, esp["3V3"][1] - 0.35)).label(
        "do not feed 3.3 V in", halign="right", fontsize=10)
    d += elm.Line().at(esp["GND"]).left(0.6)
    d += elm.Ground()

    # ---- D27 flow sensor input via divider (10k in series, 20k to GND) ----
    y27 = row("D27")[1]
    d += elm.Line().at(row("D27")).right(1.2)
    d += elm.Dot()
    jx, jy = d.here
    d += elm.Resistor().down().length(2.0)
    d += elm.Label().at((jx + 0.5, jy - 1.0)).label("20k", halign="left", fontsize=10)
    d += elm.Ground()
    d += elm.Label().at((jx + 0.5, jy - 2.0)).label("DIVIDER (10k + 20k)", halign="left", fontsize=10)
    d += elm.Line().at((jx, jy)).right(0.4)
    d += elm.Resistor().right().label("10k", loc="top")
    d += elm.Line().right(0.6)
    flow = elm.Ic(
        pins=[IcPin(name="SIG", side="left"),
              IcPin(name="5V", side="top"),
              IcPin(name="GND", side="bottom")],
        size=(2.4, 2.0),
        leadlen=0.8,
        edgepadding=0.3,
        lblsize=10,
    ).label("", fontsize=10)
    d += flow.anchor("SIG").theta(0)
    d += elm.Label().at((flow["5V"][0] + 1.5, flow["5V"][1] - 0.6)).label("FLOW\nYF-S201", halign="left", fontsize=10)
    d += elm.Line().at(flow["5V"]).up(0.4)
    d += elm.Vdd().label("+5 V")
    d += elm.Line().at(flow["GND"]).down(0.4)
    d += elm.Ground()

    # ---- D22 / D21 - OLED I2C (SCL top, SDA bottom) ----
    oled = elm.Ic(
        pins=[IcPin(name="SCL", side="left", slot="2/2"),
              IcPin(name="SDA", side="left", slot="1/2"),
              IcPin(name="VCC", side="top"),
              IcPin(name="GND", side="bottom")],
        size=(3.0, ROW * 2 + 1.0),
        pinspacing=ROW,
        leadlen=1,
        edgepadding=0.5,
        lblsize=10,
    ).label("OLED\nSSD1306 0x3C", "center", fontsize=10)
    d += oled.at((row("D22")[0] + 3.0, row("D22")[1])).anchor("SCL").theta(0)
    d += elm.Line().at(row("D22")).to(oled["SCL"])
    d += elm.Line().at(row("D21")).to(oled["SDA"])
    d += elm.Line().at(oled["VCC"]).up(0.4)
    d += elm.Dot(open=True)
    d += elm.Label().at((oled["VCC"][0], oled["VCC"][1] + 0.9)).label(
        "3V3 from ESP32", fontsize=10)
    d += elm.Line().at(oled["GND"]).down(0.4)
    d += elm.Ground()

    # ---- D33 - flow LED ----
    d += elm.Line().at(row("D33")).right(1.2)
    d += elm.Resistor().right().label("220", loc="top")
    d += elm.LED().right().color("green")
    d += elm.Line().right(0.4)
    gx, gy = d.here
    d += elm.Ground()
    d += elm.Label().at((gx + 0.4, gy - 0.1)).label("LED_FLOW (green)", halign="left", fontsize=10)

    # ---- D26 / D13 - buttons to GND (internal pull-up) ----
    for pin, name in (("D26", "BTN_START"), ("D13", "BTN_RESET")):
        d += elm.Line().at(row(pin)).right(1.2)
        d += elm.Button().right().label(name, loc="top")
        d += elm.Line().right(0.6)
        d += elm.Ground()

    # ---- D34 - volume pot (10k): ends to 3V3 and GND, wiper to D34 ----
    yb = row("D34")[1]
    px = row("D34")[0] + 6.5
    pot = elm.Potentiometer().up().at((px, yb - 1.5))
    d += pot
    d += elm.Line().at(pot.start).down(0.4)
    d += elm.Ground()
    d += elm.Line().at(pot.end).up(0.3)
    d += elm.Dot(open=True)
    d += elm.Label().at((pot.end[0], pot.end[1] + 0.8)).label(
        "3V3 from ESP32", fontsize=10)
    d += elm.Line().at(row("D34")).to(pot.tap)
    d += elm.Label().at((px + 0.9, yb)).label("POT_VOLUME\n10k", halign="left", fontsize=10)

    # ---- D25 - LED_VALVE and D4184 trigger ----
    x25, y25 = row("D25")
    d += elm.Line().at(row("D25")).right(1.0)
    d += elm.Dot()
    tx, ty = d.here
    d += elm.Resistor().right().label("220", loc="top")
    d += elm.LED().right().color("red")
    d += elm.Line().right(0.4)
    gx, gy = d.here
    d += elm.Ground()
    d += elm.Label().at((gx + 0.4, gy - 0.1)).label("LED_VALVE (red)", halign="left", fontsize=10)

    drv = elm.Ic(
        pins=[IcPin(name="TRIG", side="left", slot="2/2"),
              IcPin(name="GND", side="left", slot="1/2"),
              IcPin(name="VIN-", side="bottom"),
              IcPin(name="OUT-", side="right")],
        size=(3.2, 2.6),
        pinspacing=ROW,
        leadlen=1,
        edgepadding=0.5,
        lblsize=10,
    ).label("DRIVER_D4184", "top", fontsize=10)
    y_d = y25 - 5.0
    d += drv.at((tx + 1.5, y_d)).anchor("TRIG").theta(0)
    d += elm.Line().at((tx, ty)).to((tx, y_d))
    d += elm.Line().to(drv["TRIG"])
    d += elm.Line().at(drv["GND"]).left(0.5)
    d += elm.Ground()
    d += elm.Line().at(drv["VIN-"]).down(0.4)
    d += elm.Ground()

    # Valve between OUT- and +12 V, flyback diode across it (cathode to +12 V)
    d += elm.Line().at(drv["OUT-"]).right(1.2)
    d += elm.Dot()
    ax, ay = d.here
    d += elm.Line().right(1.6)
    d += elm.Dot()
    bx, _ = d.here
    d += elm.Inductor2(loops=3).at((ax, ay)).up().length(3.0).label(
        "", fontsize=10)
    d += elm.Label().at((ax - 0.6, ay + 1.5)).label("VALVE", halign="right", fontsize=10)
    top_y = ay + 3.0
    d += elm.Diode().at((bx, ay)).up().length(3.0).label(
        "DIODE_FLYBACK\n1N4007", loc="right", fontsize=10)
    d += elm.Line().at((ax, top_y)).to((bx, top_y))
    d += elm.Dot().at((ax, top_y))
    d += elm.Line().at((ax, top_y)).up(0.4)
    d += elm.Vdd().label("+12 V")
