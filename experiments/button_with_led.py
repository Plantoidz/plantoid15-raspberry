"""Reproduce the runtime's button read in isolation. Run ON the Pi, from the
repo root: `python3.10 experiments/button_with_led.py`

The standalone scan reads pin 26 fine, but inside Plantoid.py it always reads
0. The difference: the runtime starts the NeoPixel LED controller (GPIO 10)
*before* reading the button, and runs under load. This script reproduces that
exact order, then polls pin 26 at ~50 Hz (fast, so slow sampling is NOT the
variable) and prints every change.

Toggle the LED load with --led to see if driving the NeoPixels is what breaks
the read:

    python3.10 experiments/button_with_led.py            # LED controller active
    python3.10 experiments/button_with_led.py --no-led   # button only (control)

Interpretation:
- pin 26 toggles 0/1 here WITH the LED active -> the read is fine; the runtime
  bug is purely the 1 Hz sampling missing the pulse (fix in gpio_utils).
- pin 26 stuck at 0 only WITH the LED active (but toggles with --no-led) ->
  the NeoPixel/Blinka stack is clobbering the RPi.GPIO read (a real conflict).
- stuck at 0 even with --no-led -> power/wiring under this process, not sampling.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# allow `import lib.plantoid...` when run from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import RPi.GPIO as GPIO

PIN = 26


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--led", dest="led", action="store_true", default=True)
    ap.add_argument("--no-led", dest="led", action="store_false")
    ap.add_argument("--pin", type=int, default=PIN)
    args = ap.parse_args()

    led = None
    if args.led:
        import lib.plantoid.gpio_utils as g
        print("starting NeoPixel LED controller on GPIO 10 (like the runtime)...")
        led = g.GPIOLEDController(10)
        led.set_state("listening")   # drive the LEDs to load the rail
        time.sleep(0.5)
    else:
        print("LED controller NOT started (control run)")

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(args.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    last = GPIO.input(args.pin)
    print(f"reading BCM {args.pin}; idle = {last}. Press the button (Ctrl+C to stop)...")
    presses = 0
    try:
        while True:
            cur = GPIO.input(args.pin)
            if cur != last:
                if cur == 1:
                    presses += 1
                print(f"  pin {args.pin}: {last} -> {cur}   (presses: {presses})")
                last = cur
            time.sleep(0.02)
    except KeyboardInterrupt:
        print(f"\nstopped. total HIGH transitions seen: {presses}")
    finally:
        if led:
            led.cleanup()
        GPIO.cleanup()


if __name__ == "__main__":
    main()
