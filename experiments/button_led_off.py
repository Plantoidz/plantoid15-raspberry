"""Disambiguate: is the button-read failure caused by NeoPixel *initializing*
(hardware reconfig) or by LED *current draw* (power sag)?

Run ON the Pi from the repo root:
    python3.10 experiments/button_led_off.py

It initializes the NeoPixel controller (so the rpi_ws281x hardware is set up
exactly like the runtime) but then STOPS the animation and blanks the LEDs to
~zero current, and reads pin 26.

Interpretation:
- pin 26 toggles now (LEDs initialized but OFF) -> the failure is LED CURRENT
  DRAW / power sag, not software. Fix is power (separate/!beefier supply,
  decoupling, fewer/dimmer LEDs) -- ties to the USB over-current issue.
- pin 26 still stuck at 0 -> NeoPixel INITIALIZATION reconfigures the GPIO
  hardware. Fix is software/wiring (different LED drive method or move the
  button off the affected bank).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import RPi.GPIO as GPIO
import lib.plantoid.gpio_utils as g

PIN = 26


def main() -> None:
    print("init NeoPixel controller on GPIO 10, then BLANK it (LEDs off)...")
    led = g.GPIOLEDController(10)
    led.running = False                 # stop the animation thread
    time.sleep(0.3)
    try:
        led.pixels.fill((0, 0, 0))     # all LEDs off -> ~zero current
        led.pixels.show()
    except Exception as e:
        print(f"(couldn't blank pixels: {e})")
    time.sleep(0.3)

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    last = GPIO.input(PIN)
    print(f"reading BCM {PIN} (NeoPixel initialized but LEDs OFF); idle = {last}.")
    print("press the button (Ctrl+C to stop)...")
    presses = 0
    try:
        while True:
            cur = GPIO.input(PIN)
            if cur != last:
                if cur == 1:
                    presses += 1
                print(f"  pin {PIN}: {last} -> {cur}   (presses: {presses})")
                last = cur
            time.sleep(0.02)
    except KeyboardInterrupt:
        print(f"\nstopped. HIGH transitions seen: {presses}")
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()
