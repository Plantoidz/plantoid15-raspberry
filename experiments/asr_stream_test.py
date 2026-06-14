"""Stream a known-good wav to the 8200 Smart-ASR WS server.

Run ON the Pi after capturing a clean mic_left.wav with mic_check.py.
This sends that wav as raw PCM16 mono 16k, in 512-frame (32ms) chunks
paced in real time, to the same ws://.../v1/listen endpoint that
listen_smartASR() uses -- but with perfectly contiguous audio (no
mic-overflow gaps). It prints every event the server returns.

Usage (on the Pi):
    uv run python experiments/asr_stream_test.py mic_left.wav

Interpretation:
- Server prints speech_start + a non-empty "transcription" -> the 8200
  server transcribes good audio fine. The live empty-Heard problem is
  dropped mic samples in listen_smartASR (decouple read from send).
- speech_start but empty/again-empty transcription -> the server's
  Smart-Turn / ASR is the problem, fix on Glitchbox.
- No speech_start at all -> the server isn't getting usable audio
  (format/rate mismatch).
"""
from __future__ import annotations

import asyncio
import json
import sys
import wave

import websockets

URI = "ws://100.79.41.86:8200/v1/listen"
CHUNK = 512  # frames; 32ms at 16kHz


async def main(path: str) -> None:
    with wave.open(path, "rb") as w:
        assert w.getnchannels() == 1, "expected mono wav (mic_left.wav)"
        assert w.getframerate() == 16000, f"expected 16k, got {w.getframerate()}"
        pcm = w.readframes(w.getnframes())

    print(f"streaming {len(pcm)} bytes ({len(pcm)/2/16000:.1f}s) to {URI}")
    async with websockets.connect(URI, open_timeout=3) as ws:
        bytes_per_chunk = CHUNK * 2  # mono int16

        async def reader():
            try:
                while True:
                    msg = await ws.recv()
                    print("  <-", msg)
            except websockets.exceptions.ConnectionClosed:
                print("  <- (server closed)")

        rtask = asyncio.create_task(reader())

        for i in range(0, len(pcm), bytes_per_chunk):
            await ws.send(pcm[i:i + bytes_per_chunk])
            await asyncio.sleep(CHUNK / 16000)  # real-time pacing

        # Append trailing silence so Smart-Turn detects end-of-turn and
        # the server emits its transcription (live mic does this naturally
        # when the speaker pauses). 2.5s of zeros.
        silence = b"\x00" * bytes_per_chunk
        for _ in range(int(2.5 * 16000 / CHUNK)):
            await ws.send(silence)
            await asyncio.sleep(CHUNK / 16000)

        print("  ... sent speech + 2.5s silence, waiting up to 10s for transcription")
        # let the server flush its final transcription
        await asyncio.sleep(10)
        rtask.cancel()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: asr_stream_test.py <wav>")
    asyncio.run(main(sys.argv[1]))
