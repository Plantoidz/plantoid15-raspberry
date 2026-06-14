"""GPIO button tester for the Plantoid touch input. Run ON the Pi.

Bypasses the plantoid runtime and reads the GPIO directly so you can tell
whether the button hardware/wiring works and which pin it's on.

Pins are BCM numbering (same as configuration.toml USE_GPIO.touch).
The runtime configures the touch pin as INPUT with pull-up, so it idles
HIGH (1) and a correctly wired button pulls it LOW (0) when pressed.

Usage (on the Pi, with the plantoid STOPPED):

    # 1. Watch the configured pin (26) live -- press the button, watch it flip:
    python3.10 experiments/button_test.py --pin 26

    # 2. Don't know the pin / nothing flips? Scan many pins at once and press
    #    the button -- it prints whichever pin changes:
    python3.10 experiments/button_test.py --scan

    # try pull-down instead if the button wires the pin to 3.3V (not GND):
    python3.10 experiments/button_test.py --pin 26 --pull down

Ctrl+C to stop.
"""
from __future__ import annotations

import argparse
import time

import RPi.GPIO as GPIO

# Safe-ish BCM pins to scan. 10 is the NeoPixel LED data line -- excluded.
SCAN_PINS = [4, 5, 6, 12, 13, 16, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27]


def _pud(name: str):
    return {"up": GPIO.PUD_UP, "down": GPIO.PUD_DOWN,
            "none": GPIO.PUD_OFF}[name]


def monitor(pin: int, pull: str) -> None:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.IN, pull_up_down=_pud(pull))
    last = GPIO.input(pin)
    idle = "HIGH" if last else "LOW"
    print(f"monitoring BCM {pin} (pull={pull}); idle level = {last} ({idle})")
    print("press/release the button...  (Ctrl+C to stop)")
    presses = 0
    while True:
        cur = GPIO.input(pin)
        if cur != last:
            edge = "released -> HIGH" if cur else "pressed -> LOW"
            if not cur:
                presses += 1
            print(f"  pin {pin}: {last} -> {cur}   [{edge}]   "
                  f"(presses so far: {presses})")
            last = cur
        time.sleep(0.01)


def scan(pull: str) -> None:
    GPIO.setmode(GPIO.BCM)
    for p in SCAN_PINS:
        try:
            GPIO.setup(p, GPIO.IN, pull_up_down=_pud(pull))
        except Exception as e:
            print(f"  (skip pin {p}: {e})")
    last = {p: GPIO.input(p) for p in SCAN_PINS}
    print(f"scanning pins {SCAN_PINS} (pull={pull})")
    print("idle levels:", {p: last[p] for p in SCAN_PINS})
    print("now PRESS the button -- the pin that changes is your button pin.")
    print("(Ctrl+C to stop)")
    while True:
        for p in SCAN_PINS:
            cur = GPIO.input(p)
            if cur != last[p]:
                print(f"  >>> BCM {p} changed: {last[p]} -> {cur}   "
                      f"<-- button is likely on pin {p}")
                last[p] = cur
        time.sleep(0.01)


def main() -> None:
    ap = argparse.ArgumentParser(description="Plantoid GPIO button tester")
    ap.add_argument("--pin", type=int, default=26, help="BCM pin (default 26)")
    ap.add_argument("--pull", choices=["up", "down", "none"], default="up")
    ap.add_argument("--scan", action="store_true",
                    help="scan many pins to find which one the button drives")
    args = ap.parse_args()
    try:
        if args.scan:
            scan(args.pull)
        else:
            monitor(args.pin, args.pull)
    except KeyboardInterrupt:
        print("\nstopped.")
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()
