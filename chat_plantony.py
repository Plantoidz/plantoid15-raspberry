#!/usr/bin/env python3
"""Simple terminal chat with Plantony, spoken in his cloned voice.

Usage:
    python3 chat_plantony.py [context_name] [--no-voice]

context_name is the suffix of a file in ./prompt_context/, e.g.
    python3 chat_plantony.py p21-lunarpunk_singer
Defaults to plantony_context.txt. Ctrl-C or 'quit' to exit.

Speech uses the Glitchbox qwen3-tts server, same as lib/plantoid/speech.py.
If it can't be reached the chat carries on in text only.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import wave

ENDPOINT = "http://100.94.7.108:8090/v1/chat/completions"
CONTEXT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompt_context")

# Glitchbox TTS, as used by stream_response() in lib/plantoid/speech.py.
TTS_ENDPOINT = "http://100.79.41.86:8000/v1/audio/speech"
TTS_VOICE = "plantony"
TTS_RATE = 24000  # server streams headerless 16-bit mono PCM at this rate


def load_context(name):
    fname = "plantony_context.txt" if not name else f"plantony_context-{name}.txt"
    path = os.path.join(CONTEXT_DIR, fname)
    if not os.path.exists(path):
        available = sorted(f for f in os.listdir(CONTEXT_DIR) if f.endswith(".txt"))
        sys.exit(f"No such context: {path}\n\nAvailable:\n  " + "\n  ".join(available))
    with open(path) as f:
        return f.read()


def find_player():
    """First available CLI audio player: macOS afplay, else ALSA aplay on the Pi."""
    for cmd in ("afplay", "aplay"):
        if shutil.which(cmd):
            return cmd
    return None


def speak(text, player):
    """Render text in Plantony's cloned voice and play it. Never fatal."""
    body = json.dumps(
        {
            "model": "qwen3-tts",
            "input": text,
            "voice": f"clone:{TTS_VOICE}",
            "response_format": "wav",
            "stream": True,
            "streaming_interval": 0.5,
        }
    )
    req = urllib.request.Request(
        TTS_ENDPOINT, data=body.encode(), headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            pcm = resp.read()
    except Exception as e:
        print(f"[voice unavailable: {e}]", file=sys.stderr)
        return

    if not pcm:
        return

    # The stream is raw headerless PCM, so give it a WAV header before playing.
    path = os.path.join(tempfile.gettempdir(), "plantony_say.wav")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(TTS_RATE)
        wf.writeframes(pcm[: len(pcm) // 2 * 2])

    try:
        subprocess.run([player, path], check=False)
    except KeyboardInterrupt:
        pass  # let the user cut a long reply short


def stream_reply(messages):
    """POST to the endpoint and print the reply as it arrives. Returns full text.

    The model streams its reasoning first and closes it with </think>, then emits
    a <|user|> turn marker the server doesn't strip; both are hidden here.
    """
    body = json.dumps({"model": "plantony", "messages": messages, "stream": True})
    req = urllib.request.Request(
        ENDPOINT, data=body.encode(), headers={"Content-Type": "application/json"}
    )
    buf = ""
    reply = []
    thinking = True

    def emit(text):
        reply.append(text)
        print(text, end="", flush=True)

    with urllib.request.urlopen(req, timeout=300) as resp:
        for raw in resp:
            line = raw.decode().strip()
            if not line.startswith("data: "):
                continue
            payload = line[6:]
            if payload == "[DONE]":
                break
            buf += json.loads(payload)["choices"][0]["delta"].get("content", "")

            if thinking:
                if "</think>" not in buf:
                    continue
                buf = buf.split("</think>", 1)[1]
                thinking = False
            if "<|user|>" in buf:
                buf = buf.split("<|user|>", 1)[0]
                break
            # Hold back a tail long enough to catch a marker split across chunks.
            emit(buf[:-8])
            buf = buf[-8:]

    # No </think> in the whole stream: it wasn't reasoning, buf is the real reply.
    if thinking:
        buf = buf.split("<|user|>", 1)[0]

    emit(buf)
    print()
    return "".join(reply).strip()


def main():
    args = [a for a in sys.argv[1:] if a != "--no-voice"]
    voice = "--no-voice" not in sys.argv

    context = load_context(args[0] if args else None)
    messages = [{"role": "system", "content": context}]

    player = find_player() if voice else None
    if voice and not player:
        print("[no afplay/aplay found — text only]", file=sys.stderr)

    while True:
        try:
            user = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user:
            continue
        if user in ("quit", "exit"):
            break
        messages.append({"role": "user", "content": user})
        print("\nplantony> ", end="", flush=True)
        try:
            reply = stream_reply(messages)
        except KeyboardInterrupt:
            print("\n[interrupted]")
            messages.pop()
            continue
        messages.append({"role": "assistant", "content": reply})

        if player and reply:
            speak(reply, player)


if __name__ == "__main__":
    main()
