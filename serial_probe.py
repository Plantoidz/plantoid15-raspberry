"""
Probe /dev/ttyUSB0 at several baud rates.
For each: open port, send <RESET>, read for 5 seconds, print bytes (raw + decoded).
"""
import serial
import time
import sys

PORT = "/dev/ttyUSB0"
BAUDS = [9600, 115200, 57600, 38400, 19200, 4800]
LISTEN_SECS = 5

def probe(baud):
    print(f"\n=== {baud} baud ===")
    try:
        ser = serial.Serial(PORT, baud, timeout=0.2)
    except Exception as e:
        print(f"  open failed: {e}")
        return

    time.sleep(2)  # give board time to auto-reset on DTR toggle
    ser.reset_input_buffer()

    ser.write(b"<RESET>\n")
    ser.flush()
    print(f"  sent: <RESET>")

    raw = b""
    deadline = time.time() + LISTEN_SECS
    while time.time() < deadline:
        chunk = ser.read(256)
        if chunk:
            raw += chunk
        else:
            time.sleep(0.05)

    ser.close()

    if not raw:
        print(f"  received: (nothing in {LISTEN_SECS}s)")
        return

    print(f"  received {len(raw)} bytes")
    print(f"  raw hex : {raw.hex()}")
    try:
        decoded = raw.decode("utf-8", errors="replace")
    except Exception:
        decoded = repr(raw)
    print(f"  as text : {decoded!r}")

if __name__ == "__main__":
    for b in BAUDS:
        probe(b)
