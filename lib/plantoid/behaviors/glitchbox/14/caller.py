"""Plantoid 14 simulator — pretends to be the external installation client.

In production this is replaced by the LLM-driven prompt picker + the
actual installation runtime. For now it just:

  1. Picks N prompts straight from one of the glitchbox XL prompt files
     under ./prompts/ (no LLM yet — raw captions, already trigger-prefixed).
  2. POSTs everything as multipart/form-data to
     ``/api/installations/plantoid14`` on the local server.
  3. Polls ``/api/jobs/{id}`` until terminal, prints the run_id and the
     viewer URL when complete.

Defaults match the reference run
``20260425-232151_cell_C3_twisted_water_p6_w05_w05_cn_h``:
LoRA preset 21 (twisted-bodies-xl + water-xl), 6 prompts from
prompts_twisted_bodies_XL.txt, controlnet on, fps 20.

Usage::

    uv run python plantoid/14/caller.py
    uv run python plantoid/14/caller.py --lora twisted-bodies-xl --n 4
    uv run python plantoid/14/caller.py --lora 21 --prompts-file prompts_water_XL.txt
    uv run python plantoid/14/caller.py --no-controlnet --server http://10.0.0.5:8000
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import requests
import yaml

HERE = Path(__file__).resolve().parent
# Prompts are shared across plantoid-N installations (same XL caption
# files), so they live one level up at plantoid/prompts/.
PROMPTS_DIR = HERE.parent / "prompts"
LORA_INDEX_YAML = HERE.parent / "lora_index.yaml"
#DEFAULT_SERVER = "http://127.0.0.1:8000"
DEFAULT_SERVER = "http://100.74.77.125:8000"



# ---------------------------------------------------------------------------
# Local-only LoRA index lookup. The plantoid runtime has no codebase
# access — all it ships with is plantoid/lora_index.yaml, refreshed via
# plantoid/refresh_lora_index.sh whenever glitchbox lora_config changes.
# Validation here is a pure-Python yaml load + a few set checks.
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
        sys.exit(f"{LORA_INDEX_YAML} is malformed; expected shorthands + presets")
    return idx


def validate_lora(spec: str, idx: dict) -> None:
    """Raise SystemExit on bad spec. Accepts preset index, single
    shorthand, or comma-list — same surface as the multipart ``lora`` field.
    """
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
        sys.exit(
            f"unknown shorthand(s): {unknown}. "
            f"See {LORA_INDEX_YAML} for the full list."
        )


def describe_lora(spec: str, idx: dict) -> str:
    """One-liner of what ``spec`` resolves to. For user-facing logging."""
    s = spec.strip()
    if not s or s.lower() == "none":
        return "no_lora"
    if s.lstrip("-").isdigit() and s in idx["presets"]:
        shorts = idx["presets"][s]
        if not shorts:
            return f"preset {s} (no_lora)"
        return f"preset {s} ({' + '.join(shorts)})"
    return s.replace(",", " + ")


def lora_count(spec: str, idx: dict) -> int:
    """How many LoRAs ``spec`` resolves to. Used by the caller to know
    whether a ``lora_weights`` field is meaningful (≥2)."""
    s = spec.strip()
    if not s or s.lower() == "none":
        return 0
    if s.lstrip("-").isdigit():
        return len(idx["presets"].get(s, []))
    return len([c for c in s.split(",") if c.strip()])


def load_prompts(prompts_file: Path, n: int) -> list[str]:
    """Read first ``n`` non-blank lines from a glitchbox XL prompt file."""
    if not prompts_file.is_file():
        sys.exit(f"prompts file missing: {prompts_file}")
    lines = [
        ln.strip() for ln in prompts_file.read_text().splitlines() if ln.strip()
    ]
    if len(lines) < n:
        sys.exit(f"only {len(lines)} prompts in {prompts_file.name}, asked for {n}")
    return lines[:n]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--server", default=DEFAULT_SERVER,
                        help=f"Backend origin (default: {DEFAULT_SERVER})")
    parser.add_argument("--init-image", type=Path,
                        default=HERE / "assets" / "init_image.jpg")
    parser.add_argument("--audio", type=Path,
                        default=HERE / "assets" / "audio.wav")
    parser.add_argument("--prompts-file", type=str,
                        default="prompts_twisted_bodies_XL.txt",
                        help="Filename under ./prompts/ to draw from")
    parser.add_argument("--n", type=int, default=6,
                        help="Number of prompts to send (first N lines)")
    parser.add_argument("--lora", type=str, default="21",
                        help="Preset index (e.g. '21'), single shorthand "
                             "(e.g. 'twisted-bodies-xl'), or comma-list "
                             "(e.g. 'twisted-bodies-xl,water-xl').")
    parser.add_argument("--lora-weights", type=str, default=None,
                        help="Comma-separated floats matching the LoRA "
                             "count, e.g. '0.7,0.3' for a 70/30 pair. "
                             "Only meaningful for ≥2 LoRAs. When omitted "
                             "and the spec resolves to a pair/tuple, the "
                             "caller sends an explicit equal-split (so the "
                             "field stays visible in the curl reproduce).")
    parser.add_argument("--fps", type=int, default=20)
    parser.add_argument("--no-controlnet", dest="controlnet",
                        action="store_false", default=True)
    parser.add_argument("--cn-scale", type=float, default=0.55,
                        help="ControlNet conditioning strength in (0, 2]. "
                             "Only meaningful when controlnet is on.")
    parser.add_argument("--audio-reaction-output-gain", type=float,
                        default=1.0,
                        help="Post-smoother expander gain on the α(t) "
                             "audio-reaction curve. Drives all audio-"
                             "reactive consumers (zoom / prompt blend / "
                             "LoRA blend). Default 1.0 (identity); >1 "
                             "expands α toward [0, 1]. Plantoid 14 is "
                             "passthrough today (controllers dormant), "
                             "so this is harmless until a sound-reactive "
                             "p14 mode is added.")
    
    parser.add_argument("--n-rungs", type=int, default=2,
                        help="StreamBatch queue depth (denoising rungs). "
                             "Default 2.")
    parser.add_argument("--crf", type=int, default=32,
                        help="libx264 CRF for the muxed mp4. Default 32 "
                             "(small files for plantoid download). Lower "
                             "= bigger / higher quality.")
    parser.add_argument("--preset", choices=["fast", "medium", "slow"],
                        default="slow",
                        help="libx264 preset (compression efficiency vs "
                             "encode speed). Default slow.")
    
    parser.add_argument("--audio-mode", default="passthrough",
                        choices=["passthrough"],
                        help="Plantoid 14 only supports passthrough "
                             "(static audio overlay, no controllers). "
                             "Argument exists so the curl reproduce shows "
                             "the field for future installations.")
    parser.add_argument("--mode", default="img2img",
                        choices=["img2img", "txt2img"],
                        help="Diffusion mode. img2img anchors to init_image; "
                             "txt2img generates from prompts only.")
    parser.add_argument("--h-smoothing", dest="h_smoothing",
                        default=True, action="store_true",
                        help="Cross-frame x0 smoothing on (default).")
    parser.add_argument("--no-h-smoothing", dest="h_smoothing",
                        action="store_false",
                        help="Disable x0 smoothing (sigma=0 in the runner).")
    # No default — when omitted, the server forwards None and the pipeline
    # picks a fresh random seed (still recorded in the resolved manifest).
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument("--no-wait", action="store_true",
                        help="Submit the job and exit without polling.")


    
    args = parser.parse_args()

    # Local-only validation against plantoid/lora_index.yaml — no server
    # round-trip. Fail fast on a bad --lora.
    idx = load_lora_index()
    validate_lora(args.lora, idx)

    # Weights handling. For pairs/tuples, default to equal-split so the
    # curl reproduce always shows the field (discoverable knob). For
    # single/no_lora, weights aren't meaningful — reject if the user set
    # them.
    n_loras = lora_count(args.lora, idx)
    if args.lora_weights is not None:
        if n_loras < 2:
            sys.exit(
                f"--lora-weights only valid for ≥2 LoRAs "
                f"(spec resolves to {n_loras})"
            )
        try:
            weights_parsed = [float(w) for w in args.lora_weights.split(",") if w.strip()]
        except ValueError as exc:
            sys.exit(f"--lora-weights must be comma-separated floats: {exc}")
        if len(weights_parsed) != n_loras:
            sys.exit(
                f"--lora-weights count {len(weights_parsed)} != lora count {n_loras}"
            )
    elif n_loras >= 2:
        weights_parsed = [round(1.0 / n_loras, 4)] * n_loras
        args.lora_weights = ",".join(str(w) for w in weights_parsed)

    prompts_path = PROMPTS_DIR / args.prompts_file
    prompts = load_prompts(prompts_path, args.n)
    print(f"[plantoid14] {args.n} prompts from {prompts_path.name}:")
    for i, p in enumerate(prompts):
        print(f"  {i}: {p[:80]}{'…' if len(p) > 80 else ''}")
    cn_str = f"on@{args.cn_scale}" if args.controlnet else "off"
    print(f"[plantoid14] lora={args.lora!r} → {describe_lora(args.lora, idx)}  "
          f"weights={args.lora_weights or '(default)'}  "
          f"fps={args.fps}  cn={cn_str}  "
          f"audio_mode={args.audio_mode}  "
          f"seed={args.seed if args.seed is not None else 'random'}")

    files = {
        "init_image": (args.init_image.name, args.init_image.open("rb"),
                       "application/octet-stream"),
        "audio_file": (args.audio.name, args.audio.open("rb"),
                       "application/octet-stream"),
    }
    # Multipart with repeated 'prompts' fields (FastAPI collects → list[str]).
    data = [
        ("lora", args.lora),
        ("fps", str(args.fps)),
        ("controlnet", "true" if args.controlnet else "false"),
        ("cn_scale", str(args.cn_scale)),
        ("audio_mode", args.audio_mode),
        ("audio_reaction_output_gain", str(args.audio_reaction_output_gain)),
        ("n_rungs", str(args.n_rungs)),
        ("crf", str(args.crf)),
        ("preset", args.preset),
        ("mode", args.mode),
        ("h_smoothing", "true" if args.h_smoothing else "false"),
    ] + [("prompts", p) for p in prompts]
    if args.lora_weights:
        data.append(("lora_weights", args.lora_weights))
    # Only send seed when explicitly provided — empty/missing field tells
    # the server to forward None to the resolver, which picks random.
    if args.seed is not None:
        data.append(("seed", str(args.seed)))

    url = args.server.rstrip("/") + "/api/installations/plantoid14"
    print(f"[plantoid14] POST {url}")
    r = requests.post(url, files=files, data=data, timeout=60)
    if r.status_code != 200:
        sys.exit(f"server returned {r.status_code}: {r.text}")
    job = r.json()
    summary = job.get("summary", {})
    print(f"[plantoid14] enqueued job {job['job_id'][:8]}  "
          f"frames={summary.get('frames')}  duration={summary.get('duration_s')}s  "
          f"T={summary.get('transition_frames')} H={summary.get('hold_frames')}")
    print(f"[plantoid14] resolved loras:")
    for entry in summary.get("loras", []):
        print(f"  {entry}")

    if args.no_wait:
        print(f"[plantoid14] not waiting; poll {args.server}/api/jobs/{job['job_id']}")
        return

    # Poll until terminal.
    job_url = args.server.rstrip("/") + f"/api/jobs/{job['job_id']}"
    print(f"[plantoid14] polling {job_url}")
    last_stage = None
    last_frame = -1
    while True:
        time.sleep(args.poll_interval)
        try:
            j = requests.get(job_url, timeout=10).json()
        except Exception as exc:
            print(f"[plantoid14] poll failed: {exc}")
            continue
        stage = j.get("progress", {}).get("stage")
        frame = j.get("progress", {}).get("frame", 0)
        total = j.get("progress", {}).get("total", 0)
        if stage != last_stage or frame != last_frame:
            print(f"  [{j['status']}] stage={stage}  frame {frame}/{total}")
            last_stage, last_frame = stage, frame
        if j["status"] in ("complete", "failed", "cancelled"):
            print(f"[plantoid14] terminal: {j['status']}  return_code={j.get('return_code')}")
            if j.get("run_id"):
                print(f"[plantoid14] run_id={j['run_id']}")
                print(f"[plantoid14] viewer: {args.server}/m/_installation_plantoid14/r/{j['run_id']}")
            if j["status"] != "complete" and j.get("error"):
                print(f"[plantoid14] error: {j['error']}")
                tail = j.get("stdout_tail", [])
                if tail:
                    print("--- stdout tail ---")
                    print("\n".join(tail[-20:]))
            sys.exit(0 if j["status"] == "complete" else 1)


if __name__ == "__main__":
    main()
