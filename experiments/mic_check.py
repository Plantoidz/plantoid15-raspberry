"""Mic diagnostic for the Smart ASR path.

Run ON the Raspberry Pi. Captures audio the same way listen_smartASR()
does (stereo, 16 kHz, paInt16, 512-frame buffers) and reports the RMS
level of the LEFT vs RIGHT channel, plus saves three wavs so you can
listen back:

    mic_left.wav   - what the code actually sends to the ASR server
    mic_right.wav  - the other channel
    mic_stereo.wav - the raw stereo capture

Usage (on the Pi):
    uv run python experiments/mic_check.py            # 5s capture
    uv run python experiments/mic_check.py --seconds 8

Read the RMS numbers: a channel carrying speech reads in the hundreds to
low thousands; a silent/dead channel reads near 0 (single digits). If the
LEFT RMS is ~0 but RIGHT has signal, the left-channel extraction in
listen_smartASR() is grabbing the wrong lane on this unit.
"""
from __future__ import annotations

import argparse
import math
import struct
import wave

import pyaudio

RATE = 16000
CHUNK = 512


def _rms(samples) -> float:
    if not samples:
        return 0.0
    return math.sqrt(sum(s * s for s in samples) / len(samples))


def main() -> None:
    ap = argparse.ArgumentParser(description="Mic diagnostic for Smart ASR")
    ap.add_argument("--seconds", type=float, default=5.0)
    ap.add_argument("--device", type=int, default=None,
                    help="input device index (default: system default)")
    args = ap.parse_args()

    pa = pyaudio.PyAudio()

    print("=== input devices ===")
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info.get("maxInputChannels", 0) > 0:
            mark = " <- default" if i == pa.get_default_input_device_info()["index"] else ""
            print(f"  [{i}] {info['name']}  "
                  f"in_ch={info['maxInputChannels']}  "
                  f"rate={int(info['defaultSampleRate'])}{mark}")

    mic = pa.open(format=pyaudio.paInt16, channels=2, rate=RATE,
                  input=True, frames_per_buffer=CHUNK,
                  input_device_index=args.device)

    print(f"\nCapturing {args.seconds:.0f}s — TALK NOW...")
    left_all, right_all, stereo_all = [], [], []
    n_chunks = int(args.seconds * RATE / CHUNK)
    for _ in range(n_chunks):
        data = mic.read(CHUNK, exception_on_overflow=False)
        samples = struct.unpack("<" + "hh" * CHUNK, data)
        left_all.extend(samples[0::2])
        right_all.extend(samples[1::2])
        stereo_all.extend(samples)

    mic.stop_stream()
    mic.close()
    pa.terminate()

    l_rms, r_rms = _rms(left_all), _rms(right_all)
    l_peak, r_peak = max(abs(s) for s in left_all), max(abs(s) for s in right_all)
    print("\n=== results ===")
    print(f"LEFT  (sent to ASR): RMS={l_rms:8.1f}  peak={l_peak}")
    print(f"RIGHT             : RMS={r_rms:8.1f}  peak={r_peak}")
    if l_rms < 10 and r_rms >= 50:
        print("\n>>> LEFT channel is silent but RIGHT has signal.")
        print(">>> The left-channel extraction in listen_smartASR() is on the wrong lane.")
        print(">>> Fix: send samples[1::2] (right) instead of samples[0::2].")
    elif l_rms < 10 and r_rms < 10:
        print("\n>>> Both channels near-silent. Mic not capturing — check device "
              "index above, cabling, and alsamixer capture levels.")
    else:
        print("\n>>> LEFT has signal. Mic/channel OK — listen to mic_left.wav to "
              "judge intelligibility (clipping, noise, too quiet).")

    for name, mono in (("mic_left.wav", left_all), ("mic_right.wav", right_all)):
        with wave.open(name, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes(struct.pack("<" + "h" * len(mono), *mono))
    with wave.open("mic_stereo.wav", "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(struct.pack("<" + "h" * len(stereo_all), *stereo_all))
    print("\nWrote mic_left.wav, mic_right.wav, mic_stereo.wav — play them with "
          "`aplay mic_left.wav`")


if __name__ == "__main__":
    main()
