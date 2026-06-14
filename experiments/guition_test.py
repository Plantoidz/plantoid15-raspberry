"""Direct GuiTion screen tester. Run ON the Pi.

Speaks the GuiTion framed protocol straight over serial so you can confirm
the display reacts, independent of the plantoid runtime.

Frame:  [0xAA 0x55][TYPE 1B][LEN 4B LE][PAYLOAD]
  'S' screen switch   payload = b"idle" | b"working" | b"video"
  'P' progress        payload = 1 byte 0..100  (0xFF = hide bar)

Usage (on the Pi):
    # cycle through screens so you can watch it move:
    python3.10 experiments/guition_test.py --port /dev/ttyACM1

    # or just force one screen:
    python3.10 experiments/guition_test.py --port /dev/ttyACM1 --screen working
    python3.10 experiments/guition_test.py --port /dev/ttyACM1 --screen idle

If nothing changes on the screen, watch the terminal: a write error means
the device dropped (the over-current / re-enumeration issue) -- re-check
`ls /dev/ttyACM*` because it may have jumped to a different node.
"""
from __future__ import annotations

import argparse
import struct
import time

import serial

SYNC = b"\xAA\x55"


def send(ser, type_byte: bytes, payload: bytes = b"") -> None:
    msg = SYNC + type_byte + struct.pack("<I", len(payload)) + payload
    ser.write(msg)
    ser.flush()
    print(f"  sent {type_byte!r} payload={payload!r} ({len(msg)} bytes)")


def open_port(port: str, baud: int) -> serial.Serial:
    # Set DTR/RTS low BEFORE opening so we don't pulse the ESP32 into reset.
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = baud
    ser.timeout = 1
    ser.dtr = False
    ser.rts = False
    ser.open()
    print(f"opened {port} @ {baud} (dtr/rts held low)")
    return ser


def main() -> None:
    ap = argparse.ArgumentParser(description="Direct GuiTion screen tester")
    ap.add_argument("--port", default="/dev/ttyACM1")
    ap.add_argument("--baud", type=int, default=921600)
    ap.add_argument("--screen", choices=["idle", "working", "video"],
                    default=None, help="force one screen instead of cycling")
    args = ap.parse_args()

    ser = open_port(args.port, args.baud)
    time.sleep(0.3)  # let the device settle after open

    try:
        if args.screen:
            print(f"setting screen -> {args.screen}")
            send(ser, b"S", args.screen.encode("ascii"))
            time.sleep(0.5)
            return

        print("cycling screens (watch the display)...")
        print("-> WORKING")
        send(ser, b"S", b"working")
        for pct in (0, 25, 50, 75, 100):
            print(f"-> progress {pct}%")
            send(ser, b"P", bytes([pct]))
            time.sleep(1.0)
        time.sleep(1.0)
        print("-> IDLE")
        send(ser, b"S", b"idle")
        time.sleep(1.0)
        print("done.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
