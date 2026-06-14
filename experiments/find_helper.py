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


def reads_high(pin: int, secs: float) -> bool:
    end = time.time() + secs
    while time.time() < end:
        if GPIO.input(pin) == 1:
            return True
        time.sleep(0.01)
    return False


def setup(pins) -> None:
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    for p in pins:
        GPIO.setup(p, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    time.sleep(0.15)


def main() -> None:
    print(">>> HOLD THE BUTTON DOWN now and keep holding until the end <<<")
    time.sleep(2.0)
    try:
        setup([TOUCH])
        base = reads_high(TOUCH, HOLD_SECS)
        print(f"baseline (26 alone): {'HIGH seen (already works!)' if base else 'stuck 0'}")

        helpers = []
        for h in CANDIDATES:
            setup([TOUCH, h])
            ok = reads_high(TOUCH, HOLD_SECS)
            print(f"  26 + {h:>2}: {'HIGH ✓  <-- helper' if ok else 'stuck 0'}")
            if ok:
                helpers.append(h)

        setup([TOUCH] + CANDIDATES)
        full = reads_high(TOUCH, HOLD_SECS)
        print(f"full batch: {'HIGH ✓' if full else 'stuck 0'}")

        print("\n=== result ===")
        if helpers:
            print(f"helper pin(s): {helpers}  -> sensor draws power/reference "
                  f"from there. Rewire sensor VCC to 3.3V, or drive that pin HIGH.")
        elif full:
            print("no single helper, but full batch works -> RPi.GPIO setup "
                  "quirk; fix = set up a batch of pins at init.")
        else:
            print("nothing made it read HIGH -- were you holding the button? "
                  "re-run and keep it pressed the whole time.")
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()
