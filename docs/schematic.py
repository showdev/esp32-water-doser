"""Schematic of the water-dispenser bench stub (schemdraw).

Run:  /home/shovol/Lab/iot/elefun/.venv/bin/python docs/schematic.py  -> docs/schematic.svg
Source of truth for pins is ../PINOUT.md. Only used pins are drawn.
"""
from pathlib import Path

import schemdraw
import schemdraw.elements as elm
from schemdraw.elements import IcPin

OUT = Path(__file__).with_name("schematic.svg")
ROW = 1.6  # vertical pitch between ESP32 pins

schemdraw.use("svg")
with schemdraw.Drawing(file=str(OUT), show=False) as d:
    d.config(unit=3, fontsize=11)

    # Right-hand pins, top to bottom. schemdraw numbers slots bottom to top,
    # so slot = len - index.
    right = ["D22", "D21", "D27", "D32", "D33", "D25", "D26", "D13", "D34"]
    n = len(right)
    esp = elm.Ic(
        pins=[IcPin(name="3V3", side="left", slot="2/2"),
              IcPin(name="GND", side="left", slot="1/2")]
             + [IcPin(name=nm, side="right", slot=f"{n - i}/{n}")
                for i, nm in enumerate(right)],
        size=(3.2, ROW * n),
        pinspacing=ROW,
        leadlen=1,
        edgepadding=0.4,
        lblsize=11,
    ).label("ESP32 DevKit V1\n(30-pin)", "top", fontsize=12)
    d += esp

    # Left side: power rails.
    d += elm.Line().at(esp["3V3"]).left(0.6)
    d += elm.Vdd().label("3V3")
    d += elm.Line().at(esp["GND"]).left(0.6)
    d += elm.Ground()

    def row(pin):
        return esp[pin]

    # D22 / D21 - OLED I2C (SCL top, SDA bottom)
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
    ).label("SSD1306 OLED\n0x3C", "center", fontsize=10)
    d += oled.at((row("D22")[0] + 3.0, row("D22")[1])).anchor("SCL").theta(0)
    d += elm.Line().at(row("D22")).to(oled["SCL"])
    d += elm.Line().at(row("D21")).to(oled["SDA"])
    d += elm.Line().at(oled["VCC"]).up(0.4)
    d += elm.Vdd().label("3V3")
    d += elm.Line().at(oled["GND"]).down(0.4)
    d += elm.Ground()

    # D27 flow sensor input; D32 simulator output jumpered to it.
    y32, y27 = row("D32")[1], row("D27")[1]
    x_loop = row("D32")[0] + 2.2
    d += elm.Line().at(row("D32")).right(2.2)
    d += elm.Line().to((x_loop, y27))
    d += elm.Line().to(row("D27"))
    d += elm.Dot().at((x_loop, y27))
    d += elm.Line().at((x_loop, y27)).right(0.8)
    d += elm.Label().at((x_loop + 0.9, y27 - 0.4)).label(
        "flow sensor in\n(3.3 V max)", halign="left", fontsize=10)
    d += elm.Label().at((x_loop + 0.2, y32 - 0.4)).label(
        "sim jumper (remove\nfor real sensor)", halign="left", fontsize=10)

    # D33 - flow LED
    d += elm.Line().at(row("D33")).right(1.2)
    d += elm.Resistor().right().label("220", loc="top")
    d += elm.LED().right().color("green")
    d += elm.Line().right(0.4)
    gx, gy = d.here
    d += elm.Ground()
    d += elm.Label().at((gx + 0.4, gy - 0.1)).label("flow LED (green)", halign="left", fontsize=10)

    # D25 - valve LED
    d += elm.Line().at(row("D25")).right(1.2)
    d += elm.Resistor().right().label("220", loc="top")
    d += elm.LED().right().color("red")
    d += elm.Line().right(0.4)
    gx, gy = d.here
    d += elm.Ground()
    d += elm.Label().at((gx + 0.4, gy - 0.1)).label("valve LED (red)", halign="left", fontsize=10)

    # D26 - START button to GND (internal pull-up)
    d += elm.Line().at(row("D26")).right(1.2)
    d += elm.Button().right().label("START", loc="top")
    d += elm.Line().right(0.6)
    d += elm.Ground()

    # D13 - RESET button to GND (internal pull-up)
    d += elm.Line().at(row("D13")).right(1.2)
    d += elm.Button().right().label("RESET", loc="top")
    d += elm.Line().right(0.6)
    d += elm.Ground()

    # D34 - volume pot (10k): ends to 3V3 and GND, wiper to D34
    yb = row("D34")[1]
    px = row("D34")[0] + 6.5
    pot = elm.Potentiometer().up().at((px, yb - 1.5))
    d += pot
    d += elm.Line().at(pot.start).down(0.4)
    d += elm.Ground()
    d += elm.Line().at(pot.end).up(0.3)
    d += elm.Vdd().label("3V3")
    d += elm.Line().at(row("D34")).to(pot.tap)
    d += elm.Label().at((px + 0.9, yb)).label("10k volume pot", halign="left", fontsize=10)
