"""Scan all GPIO inputs WITH the NeoPixel controller initialized, to learn
whether NeoPixel-on-GPIO-10 kills only pin 26 or all GPIO reads.

Run ON the Pi from the repo root:
    python3.10 experiments/scan_with_led.py

It inits the NeoPixel controller (LEDs blanked), prints the idle level of every
candidate pin, then watches for changes while you press the button (still on 26).

Compare the printed idle map to the no-NeoPixel scan (button_test.py --scan),
which was: most pins=1, pin 26=0.

Interpretation:
- idle map looks the same and pin 26 toggles when pressed -> NeoPixel init is
  fine here; something else. (unlikely given prior tests)
- pin 26 dead but OTHER pins still read 1 and respond -> the damage is pin/bank
  specific. Move the BUTTON wire to a pin that still works, update USE_GPIO.touch.
- many/all pins forced to 0 or unresponsive -> NeoPixel init broadly clobbers
  GPIO inputs. Fix the LED side: move NeoPixel data to GPIO 18 or 21 (the
  recommended pins) and update USE_GPIO.led.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import RPi.GPIO as GPIO
import lib.plantoid.gpio_utils as g

SCAN_PINS = [4, 5, 6, 12, 13, 16, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27]


def main() -> None:
    print("init NeoPixel controller on GPIO 10 (LEDs blanked)...")
    led = g.GPIOLEDController(10)
    led.running = False
    time.sleep(0.3)
    try:
        led.pixels.fill((0, 0, 0))
        led.pixels.show()
    except Exception:
        pass
    time.sleep(0.3)

    GPIO.setmode(GPIO.BCM)
    for p in SCAN_PINS:
        try:
            GPIO.setup(p, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        except Exception as e:
            print(f"  (skip {p}: {e})")
    last = {p: GPIO.input(p) for p in SCAN_PINS}
    print("idle levels WITH NeoPixel init:", {p: last[p] for p in SCAN_PINS})
    print("compare to no-NeoPixel: most pins=1, pin 26=0")
    print("now press the button (on 26). Ctrl+C to stop.")
    try:
        while True:
            for p in SCAN_PINS:
                cur = GPIO.input(p)
                if cur != last[p]:
                    print(f"  >>> BCM {p}: {last[p]} -> {cur}")
                    last[p] = cur
            time.sleep(0.02)
    except KeyboardInterrupt:
        print("\nstopped.")
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()
