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

# Mapping from Plantony's existing serial messages to GuiTion screens
SCREEN_FROM_STATE = {
    "asleep":    "idle",
    "awake":     "idle",
    "thinking":  "working",
    "listening": "working",
    "speaking":  "working",
}


class Guition:
    """Thread-safe client. All writes go through a lock so video streaming
    and state changes from other threads don't interleave their bytes."""

    def __init__(self, port: str | None, baud: int = 921600):
        self.port = port
        self.ser: serial.Serial | None = None
        self.lock = threading.Lock()
        if port:
            try:
                self.ser = serial.Serial(port, baud, timeout=1)
                print(f"[guition] connected on {port}")
            except Exception as e:
                print(f"[guition] failed to open {port}: {e}")
                self.ser = None

    # ---- low level ----
    def _send(self, type_byte: bytes, payload: bytes = b"") -> None:
        if not self.ser:
            return
        msg = SYNC + type_byte + struct.pack("<I", len(payload)) + payload
        with self.lock:
            try:
                self.ser.write(msg)
            except Exception as e:
                print(f"[guition] write failed: {e}")

    # ---- high level ----
    def set_screen(self, name: str) -> None:
        """name in {'idle', 'working', 'video'}"""
        self._send(b"S", name.encode("ascii"))

    def set_progress(self, percent: float) -> None:
        p = max(0, min(100, int(percent)))
        self._send(b"P", bytes([p]))

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
        if not self.ser:
            print("[guition] stream_video: not connected")
            return
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
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
            self.ser = None


def setup(port: str | None) -> Guition:
    """Convenience factory. Returns a Guition (possibly disconnected — all
    methods become no-ops if the port couldn't be opened)."""
    return Guition(port)
