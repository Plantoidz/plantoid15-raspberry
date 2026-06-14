"""Decisive test: read the button via Adafruit Blinka digitalio (the SAME
stack NeoPixel uses) while the NeoPixel LED controller is active.

Run ON the Pi, from the repo root:
    python3.10 experiments/button_digitalio.py

Background: with the LED controller running, reading pin 26 via RPi.GPIO
always returns 0 (RPi.GPIO and rpi_ws281x fight over the GPIO registers).
digitalio shares Blinka's GPIO backend with NeoPixel, so they should coexist.

Interpretation:
- pin 26 toggles here WITH the LED active -> digitalio is the fix; rewrite
  check_if_talk() to use digitalio instead of RPi.GPIO.
- still stuck at 0 -> not a library conflict; it's power (rail sag under load,
  ties back to the USB over-current issue).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import board
import digitalio

import lib.plantoid.gpio_utils as g

PIN = 26


def main() -> None:
    print("starting NeoPixel LED controller on GPIO 10 (like the runtime)...")
    led = g.GPIOLEDController(10)
    led.set_state("listening")
    time.sleep(0.5)

    btn = digitalio.DigitalInOut(getattr(board, f"D{PIN}"))
    btn.direction = digitalio.Direction.INPUT
    btn.pull = digitalio.Pull.DOWN   # active-high sensor: idle LOW, touch HIGH

    last = btn.value
    print(f"reading D{PIN} via digitalio (LED active); idle = {int(last)}.")
    print("press the button (Ctrl+C to stop)...")
    presses = 0
    try:
        while True:
            v = btn.value
            if v != last:
                if v:
                    presses += 1
                print(f"  pin {PIN}: {int(last)} -> {int(v)}   (presses: {presses})")
                last = v
            time.sleep(0.02)
    except KeyboardInterrupt:
        print(f"\nstopped. HIGH transitions seen: {presses}")
    finally:
        btn.deinit()
        led.running = False   # stop the animation thread without join-hang


if __name__ == "__main__":
    main()
