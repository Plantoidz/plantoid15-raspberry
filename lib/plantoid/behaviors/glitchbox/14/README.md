# Plantoid 14 — API

One call in, one video out. You upload an init image, an audio file, a
list of prompts, and a LoRA spec; the server returns a video whose
length matches the audio, with the audio overlaid on it.

There are no sound-reactive controllers. The audio drives video length
and is muxed into the output, nothing more.

---

## `POST /api/installations/plantoid14`

Content type: `multipart/form-data`

### Files

| field         | required | notes |
| ------------- | -------- | ----- |
| `init_image`  | yes      | The image the diffusion is anchored to. Any common image format. |
| `audio_file`  | yes      | Drives the output video length and is muxed into the final mp4. |

### Form fields

| field          | type                                | default       | meaning |
| -------------- | ----------------------------------- | ------------- | ------- |
| `prompts`      | repeated string, ≥2 entries         | —             | The journey list. Send as `-F prompts=A -F prompts=B …`. |
| `lora`         | string                              | —             | One of: a preset index (`"21"`), a single shorthand (`"twisted-bodies-xl"`), or a comma-list (`"twisted-bodies-xl,water-xl"`). Empty / `"none"` → no LoRA. The set of valid presets and shorthands is in `plantoid/lora_index.yaml`. |
| `lora_weights` | comma-separated floats, optional    | equal split   | Static per-LoRA weights for pair/tuple specs (e.g. `"0.7,0.3"`). Length must match the LoRA count. Reject if `lora` resolves to fewer than 2 LoRAs. |
| `fps`          | int > 0                             | `20`          | Output frame rate. |
| `controlnet`   | bool                                | `true`        | Depth ControlNet on/off. |
| `cn_scale`     | float in `(0, 2]`                   | `0.55`        | ControlNet conditioning strength. Only meaningful when `controlnet=true`; ignored otherwise. |
| `audio_mode`   | enum                                | `passthrough` | Only `"passthrough"` is accepted on this endpoint. Anything else returns 400. |
| `audio_reaction_output_gain` | float ≥ 0             | `1.0`         | Post-smoother expander gain on the α(t) audio-reaction curve. Drives all audio-reactive consumers (zoom / prompt blend / LoRA blend). Plantoid 14 is passthrough today (controllers dormant), so this is harmless until a sound-reactive p14 mode is added. |
| `n_rungs`      | int ≥ 1                              | `2`           | StreamBatch queue depth (denoising rungs). 2 = one rung + one buffer step; raise for more denoising fidelity at higher latency. |
| `crf`          | int in `[0, 51]`                     | `32`          | libx264 Constant Rate Factor for the output mp4. Plantoid 14 default is `32` (small files: ~5× smaller than the pipeline-internal `crf 17` near-lossless default, optimised for plantoid download bandwidth). Lower = larger / higher quality. |
| `preset`       | `"fast"` \| `"medium"` \| `"slow"`   | `slow`        | libx264 preset. `slow` gets the best size at a given crf, `fast` encodes ~3-4× quicker. |
| `mode`         | `"img2img"` \| `"txt2img"`          | `img2img`     | `img2img` keeps the init_image as the visual anchor. `txt2img` drops the anchor and generates from prompts only. |
| `h_smoothing`  | bool                                | `true`        | Cross-frame smoothing toggle. |
| `seed`         | int, optional                       | random        | Omit for a fresh random seed. The chosen value is recorded in the run output so the result is reproducible after the fact. |

### Validation errors (`400`)

- fewer than 2 prompts
- audio too short for the requested prompt count (need at least
  `3 N − 2` frames at the requested fps)
- `lora_weights` cardinality doesn't match the resolved LoRA count
- `lora_weights` set when there are fewer than 2 LoRAs
- unknown LoRA preset / shorthand
- `cn_scale` outside `(0, 2]`
- `audio_mode` ≠ `"passthrough"`
- `audio_reaction_output_gain` < 0
- `n_rungs` < 1
- `crf` outside `[0, 51]` or `preset` not in `{fast, medium, slow}`
- `mode` ≠ `"img2img"` / `"txt2img"`
- `fps` ≤ 0

### Response — `200 OK`

```json
{
  "job_id": "f6323484abc…",
  "status": "queued",
  "summary": {
    "frames": 200,
    "fps": 20,
    "duration_s": 10.0,
    "n_prompts": 6,
    "transition_frames": 26,
    "hold_frames": 13,
    "loras": [
      "/.../twisted_bodies_XL-step00001000.safetensors=0.5",
      "/.../water_XL-step00000800.safetensors=0.5"
    ],
    "controlnet": "depth-sdxl"
  }
}
```

The summary lets you confirm the schedule the server derived from your
audio length and prompt count without polling the run.

---

## `GET /api/jobs/{job_id}`

Poll for progress. Status flows: `queued` → `running` → `complete` |
`failed` | `cancelled`.

```json
{
  "job_id": "f6323484abc…",
  "status": "running",
  "progress": { "stage": null, "frame": 87, "total": 200 },
  "run_id": "20260427-223506_…",
  "return_code": null,
  "error": null,
  "stdout_tail": ["...", "..."]
}
```

When `status` is terminal:
- `complete` → `run_id` is set; outputs are at the run dir.
- `failed` / `cancelled` → `error` is a short string, `stdout_tail` is
  the last ~80 lines of runner output (for debugging).

Viewer URL once complete:
`http://<server>/m/_installation_plantoid14/r/<run_id>`

---

## `GET /api/runs/{run_id}/file/{path}`

Downloads any file from the run's output directory by relative path.
This is how the plantoid actually pulls the video bytes once a job
finishes.

Useful paths inside a run directory:

| path                       | what it is |
| -------------------------- | ---------- |
| `video.mp4`                | the output video with audio muxed in (this is what the plantoid plays) |
| `manifest.yaml`            | the resolved manifest, including the seed that was actually used |
| `installation_call.json`   | the original multipart inputs (intent form) |
| `metrics.json`             | per-frame metrics |
| `frames/frame_NNNN.png`    | individual frames |

Path traversal outside the run directory returns `400`. Missing files
return `404`.

```bash
# Once GET /api/jobs/{id} reports status=complete and run_id is set:
curl -o output.mp4 \
  http://127.0.0.1:8000/api/runs/$RUN_ID/file/video.mp4
```

The endpoint streams the file as `FileResponse` — no auth, no
expiration. It works as long as the run directory exists on the server.

---

## `GET /api/installations/lora_index?xl_only=true`

Returns the static LoRA index (presets + shorthands). The plantoid
runtime ships its own copy in `plantoid/lora_index.yaml` and validates
locally — this endpoint is for first-time discovery / refresh only.

```json
{
  "shorthands": ["angels-xl", "dwellers-input", "...", "water-xl"],
  "presets": {
    "21": ["twisted-bodies-xl", "water-xl"],
    "22": ["san-xl", "angels-xl"],
    "...": ["..."]
  }
}
```

---

## How the schedule is derived

You don't pick the frame count — it's derived from your audio:

```
target_frames = ceil(audio_duration_s * fps)
H = ceil(target_frames / (3N - 2))      # T:H ratio is 2:1
T = 2 * H
frames = (N - 1) * (T + H) + H          # ≥ target_frames
```

Where `N = len(prompts)`. The video is rounded up so the audio plays in
full; ffmpeg's `-shortest` trims the at-most-`T+H` surplus video tail.

---

## Curl example

```bash
curl -X POST http://127.0.0.1:8000/api/installations/plantoid14 \
  -F "init_image=@init.jpg" \
  -F "audio_file=@audio.wav" \
  -F "lora=21" \
  -F "lora_weights=0.5,0.5" \
  -F "fps=20" \
  -F "controlnet=true" \
  -F "cn_scale=0.55" \
  -F "audio_mode=passthrough" \
   -F "audio_reaction_output_gain=1.0" \
  -F "n_rungs=2" \
  -F "crf=32" \
  -F "preset=slow" \
  -F "mode=img2img" \
  -F "h_smoothing=true" \
  -F "prompts=twisted bodies Pale beige sculptural forms..." \
  -F "prompts=twisted bodies Pale cream sculptural figures..." \
  -F "prompts=twisted bodies Abstract organic sculpture..." \
  -F "prompts=twisted bodies Pale beige jellyfish cluster..." \
  -F "prompts=twisted bodies Pale beige sculptural figures..." \
  -F "prompts=twisted bodies Pale sculpted figures..."
```
