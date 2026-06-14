"""Live-mic tester for the 8200 streaming Smart-ASR server.

Run on your LAPTOP. Captures your microphone, streams it to the same
ws://.../v1/listen endpoint the plantoid uses, and prints every event the
server sends back -- so you can speak and immediately see whether the
server transcribes (non-empty `Heard:`) or returns empty text.

Sends raw PCM16 mono 16kHz, exactly what the server expects. If your mic
can't open at 16kHz, it captures at the device's native rate and resamples.

Usage:
    pip install pyaudio websockets        # if not already present
    python experiments/asr_mic_live.py                 # talk, Ctrl+C to stop
    python experiments/asr_mic_live.py --seconds 8     # auto-stop after 8s
    python experiments/asr_mic_live.py --uri ws://100.79.41.86:8200/v1/listen

Reading the output:
    Heard: 'hello plantoid'   -> server works end to end.
    Heard: ''                 -> server got speech but ASR returned nothing
                                 (the backend ASR/Whisper on Glitchbox is broken).
    only speech_start, no transcription -> Smart-Turn never ended the turn
                                 (pause longer / speak a full phrase).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

import pyaudio
import websockets

DEFAULT_URI = "ws://100.79.41.86:8200/v1/listen"
TARGET_RATE = 16000
CHUNK = 1024  # frames per read at the capture rate

try:
    import audioop  # stdlib, removed in Python 3.13
    _HAVE_AUDIOOP = True
except Exception:
    _HAVE_AUDIOOP = False


def _open_mic(pa: "pyaudio.PyAudio"):
    """Return (stream, capture_rate). Prefer 16kHz; fall back to the device
    native rate and resample."""
    info = pa.get_default_input_device_info()
    name = info["name"]
    # 1. try native 16kHz mono — no resampling needed.
    try:
        st = pa.open(format=pyaudio.paInt16, channels=1, rate=TARGET_RATE,
                     input=True, frames_per_buffer=CHUNK)
        print(f"mic: {name} @ {TARGET_RATE}Hz (no resample)")
        return st, TARGET_RATE
    except Exception:
        pass
    # 2. fall back to native rate + resample.
    native = int(info["defaultSampleRate"])
    st = pa.open(format=pyaudio.paInt16, channels=1, rate=native,
                 input=True, frames_per_buffer=CHUNK)
    if native != TARGET_RATE and not _HAVE_AUDIOOP and native % TARGET_RATE != 0:
        sys.exit(f"mic is {native}Hz, can't resample to {TARGET_RATE} "
                 f"(no audioop on this Python and rate isn't an integer multiple)")
    print(f"mic: {name} @ {native}Hz -> resample to {TARGET_RATE}Hz")
    return st, native


def _resample(data: bytes, native: int, state):
    if native == TARGET_RATE:
        return data, state
    if _HAVE_AUDIOOP:
        return audioop.ratecv(data, 2, 1, native, TARGET_RATE, state)
    # crude decimation for integer-multiple rates (e.g. 48000 -> 16000)
    import array
    factor = native // TARGET_RATE
    a = array.array("h", data)
    return a[::factor].tobytes(), state


async def main(args) -> None:
    pa = pyaudio.PyAudio()
    stream, native = _open_mic(pa)
    loop = asyncio.get_event_loop()

    try:
        async with websockets.connect(args.uri, open_timeout=5) as ws:
            print(f"connected to {args.uri}")

            async def reader():
                try:
                    while True:
                        msg = await ws.recv()
                        try:
                            ev = json.loads(msg)
                        except Exception:
                            print("  <-", msg)
                            continue
                        kind = ev.get("event")
                        if kind == "speech_start":
                            print("  [speech detected]")
                        elif kind == "incomplete":
                            print(f"  [still talking prob={ev.get('probability'):.2f}]")
                        elif kind == "transcription":
                            print(f"\n>>> Heard: {ev.get('text','')!r}"
                                  f"   (prob={ev.get('probability')}, "
                                  f"dur={ev.get('duration')})\n")
                        else:
                            print("  <-", msg)
                except websockets.exceptions.ConnectionClosed:
                    print("(server closed connection)")

            rtask = asyncio.create_task(reader())

            print("Speak now" + (f" for {args.seconds}s..." if args.seconds
                                  else " (Ctrl+C to stop)..."))
            state = None
            deadline = (loop.time() + args.seconds) if args.seconds else None
            try:
                while True:
                    if deadline and loop.time() > deadline:
                        break
                    data = await loop.run_in_executor(
                        None, stream.read, CHUNK, False)
                    out, state = _resample(data, native, state)
                    await ws.send(out)
            except (KeyboardInterrupt, asyncio.CancelledError):
                pass

            # Send trailing silence so Smart-Turn detects end-of-turn and the
            # server emits its transcription (it needs silent frames to close
            # the turn -- just stopping the stream isn't enough).
            print("...sending 2.5s silence to close the turn")
            silence = b"\x00" * (CHUNK * 2)  # CHUNK frames of int16 mono
            for _ in range(int(2.5 * TARGET_RATE / CHUNK)):
                await ws.send(silence)
                await asyncio.sleep(CHUNK / TARGET_RATE)

            print("...waiting up to 8s for final transcription")
            await asyncio.sleep(8)
            rtask.cancel()
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Live mic -> 8200 Smart-ASR tester")
    ap.add_argument("--uri", default=DEFAULT_URI)
    ap.add_argument("--seconds", type=float, default=0,
                    help="auto-stop after N seconds (0 = until Ctrl+C)")
    args = ap.parse_args()
    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        pass
