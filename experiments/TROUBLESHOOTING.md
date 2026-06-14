# Plantoid ↔ Glitchbox troubleshooting

Glitchbox box: `plantoidz-brainz` = `100.79.41.86` (Tailscale).

## Services on Glitchbox

| port | what | used by |
| ---- | ---- | ------- |
| 8002 | video / installation job server | `plantoid_wrapper.py` (`/api/installations/...`, `/api/jobs/...`) |
| 8200 | streaming Smart-ASR (VAD + Smart-Turn + ASR), WebSocket `/v1/listen` | `listen_smartASR()` in `lib/plantoid/speech.py` |
| 8005 | file-based Whisper HTTP, `POST /v1/audio/transcriptions` | `recognize_speech()` fallback |

## First question: is it the Pi's link, or a Glitchbox server?

Check all ports from the Pi:

```bash
for p in 8002 8005 8200; do nc -zv -w3 100.79.41.86 $p; done
```

- **All ports time out** → it's the Pi↔Glitchbox **Tailscale path**, not the servers.
  Confirm: `tailscale ping 100.79.41.86`. If ping works but `nc` still times out,
  the direct path is black-holing TCP (small pings pass, real data dropped).
  **Fix:** `sudo systemctl restart tailscaled` then re-test `nc`.
- **One port "Connection refused"** (others open) → host reachable, that one
  **server process is down** on Glitchbox. Restart it there (see below).

## Symptom → cause map (from the 2026-06-14 session)

- **Video job looks "stuck" at `[queued] stage=None frame 0/0`** — usually just a
  queue/startup delay (worker busy, model loading). The client only logs on
  progress *change*. Verify with:
  `curl -s http://100.79.41.86:8002/api/jobs/<JOB_ID> | python3 -m json.tool`
  Compare `queued_at` vs `started_at`; if `running`, watch `progress.frame`.
- **"Not hearing you" / empty `Heard:`** — check in this order:
  1. Mic OK? `uv run python experiments/mic_check.py` → play `mic_left.wav`.
     If clear, the mic and left-channel extraction are fine.
  2. Can the Pi reach 8200? `nc -zv -w3 100.79.41.86 8200`. If timeout →
     Tailscale path (restart `tailscaled`). The 2026-06-14 outage was this.
  3. 8200 reachable but still empty `Heard:`? Stream a known-good wav with
     `experiments/asr_stream_test.py mic_left.wav` to isolate server vs.
     dropped mic samples in the live loop.

## Restarting the 8005 Whisper server (on Glitchbox)

8005 is not in this repo — it's a process on Glitchbox. SSH in and relaunch:

```bash
ssh plantoidz@100.79.41.86
# find what was serving it / the launch script, then restart it.
# (server is an OpenAI-compatible Whisper endpoint at /v1/audio/transcriptions)
```

Note: with 8200 (streaming ASR) up, the plantoid hears fine even when 8005 is
down — 8005 is only the file-based fallback path.
