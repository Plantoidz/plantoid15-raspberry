"""Client for the GuiTion ESP32 display.

Mirrors Plantony's state messages onto a second screen, and streams the
generated NFT video over USB serial. All messages use a 7-byte framed header:

    [0xAA 0x55][TYPE: 1B][LEN: 4B little-endian][PAYLOAD: LEN bytes]

TYPE values:
    'S' = screen switch       payload = ASCII name ("idle" | "working" | "video")
    'P' = progress update     payload = 1 byte percentage (0..100)
    'V' = video JPEG frame    payload = JPEG bytes
"""
from __future__ import annotations

import struct
import subprocess
import threading
import time
from pathlib import Path

import serial


SYNC = b"\xAA\x55"

# All screen changes are now explicit — see show_working/show_idle/show_ready.
# The firmware returns to IDLE on its own:
#   - 60s after SEED READY is shown
#   - 3s after a video stream stops (videoPlaying timeout)
#   - on boot (default screen)
# so no Plantony state message needs to map to a screen.
SCREEN_FROM_STATE = {}


class Guition:
    """Thread-safe client. All writes go through a lock so video streaming
    and state changes from other threads don't interleave their bytes.

    Construction opens the serial port; if it can't be opened the constructor
    raises. Use the module-level `setup()` factory if you want a clean
    "returns None on failure" wrapper.
    """

    def __init__(self, port: str, baud: int = 921600):
        self.port = port
        self.baud = baud
        self.lock = threading.Lock()
        self.ser = None
        self._stop = False
        self._write_err_logged = False
        # The GuiTion ESP32 enumerates on USB a few seconds AFTER the Pi
        # launches Plantoid, and can re-enumerate (ACM0 -> ACM1) on a USB
        # over-current blip. A one-shot open at startup loses the screen for
        # the whole session, so open in the background and keep retrying.
        self._connector = None
        self._ensure_connector()

    # ---- connection management ----
    def _open_once(self) -> bool:
        try:
            # Hold DTR/RTS low BEFORE opening so we never pulse the ESP32 into
            # reset on connect.
            ser = serial.Serial()
            ser.port = self.port
            ser.baudrate = self.baud
            ser.timeout = 1
            ser.dtr = False
            ser.rts = False
            ser.open()
        except Exception:
            return False
        with self.lock:
            self.ser = ser
            self._write_err_logged = False
        print(f"[guition] connected on {self.port}")
        return True

    def _connect_loop(self) -> None:
        delay, announced = 1.0, False
        while not self._stop:
            if self._open_once():
                return
            if not announced:
                print(f"[guition] {self.port} not available yet, "
                      f"retrying in background...")
                announced = True
            time.sleep(delay)
            delay = min(delay * 1.5, 10.0)

    def _ensure_connector(self) -> None:
        """Start the background (re)connect thread if one isn't already
        running. Only spawns a thread; safe to call with the lock held."""
        if self._connector is None or not self._connector.is_alive():
            self._connector = threading.Thread(
                target=self._connect_loop, daemon=True)
            self._connector.start()

    # ---- low level ----
    def _send(self, type_byte: bytes, payload: bytes = b"") -> None:
        msg = SYNC + type_byte + struct.pack("<I", len(payload)) + payload
        with self.lock:
            if self.ser is None:
                return  # not connected yet; background thread is retrying
            try:
                self.ser.write(msg)
            except Exception as e:
                if not self._write_err_logged:  # log once per disconnect
                    print(f"[guition] write failed, reconnecting: {e}")
                    self._write_err_logged = True
                try:
                    self.ser.close()
                except Exception:
                    pass
                self.ser = None
                self._ensure_connector()

    # ---- high level ----
    def set_screen(self, name: str) -> None:
        """name in {'idle', 'working', 'video'}"""
        self._send(b"S", name.encode("ascii"))

    def set_progress(self, percent: float) -> None:
        p = max(0, min(100, int(percent)))
        self._send(b"P", bytes([p]))

    def hide_progress(self) -> None:
        """Spinner only — hide bar/percentage/caption on the WORKING screen."""
        self._send(b"P", bytes([0xFF]))

    def state_changed(self, plantony_state: str) -> None:
        """Translate a Plantony serial message ('asleep', 'thinking', ...)
        to a screen name and switch. Unknown states are ignored."""
        screen = SCREEN_FROM_STATE.get(plantony_state)
        if screen:
            self.set_screen(screen)

    def send_video_frame(self, jpeg_bytes: bytes) -> None:
        self._send(b"V", jpeg_bytes)

    def show_ready(self, url: str) -> None:
        """Switch to the 'reveal ready' screen with a dynamic QR for `url`.
        Firmware auto-returns to IDLE after 60s; no action required from the Pi."""
        self._send(b"R", url.encode("utf-8"))

    # ---- video streaming ----
    def stream_video(self, mp4_path: str | Path, fps: int = 10,
                     width: int = 240, height: int = 320) -> None:
        """Extract MJPEG frames from the given MP4 with ffmpeg and stream them
        to the GuiTion. Blocks for the duration of the clip. Audio is *not*
        sent — it should be played through the Pi's existing audio path
        (pygame mixer) in parallel."""
        mp4 = Path(mp4_path)
        if not mp4.exists():
            print(f"[guition] stream_video: missing {mp4}")
            return

        # Render the whole MJPEG via ffmpeg in one shot (we have plenty of RAM
        # on the Pi). For very long clips, switch to a streamed pipe instead.
        try:
            mjpeg = subprocess.check_output([
                "ffmpeg", "-i", str(mp4),
                "-vf", f"scale={width}:{height}",
                "-c:v", "mjpeg", "-q:v", "6",
                "-f", "mjpeg", "-an",
                "-loglevel", "error",
                "-",
            ])
        except Exception as e:
            print(f"[guition] ffmpeg failed: {e}")
            return

        frames = self._split_jpegs(mjpeg)
        print(f"[guition] streaming {len(frames)} frames at {fps} fps")
        self.set_screen("video")

        period = 1.0 / fps
        next_t = time.monotonic()
        for f in frames:
            self.send_video_frame(f)
            next_t += period
            slack = next_t - time.monotonic()
            if slack > 0:
                time.sleep(slack)
            else:
                next_t = time.monotonic()  # fell behind, resync

    @staticmethod
    def _split_jpegs(data: bytes) -> list[bytes]:
        out: list[bytes] = []
        i, n = 0, len(data)
        while i < n - 1:
            while i < n - 1 and not (data[i] == 0xFF and data[i + 1] == 0xD8):
                i += 1
            if i >= n - 1:
                break
            start = i
            i += 2
            while i < n - 1 and not (data[i] == 0xFF and data[i + 1] == 0xD9):
                i += 1
            if i >= n - 1:
                break
            out.append(data[start:i + 2])
            i += 2
        return out

    def close(self) -> None:
        self._stop = True
        with self.lock:
            if self.ser is not None:
                try:
                    self.ser.close()
                except Exception:
                    pass
                self.ser = None


def setup(port: str | None) -> Guition | None:
    """Open a connection to the GuiTion display.

    Returns a Guition instance, or None only if `port` is empty. The actual
    serial open happens in a background thread that retries until the device
    appears (and reconnects if it later re-enumerates), so this never blocks
    startup or fails just because the ESP32 hasn't booted yet. Callers still
    gate on `if self.guition: ...` so the integration stays optional.
    """
    if not port:
        return None
    g = Guition(port)
    set_current(g)
    return g


# ---- module-level handle so deep callbacks (e.g. the Glitchbox poll loop
# inside lib/plantoid/behaviors/glitchbox/) can report progress without
# plumbing a `plantoid` argument through every layer. Set by setup(). ----
_current: Guition | None = None


def set_current(g: Guition | None) -> None:
    global _current
    _current = g


def get_current() -> Guition | None:
    return _current


def report_progress(percent: float) -> None:
    """Update the WORKING screen progress bar from anywhere in the codebase.
    No-op if no GuiTion is connected."""
    if _current:
        _current.set_progress(percent)


def show_working(hide_bar: bool = False) -> None:
    """Switch to WORKING. Pass hide_bar=True for spinner-only (no bar)."""
    if _current:
        _current.set_screen("working")
        if hide_bar:
            _current.hide_progress()


def show_idle() -> None:
    if _current:
        _current.set_screen("idle")
