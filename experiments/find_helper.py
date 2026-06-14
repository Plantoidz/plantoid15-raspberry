"""Find which extra GPIO pin makes pin 26 readable.

Setting up only pin 26 can't read the button, but setting up a batch of pins
works -- suggesting the touch sensor draws power/reference from a neighboring
pin that the batch setup energizes (weak pull-up). This finds that pin.

Run ON the Pi from the repo root and HOLD THE BUTTON DOWN the whole time:
    python3.10 experiments/find_helper.py

It first checks pin 26 alone (should read stuck 0 while you hold), then pairs
26 with each candidate pin and reports which pairing lets 26 read HIGH.

Interpretation:
- exactly one (or a few) helper pin makes 26 go HIGH -> the sensor is wired to
  take power/reference from that pin. REAL fix: rewire the sensor VCC to a
  proper 3.3V pin. Quick fix: drive that pin HIGH (output) at runtime.
- only the full batch works, no single helper -> it's an RPi.GPIO setup quirk;
  software fix = set up a batch of pins at init (replicate the scan).
"""
from __future__ import annotations

import time

import RPi.GPIO as GPIO

TOUCH = 26
CANDIDATES = [4, 5, 6, 12, 13, 16, 17, 19, 20, 21, 22, 23, 24, 25, 27]
HOLD_SECS = 1.5


def count_edges(pin: int, secs: float) -> int:
    """Count rising edges (taps) over `secs`. The sensor pulses on touch, so
    we must catch transitions, not a held level."""
    end = time.time() + secs
    last = GPIO.input(pin)
    edges = 0
    while time.time() < end:
        cur = GPIO.input(pin)
        if cur == 1 and last == 0:
            edges += 1
        last = cur
        time.sleep(0.005)
    return edges


def setup(pins) -> None:
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    for p in pins:
        GPIO.setup(p, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    time.sleep(0.15)


def main() -> None:
    print(">>> TAP THE BUTTON REPEATEDLY and keep tapping until the end <<<")
    time.sleep(2.0)
    try:
        setup([TOUCH])
        base = count_edges(TOUCH, HOLD_SECS)
        print(f"baseline (26 alone): {base} taps detected "
              f"{'(already works!)' if base else '(dead)'}")

        helpers = []
        for h in CANDIDATES:
            setup([TOUCH, h])
            n = count_edges(TOUCH, HOLD_SECS)
            print(f"  26 + {h:>2}: {n} taps  {'<-- helper ✓' if n else ''}")
            if n:
                helpers.append(h)

        setup([TOUCH] + CANDIDATES)
        full = count_edges(TOUCH, HOLD_SECS)
        print(f"full batch: {full} taps")

        print("\n=== result ===")
        if base:
            print("26 alone already detects taps -- earlier single-pin failures "
                  "may have been timing; re-run button_test.py --pin 26.")
        elif helpers:
            print(f"helper pin(s): {helpers}  -> sensor draws power/reference "
                  f"from there. Rewire sensor VCC to 3.3V, or drive that pin HIGH.")
        elif full:
            print("no single helper, but full batch works -> RPi.GPIO setup "
                  "quirk; fix = set up a batch of pins at init (replicate scan).")
        else:
            print("nothing detected -- were you tapping? re-run and tap "
                  "continuously the whole time.")
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()
