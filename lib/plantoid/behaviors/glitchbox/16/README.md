# Plantoid 16 — API

One call in, one video out. The server returns a video whose length
matches the audio.

There are **two upload shapes**, mutually exclusive:

- **keyframes mode** — you upload N keyframe images + N
  `init_image_prompts`. The server runs a pregen prompt-travel
  through the keyframes, then the final pass on top of that.
- **init_video mode** — you upload a single pre-built `init_video.mp4`
  (e.g. an upstream rendered clip). The server skips the pregen
  entirely and feeds your video straight into the final pass.

The final-pass behaviour depends on whether the LoRA spec resolves to
one or two LoRAs:

- **single LoRA** — the audio is overlaid on the video (no
  reactivity). The video is a journey through `final_prompts_a`.
- **pair of LoRAs** — the audio drives both the prompt blend
  (`final_prompts_a` ↔ `final_prompts_b`) and the LoRA blend on the
  selected mel band.

---

## `POST /api/installations/plantoid16`

Content type: `multipart/form-data`

### Files

| field          | required                             | notes |
| -------------- | ------------------------------------ | ----- |
| `init_images`  | exactly one of `{init_images, init_video}` | Keyframes mode. Send as a repeated field: `-F init_images=@a.png -F init_images=@b.png …`. ≥2 files. The order matches `init_image_prompts`. |
| `init_video`   | exactly one of `{init_images, init_video}` | init_video mode. A single mp4 file. Skip-pregen — feeds the final pass directly. |
| `audio_file`   | yes                                  | Drives the output video length. In pair-LoRA mode also drives the audio reactivity in the final pass. |

### Form fields

| field                  | type                                | default       | meaning |
| ---------------------- | ----------------------------------- | ------------- | ------- |
| `init_image_prompts`   | repeated string, length = N keyframes | —           | **Required iff `init_images` is set; must be empty in init_video mode.** One prompt per keyframe, same order as `init_images`. Drives the prompt-travel between keyframes. |
| `final_prompts_a`      | repeated string, ≥2 entries         | —             | The final-pass journey list (single-LoRA) or the A side of the paired blend (pair-LoRA). |
| `final_prompts_b`      | repeated string                     | `[]`          | Required for pair-LoRA, must match `final_prompts_a` length. Reject for single-LoRA. |
| `lora`                 | string                              | —             | One of: a preset index (`"21"`), a single shorthand (`"twisted-bodies-xl"`), or a comma-list (`"twisted-bodies-xl,water-xl"`). The set of valid presets and shorthands is in `plantoid/lora_index.yaml`. The cardinality picks single vs pair behaviour. |
| `fps`                  | int > 0, optional                   | see below     | Output frame rate. **In keyframes mode**, defaults to `20`. **In init_video mode**, omit and the server infers from `ffprobe(init_video).fps`; if you set it explicitly, it must match the file's encoded fps within `0.5` (else `400`). |
| `audio_band`           | `"bass"` \| `"low_mid"` \| `"mid"` \| `"treble"` | `treble` | Pair-LoRA only. The mel band the audio reactivity tracks. |
| `audio_reaction_output_gain` | float ≥ 0                  | `1.0`         | Post-smoother expander gain on the α(t) audio-reaction curve. Drives prompt blend + LoRA blend in pair-LoRA mode. `1.0` = identity; `>1` expands α toward `[0, 1]` when periodic beats compress α into a narrow middle band (try `2.0`–`2.5` for visible swings on synth bass). Dormant in single-lora passthrough. |
| `n_rungs`              | int ≥ 1                             | `2`           | StreamBatch queue depth (denoising rungs). Applied to both pregen and final stages. 2 = one rung + one buffer step (default opera_pipe behaviour). |
| `crf`                  | int in `[0, 51]`                    | `23`          | libx264 Constant Rate Factor for the muxed mp4. Plantoid 16 default is `23` (libx264 default — perceptually transparent at ~half the size of the pipeline-internal `crf 17` near-lossless setting). Lower = larger / higher quality. Applied to both pregen and final mp4s. |
| `preset`               | `"fast"` \| `"medium"` \| `"slow"`  | `medium`      | libx264 preset. `medium` is libx264's default; `slow` gets ~5-10% better size at a given crf, `fast` encodes ~3-4× quicker. |
| `mode`                 | `"img2img"` \| `"txt2img"`          | `img2img`     | Final-pass mode. **Note**: the JJ baseline uses `latent_carryover`, which the runner only accepts under `mode=img2img`. Passing `mode=txt2img` today will fail at runner-validation time (job → `failed`). Keep `mode=img2img` for the canonical pipeline. |
| `h_smoothing`          | bool                                | `false`       | Cross-frame H-smoothing toggle for the final pass. **Default off** (the JJ baseline relies on `latent_carryover` for cross-frame momentum; stacking H-smoothing on top is usually over-damped). When `true`, the orchestrator restores the opera-pipe triplet (`sigma=2.0, beta_low=1.0, beta_high=0.3`). |
| `controlnet`           | bool                                | `true`        | Final-pass depth ControlNet on/off. When on, every frame of the source video (pregen output or your `init_video`) is depth-estimated and used as the conditioning image. |
| `cn_scale`             | float in `(0, 2]`                   | `0.55`        | Final-pass ControlNet conditioning strength. Only meaningful when `controlnet=true`. |
| `seed`                 | int, optional                       | random        | Omit for fresh random seeds. The chosen value is recorded in the run output so the result is reproducible after the fact. |

### Validation errors (`400`)

- both or neither of `{init_images, init_video}` set
- keyframes mode: fewer than 2 keyframes
- keyframes mode: `init_image_prompts` count doesn't match `init_images` count
- init_video mode: `init_image_prompts` non-empty
- init_video mode: explicit `fps` doesn't match file fps within 0.5
- fewer than 2 entries in `final_prompts_a`
- pair-LoRA: `final_prompts_b` length doesn't match `final_prompts_a`
- single-LoRA: `final_prompts_b` is non-empty
- unknown LoRA preset / shorthand
- `cn_scale` outside `(0, 2]`
- `audio_reaction_output_gain` < 0
- `n_rungs` < 1
- `crf` outside `[0, 51]` or `preset` not in `{fast, medium, slow}`
- audio too short to fit the schedule (`target_frames < 3·N − 2`)
- `mode` ≠ `"img2img"` / `"txt2img"`

### Soft warnings (`200`, included in `summary.warnings`)

- init_video mode: `|L_init − target_frames| / target_frames > 5%` —
  the supplied video will be looped (if short) or truncated (if long)
  to fit the audio-driven frame budget. The seam / cut will be
  visible if the drift is large.

### Response — `200 OK`

Keyframes mode:

```json
{
  "job_id": "9ec83a51b2c…",
  "status": "queued",
  "summary": {
    "mode": "keyframes",
    "n_keyframes": 3,
    "n_final_prompts": 6,
    "is_pair": true,
    "audio_mode": "react",
    "audio_band": "treble",
    "controlnet": "depth-sdxl",
    "cn_scale": 0.55,
    "fps": 20,
    "target_frames": 208,
    "audio_duration_s": 10.4
  }
}
```

init_video mode:

```json
{
  "job_id": "9ec83a51b2c…",
  "status": "queued",
  "summary": {
    "mode": "init_video",
    "init_video_filename": "wan_ballerina_lossless_768x1024.mp4",
    "init_video_fps": 20.0,
    "init_video_frames": 100,
    "init_video_duration_s": 5.0,
    "n_final_prompts": 6,
    "is_pair": true,
    "audio_mode": "react",
    "audio_band": "treble",
    "controlnet": "depth-sdxl",
    "cn_scale": 0.55,
    "fps": 20,
    "target_frames": 100,
    "audio_duration_s": 5.0
  }
}
```

`audio_mode` is `"react"` for pair-LoRA and `"passthrough"` for
single-LoRA. `audio_band` is `null` in passthrough mode.

---

## `GET /api/jobs/{job_id}`

Poll for progress. Status flows: `queued` → `running` → `complete` |
`failed` | `cancelled`.

```json
{
  "job_id": "9ec83a51b2c…",
  "status": "running",
  "progress": { "stage": "pregen", "frame": 87, "total": 203 },
  "run_id": null,
  "return_code": null,
  "error": null,
  "stdout_tail": ["...", "..."]
}
```

`progress.stage` is mode-dependent:

- **keyframes mode** — cycles through `"pregen"` then `"final"`. The
  frame counter resets when the stage changes.
- **init_video mode** — only `"final"` (pregen is skipped).

Plus the brief `"loading"` / `"starting"` stages that bookend either flow.

When `status` is terminal:
- `complete` → `run_id` is set; outputs are at the run dir.
- `failed` / `cancelled` → `error` is a short string, `stdout_tail` is
  the last ~80 lines of runner output.

Viewer URL once complete:
`http://<server>/m/_installation_plantoid16/r/<run_id>`

---

## `GET /api/runs/{run_id}/file/{path}`

Downloads any file from the run's output directory by relative path.
This is how the plantoid actually pulls the video bytes once a job
finishes.

Useful paths inside a run directory:

| path                       | what it is |
| -------------------------- | ---------- |
| `video.mp4`                | the output video with audio muxed in (this is what the plantoid plays) |
| `manifest.yaml`            | the resolved final-stage manifest, including the seed that was actually used |
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

You don't pick the frame count — it's derived from your audio. The
formula:

```
target_frames = ceil(audio_duration_s * fps)
H = ceil(target_frames / (3N - 2))      # T:H ratio is 2:1
T = 2 * H
frames = (N - 1) * (T + H) + H          # ≥ target_frames
```

In **keyframes mode**, the formula is applied to each stage with its
own prompt count (N₁ = number of keyframes, N₂ = length of
`final_prompts_a`); the server absorbs the inevitable few-frame
mismatch by looping the keyframe-travel video at the final-pass
boundary. In **init_video mode**, only N₂ matters; your supplied video
is looped (if shorter than `target_frames`) or truncated (if longer)
to fit the audio-driven frame budget.

The output `video.mp4` length always matches the audio length.

---

## Reproducible baseline — both modes, exact curl

Both snippets below are the **byte-for-byte multipart payload** that
`plantoid/16/caller.py` emits with its default flags. Running either
of these against a fresh server reproduces the canonical baseline
runs: `20260428-102859__installation_plantoid16_job_e45f9a1c`
(keyframes) and `20260428-103200__installation_plantoid16_job_cdeeb4a6`
(init_video). The seed is random — every other field is fixed.

The Python equivalents:

```bash
# Keyframes mode (full pipe — pregen + final)
uv run python plantoid/16/caller.py

# init_video mode (skip pregen; fps inferred from file)
uv run python plantoid/16/caller.py \
  --init-video plantoid/16/assets/wan_ballerina_lossless_768x1024.mp4 \
  --audio plantoid/16/assets/audio_5s.wav \
  --n-final 2
```

### Curl A — keyframes mode (full pipe, pair-LoRA, 3 keyframes, 6 final prompts)

```bash
curl -X POST http://127.0.0.1:8000/api/installations/plantoid16 \
  -F "init_images=@plantoid/16/assets/keyframes/keyframe_00.png" \
  -F "init_images=@plantoid/16/assets/keyframes/keyframe_01.png" \
  -F "init_images=@plantoid/16/assets/keyframes/keyframe_02.png" \
  -F "audio_file=@plantoid/16/assets/audio.wav" \
  -F "lora=21" \
  -F "audio_band=treble" \
  -F "audio_reaction_output_gain=1.0" \
  -F "n_rungs=2" \
  -F "crf=23" \
  -F "preset=medium" \
  -F "mode=img2img" \
  -F "h_smoothing=false" \
  -F "controlnet=true" \
  -F "cn_scale=0.55" \
  -F "init_image_prompts=black and white photograph of a single tall vertical figure on a dark background, minimalist composition, high contrast, grayscale" \
  -F "init_image_prompts=black and white photograph of two intertwined figures embracing on a dark background, dynamic composition, high contrast, grayscale" \
  -F "init_image_prompts=black and white photograph of a horizontal sprawling cluster of figures on a dark background, expansive composition, high contrast, grayscale" \
  -F "final_prompts_a=twisted bodies Pale beige sculptural forms with flowing organic shapes and smooth ovoid elements against black background." \
  -F "final_prompts_a=twisted bodies Pale cream sculptural figures with flowing organic tendrils merging together against black background." \
  -F "final_prompts_a=twisted bodies Abstract organic sculpture in cream and beige tones with flowing, perforated forms on black background." \
  -F "final_prompts_a=twisted bodies Pale beige jellyfish cluster with flowing tentacles on black background, organic sculptural form." \
  -F "final_prompts_a=twisted bodies Pale beige sculptural figures in dynamic motion against black background, organic flowing forms intertwined." \
  -F "final_prompts_a=twisted bodies Pale sculpted figures with flowing drapery intertwined against black background, baroque style marble sculpture composition." \
  -F "final_prompts_b=water Dramatic black and white portrait of face submerged in splashing water against dark background." \
  -F "final_prompts_b=water Dynamic water splash frozen mid-motion against black background, high contrast monochrome photography with crystalline droplet details." \
  -F "final_prompts_b=water Monochromatic water sculpture forming human bust silhouette with splashing droplets against black background." \
  -F "final_prompts_b=water Water splash forming human figure silhouette against black background, frozen motion, dramatic lighting." \
  -F "final_prompts_b=water Transparent water sculpture forming human face with dynamic splashing droplets on black background." \
  -F "final_prompts_b=water Black and white water splash forming human figure silhouette against dark background, high contrast photography."
```

Notes on what's missing and why:

- **No `fps=…` field.** `caller.py --fps` defaults to `None`, so the
  caller omits the field. The server falls back to `DEFAULT_FPS=20`
  in keyframes mode (and would have inferred from `ffprobe(init_video)`
  in init_video mode). This is the recommended shape — set `fps`
  explicitly only if you want to override the default.
- **No `seed=…` field.** `caller.py --seed` defaults to `None`. The
  pipeline picks a random seed at resolve time and writes it to the
  output `manifest.yaml`. To reproduce a specific run, copy that seed
  and add `-F "seed=<int>"`.
- **`h_smoothing=false`** matches the new JJ baseline (the H smoother
  is off by default; `latent_carryover` carries cross-frame momentum
  instead). Pass `h_smoothing=true` to restore the opera-pipe triplet.

### Curl B — init_video mode (skip pregen, 1 mp4, 2 final prompts)

```bash
curl -X POST http://127.0.0.1:8000/api/installations/plantoid16 \
  -F "init_video=@plantoid/16/assets/wan_ballerina_lossless_768x1024.mp4" \
  -F "audio_file=@plantoid/16/assets/audio_5s.wav" \
  -F "lora=21" \
  -F "audio_band=treble" \
  -F "audio_reaction_output_gain=1.0" \
  -F "n_rungs=2" \
  -F "crf=23" \
  -F "preset=medium" \
  -F "mode=img2img" \
  -F "h_smoothing=false" \
  -F "controlnet=true" \
  -F "cn_scale=0.55" \
  -F "final_prompts_a=twisted bodies Pale beige sculptural forms with flowing organic shapes and smooth ovoid elements against black background." \
  -F "final_prompts_a=twisted bodies Pale cream sculptural figures with flowing organic tendrils merging together against black background." \
  -F "final_prompts_b=water Dramatic black and white portrait of face submerged in splashing water against dark background." \
  -F "final_prompts_b=water Dynamic water splash frozen mid-motion against black background, high contrast monochrome photography with crystalline droplet details."
```

Notes specific to init_video mode:

- **No `init_image_prompts=…` field.** init_video mode skips pregen,
  so there are no per-keyframe prompts. Sending any returns 400.
- **No `fps=…` field.** The server infers from
  `ffprobe(init_video).avg_frame_rate`. The supplied lossless
  ballerina is encoded at 20 fps so the server uses `fps=20`.
- **Recommended encoding for the uploaded init_video:** match the
  delivery fps you want, and aim for a duration ≈ the audio length.
  The server will loop a short video or truncate a long one to fit
  `target_frames = ceil(audio_duration_s * fps)`, but mismatch beyond
  ±5% triggers a soft warning in `summary.warnings` (visible loop
  seam or unused tail). The lossless ballerina + audio_5s.wav above
  are 5.0s + 5.0s = no drift.
