"""Plantoid 16 simulator — pretends to be the external installation client.

In production this is the actual plantoid runtime, which:
  1. has N keyframe images on hand (artistic curation upstream),
  2. picks a LoRA spec + final prompts (LLM in prod; raw caption files here),
  3. POSTs everything as multipart/form-data to
     ``/api/installations/plantoid16``.

Two upload shapes, mutually exclusive:

  * keyframes mode (default): N keyframe images + N init_image_prompts.
    Server runs Stage A (build init video) + Stage 1 (pregen prompt-
    travel) + Stage 2 (final pass).
  * init_video mode (``--init-video PATH``): a pre-built mp4. Server
    skips Stage A + Stage 1 and feeds the upload straight into the
    final pass. fps is inferred from the file when ``--fps`` is omitted.

Defaults match the cell_pregen_* reference runs:
  * keyframes:    plantoid/16/assets/keyframes/keyframe_*.png  (3 b&w shots)
  * audio:        plantoid/16/assets/audio.wav  (10s opera clip)
  * init prompts: plantoid/16/init_image_prompts.txt
                  (the 3 b&w compositional prompts that produced the
                   keyframes; drive the prompt-travel between them)
  * lora:         preset 21 (twisted-bodies-xl + water-xl)
  * final A:      first N lines of prompts_twisted_bodies_XL.txt
  * final B:      first N lines of prompts_water_XL.txt

Usage::

    uv run python plantoid/16/caller.py
    uv run python plantoid/16/caller.py --lora twisted-bodies-xl  # single
    uv run python plantoid/16/caller.py --no-wait                  # submit & exit
    # init_video mode (skip pregen, fps inferred from file)
    uv run python plantoid/16/caller.py \\
        --init-video plantoid/16/assets/wan_ballerina_lossless_768x1024.mp4
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import requests
import yaml

HERE = Path(__file__).resolve().parent
PROMPTS_DIR = HERE.parent / "prompts"
LORA_INDEX_YAML = HERE.parent / "lora_index.yaml"
DEFAULT_SERVER = "http://127.0.0.1:8000"


# ---------------------------------------------------------------------------
# Local-only LoRA index lookup (same logic as plantoid14's caller). The
# plantoid runtime ships with plantoid/lora_index.yaml — no codebase
# import, no network call to validate.
# ---------------------------------------------------------------------------

def load_lora_index() -> dict:
    if not LORA_INDEX_YAML.is_file():
        sys.exit(
            f"missing {LORA_INDEX_YAML}. "
            f"Run plantoid/refresh_lora_index.sh to generate it."
        )
    with LORA_INDEX_YAML.open() as f:
        idx = yaml.safe_load(f) or {}
    if not isinstance(idx.get("shorthands"), list) or not isinstance(
        idx.get("presets"), dict,
    ):
        sys.exit(f"{LORA_INDEX_YAML} is malformed")
    return idx


def validate_lora(spec: str, idx: dict) -> None:
    s = spec.strip()
    if not s or s.lower() == "none":
        return
    if s.lstrip("-").isdigit():
        if s not in idx["presets"]:
            sys.exit(
                f"unknown preset index {s!r}. "
                f"Known: {sorted(int(k) for k in idx['presets'])}"
            )
        return
    candidates = [c.strip() for c in s.split(",") if c.strip()]
    known = set(idx["shorthands"])
    unknown = [c for c in candidates if c not in known]
    if unknown:
        sys.exit(f"unknown shorthand(s): {unknown}. See {LORA_INDEX_YAML}.")


def describe_lora(spec: str, idx: dict) -> str:
    s = spec.strip()
    if not s or s.lower() == "none":
        return "no_lora"
    if s.lstrip("-").isdigit() and s in idx["presets"]:
        shorts = idx["presets"][s]
        if not shorts:
            return f"preset {s} (no_lora)"
        return f"preset {s} ({' + '.join(shorts)})"
    return s.replace(",", " + ")


def lora_resolved_shorthands(spec: str, idx: dict) -> list[str]:
    """Resolve the spec to its ordered shorthand list. Used to pick the
    default per-LoRA prompt files for the final pass."""
    s = spec.strip()
    if not s or s.lower() == "none":
        return []
    if s.lstrip("-").isdigit():
        return list(idx["presets"].get(s, []))
    return [c.strip() for c in s.split(",") if c.strip()]


# ---------------------------------------------------------------------------
# Prompt file loading. Maps a lora shorthand to its corresponding glitchbox
# XL prompt file (best-effort name normalization — if the file isn't under
# plantoid/prompts/, the user can override with --final-prompts-a/-b).
# ---------------------------------------------------------------------------

def lora_prompts_filename(shorthand: str) -> str:
    """Convert ``twisted-bodies-xl`` → ``prompts_twisted_bodies_XL.txt``.

    The XL prompt files are mostly ``prompts_<snake_case>_XL.txt`` (with
    a few outliers like ``prompts_SAN_XL.txt`` / ``prompts_papercut_xl.txt``
    that don't fit cleanly). Caller can override via --final-prompts-* if
    the inferred name doesn't resolve.
    """
    base = shorthand.replace("-xl", "").replace("-", "_")
    return f"prompts_{base}_XL.txt"


def load_first_n_prompts(path: Path, n: int) -> list[str]:
    if not path.is_file():
        sys.exit(f"prompts file missing: {path}")
    lines = [ln.strip() for ln in path.read_text().splitlines() if ln.strip()]
    if len(lines) < n:
        sys.exit(f"only {len(lines)} prompts in {path.name}, asked for {n}")
    return lines[:n]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--server", default=DEFAULT_SERVER)
    parser.add_argument("--keyframes-dir", type=Path,
                        default=HERE / "assets" / "keyframes",
                        help="Keyframes-mode source dir. Ignored when "
                             "--init-video is set.")
    parser.add_argument("--init-video", type=Path, default=None,
                        help="Direct-stage-2 mode: a pre-built mp4 fed "
                             "straight into the final pass. Mutually "
                             "exclusive with --keyframes-dir / "
                             "--init-prompts-file.")
    parser.add_argument("--audio", type=Path,
                        default=HERE / "assets" / "audio.wav")
    parser.add_argument("--init-prompts-file", type=Path,
                        default=HERE / "assets" / "init_image_prompts.txt",
                        help="Keyframes-mode source. Lines = prompts "
                             "driving the prompt-travel between the "
                             "keyframes (one per keyframe). Ignored when "
                             "--init-video is set.")
    parser.add_argument("--lora", type=str, default="21",
                        help="Preset index, single shorthand, or comma-list.")
    parser.add_argument("--n-final", type=int, default=6,
                        help="How many final-pass prompts to send "
                             "(taken as the first N of the relevant XL file).")
    parser.add_argument("--final-prompts-a", type=Path, default=None,
                        help="Override default final_prompts_a source file.")
    parser.add_argument("--final-prompts-b", type=Path, default=None,
                        help="Override default final_prompts_b source file "
                             "(only used for pair LoRA).")
    parser.add_argument("--fps", type=int, default=None,
                        help="Output fps. Omit in --init-video mode and "
                             "the server will infer from the file. "
                             "Defaults to 20 in keyframes mode.")
    parser.add_argument("--audio-band", default="treble",
                        choices=["bass", "low_mid", "mid", "treble"])
    parser.add_argument("--mode", default="img2img",
                        choices=["img2img", "txt2img"],
                        help="Final-stage diffusion mode. Pregen always "
                             "uses img2img. txt2img drops the init_video "
                             "anchor in the final pass.")
    parser.add_argument("--h-smoothing", dest="h_smoothing",
                        default=False, action="store_true",
                        help="Final-stage x0 smoothing ON. Default off "
                             "(matches the JJ baseline — latent_carryover "
                             "already carries cross-frame momentum).")
    parser.add_argument("--no-h-smoothing", dest="h_smoothing",
                        action="store_false",
                        help="Force x0 smoothing off. Redundant with the "
                             "default; kept for symmetry and explicit curls.")
    parser.add_argument("--controlnet", dest="controlnet",
                        default=True, action="store_true",
                        help="Final-stage depth ControlNet on (default).")
    parser.add_argument("--no-controlnet", dest="controlnet",
                        action="store_false",
                        help="Disable final-stage ControlNet.")
    parser.add_argument("--cn-scale", type=float, default=0.55,
                        help="Final-stage ControlNet strength in (0, 2]. "
                             "Only meaningful when controlnet is on.")
    parser.add_argument("--audio-reaction-output-gain", type=float,
                        default=1.0,
                        help="Post-smoother expander gain on the α(t) "
                             "audio-reaction curve. Drives prompt blend "
                             "+ LoRA blend in pair-LoRA mode. Default "
                             "1.0 (identity); >1 expands α toward "
                             "[0, 1] when periodic beats compress α "
                             "into a narrow middle band. Dormant in "
                             "single-lora passthrough.")
    parser.add_argument("--n-rungs", type=int, default=2,
                        help="StreamBatch queue depth (denoising rungs). "
                             "Applied to both pregen and final stages. "
                             "Default 2.")
    parser.add_argument("--crf", type=int, default=23,
                        help="libx264 CRF for the muxed mp4. Default 23 "
                             "(libx264 default; perceptually transparent). "
                             "Lower = bigger / higher quality.")
    parser.add_argument("--preset", choices=["fast", "medium", "slow"],
                        default="medium",
                        help="libx264 preset. Default medium "
                             "(libx264 default — good speed/size balance).")
    parser.add_argument("--seed", type=int, default=None,
                        help="Omit for pipeline-random.")
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument("--no-wait", action="store_true",
                        help="Submit and exit without polling.")
    args = parser.parse_args()

    idx = load_lora_index()
    validate_lora(args.lora, idx)

    use_init_video = args.init_video is not None
    if use_init_video and not args.init_video.is_file():
        sys.exit(f"--init-video file not found: {args.init_video}")

    # ---- Keyframes-mode discovery (skipped in init_video mode) ------
    keyframe_files: list[Path] = []
    init_image_prompts: list[str] = []
    if not use_init_video:
        keyframe_files = sorted(args.keyframes_dir.glob("*.png")) + \
                         sorted(args.keyframes_dir.glob("*.jpg"))
        keyframe_files = [p for p in keyframe_files if p.is_file()]
        if len(keyframe_files) < 2:
            sys.exit(f"need ≥2 keyframes in {args.keyframes_dir}, "
                     f"found {len(keyframe_files)}")

        init_image_prompts = [
            ln.strip() for ln in args.init_prompts_file.read_text().splitlines()
            if ln.strip()
        ]
        if len(init_image_prompts) != len(keyframe_files):
            sys.exit(
                f"init_image_prompts count ({len(init_image_prompts)}) "
                f"must match keyframes count ({len(keyframe_files)})"
            )

    # Resolve final-prompt files. For pair: A=first lora's file,
    # B=second lora's file. For single: A=that lora's file, no B.
    shorts = lora_resolved_shorthands(args.lora, idx)
    is_pair = len(shorts) >= 2

    if args.final_prompts_a is not None:
        prompts_a_path = args.final_prompts_a
    elif shorts:
        prompts_a_path = PROMPTS_DIR / lora_prompts_filename(shorts[0])
    else:
        sys.exit("no LoRA selected — can't pick a default final_prompts_a file")
    final_prompts_a = load_first_n_prompts(prompts_a_path, args.n_final)

    final_prompts_b: list[str] = []
    if is_pair:
        if args.final_prompts_b is not None:
            prompts_b_path = args.final_prompts_b
        else:
            prompts_b_path = PROMPTS_DIR / lora_prompts_filename(shorts[1])
        final_prompts_b = load_first_n_prompts(prompts_b_path, args.n_final)

    if use_init_video:
        print(f"[plantoid16] init_video: {args.init_video}")
    else:
        print(f"[plantoid16] keyframes: {len(keyframe_files)} from {args.keyframes_dir}")
        for kf, prm in zip(keyframe_files, init_image_prompts):
            print(f"  {kf.name} ← {prm[:70]}{'…' if len(prm) > 70 else ''}")
    print(f"[plantoid16] lora={args.lora!r} → {describe_lora(args.lora, idx)} "
          f"(audio_mode={'react' if is_pair else 'passthrough'})")
    print(f"[plantoid16] final_prompts_a from {prompts_a_path.name}, "
          f"{len(final_prompts_a)} prompts")
    if is_pair:
        print(f"[plantoid16] final_prompts_b from {prompts_b_path.name}, "
              f"{len(final_prompts_b)} prompts")
    cn_str = f"on@{args.cn_scale}" if args.controlnet else "off"
    fps_str = str(args.fps) if args.fps is not None else "(infer from file)"
    print(f"[plantoid16] fps={fps_str}  audio_band={args.audio_band}  "
          f"cn={cn_str}  mode={args.mode}  "
          f"seed={args.seed if args.seed is not None else 'random'}")

    # ---- Build multipart payload ------------------------------------
    # Two upload shapes:
    #   keyframes mode: repeated `init_images=@...` (one per keyframe)
    #   init_video mode: a single `init_video=@...` upload
    # Audio is always required; form fields are list-as-repeated.
    files = []
    open_handles = []
    if use_init_video:
        iv_fh = args.init_video.open("rb")
        open_handles.append(iv_fh)
        files.append(("init_video",
                      (args.init_video.name, iv_fh, "video/mp4")))
    else:
        for kf in keyframe_files:
            fh = kf.open("rb")
            open_handles.append(fh)
            files.append(("init_images", (kf.name, fh, "image/png")))
    audio_fh = args.audio.open("rb")
    open_handles.append(audio_fh)
    files.append(("audio_file", (args.audio.name, audio_fh, "audio/wav")))

    data = [
        ("lora", args.lora),
        ("audio_band", args.audio_band),
        ("audio_reaction_output_gain", str(args.audio_reaction_output_gain)),
        ("n_rungs", str(args.n_rungs)),
        ("crf", str(args.crf)),
        ("preset", args.preset),
        ("mode", args.mode),
        ("h_smoothing", "true" if args.h_smoothing else "false"),
        ("controlnet", "true" if args.controlnet else "false"),
        ("cn_scale", str(args.cn_scale)),
    ]
    if args.fps is not None:
        # Omit when None — server infers from init_video, or falls
        # back to DEFAULT_FPS in keyframes mode.
        data.append(("fps", str(args.fps)))
    for p in init_image_prompts:
        data.append(("init_image_prompts", p))
    for p in final_prompts_a:
        data.append(("final_prompts_a", p))
    for p in final_prompts_b:
        data.append(("final_prompts_b", p))
    if args.seed is not None:
        data.append(("seed", str(args.seed)))

    url = args.server.rstrip("/") + "/api/installations/plantoid16"
    print(f"[plantoid16] POST {url}")
    try:
        r = requests.post(url, files=files, data=data, timeout=120)
    finally:
        for fh in open_handles:
            fh.close()
    if r.status_code != 200:
        sys.exit(f"server returned {r.status_code}: {r.text}")
    job = r.json()
    summary = job.get("summary", {})
    src = (
        f"init_video={summary.get('init_video_filename')!r} "
        f"@ {summary.get('init_video_fps')}fps "
        f"({summary.get('init_video_frames')} frames)"
        if summary.get("mode") == "init_video"
        else f"keyframes={summary.get('n_keyframes')}"
    )
    print(f"[plantoid16] enqueued job {job['job_id'][:8]}  "
          f"mode={summary.get('mode')}  {src}  "
          f"final_prompts={summary.get('n_final_prompts')}  "
          f"is_pair={summary.get('is_pair')}  "
          f"audio_mode={summary.get('audio_mode')}  "
          f"fps={summary.get('fps')}  "
          f"target_frames={summary.get('target_frames')}")
    for w in summary.get("warnings", []) or []:
        print(f"[plantoid16] warn: {w}")

    if args.no_wait:
        print(f"[plantoid16] not waiting; poll {args.server}/api/jobs/{job['job_id']}")
        return

    job_url = args.server.rstrip("/") + f"/api/jobs/{job['job_id']}"
    print(f"[plantoid16] polling {job_url}")
    last_stage = None
    last_frame = -1
    while True:
        time.sleep(args.poll_interval)
        try:
            j = requests.get(job_url, timeout=10).json()
        except Exception as exc:
            print(f"[plantoid16] poll failed: {exc}")
            continue
        stage = j.get("progress", {}).get("stage")
        frame = j.get("progress", {}).get("frame", 0)
        total = j.get("progress", {}).get("total", 0)
        if stage != last_stage or frame != last_frame:
            print(f"  [{j['status']}] stage={stage}  frame {frame}/{total}")
            last_stage, last_frame = stage, frame
        if j["status"] in ("complete", "failed", "cancelled"):
            print(f"[plantoid16] terminal: {j['status']}  "
                  f"return_code={j.get('return_code')}")
            if j.get("run_id"):
                print(f"[plantoid16] run_id={j['run_id']}")
                print(f"[plantoid16] viewer: {args.server}/m/_installation_plantoid16/r/{j['run_id']}")
            if j["status"] != "complete" and j.get("error"):
                print(f"[plantoid16] error: {j['error']}")
                tail = j.get("stdout_tail", [])
                if tail:
                    print("--- stdout tail ---")
                    print("\n".join(tail[-20:]))
            sys.exit(0 if j["status"] == "complete" else 1)


if __name__ == "__main__":
    main()
