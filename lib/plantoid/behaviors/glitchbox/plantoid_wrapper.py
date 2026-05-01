"""Plantoid installation wrapper.

Generic Python entry point for the installation HTTP API (see
``plantoid/14/caller.py`` for the reference simulator and
``plantoid/14/README.md`` for the full API contract).

Mirrors the role of ``glitchbox_video_journey()`` in the Plantoid
runtime's ``behavior_library.py``: one Python call, one MP4 path back.

What this adds on top of the raw HTTP call:

  1. Style-based, LLM-driven prompt generation. You hand it a *poem*
     text file plus a *style reference* prompts file (one of the
     glitchbox XL caption files under ``./prompts/``); it asks an LLM
     to write N image-prompts that illustrate the poem's ideas in the
     style of those references.
  2. Multipart submission to ``/api/installations/plantoid<N>``.
  3. Polling ``/api/jobs/{id}`` until terminal.
  4. Downloading ``video.mp4`` from ``/api/runs/{run_id}/file/...``
     to a local path that the runtime can pin to IPFS.

Importable Python API:

    from plantoid.plantoid_wrapper import plantoid_video_journey
    mp4_path = plantoid_video_journey(
        poem_path="seed42.txt",
        audio_path="audio.wav",
        init_image="init.jpg",
        style_prompts_file="prompts_twisted_bodies_XL.txt",
        n=6,
        fps=20,
        lora="21",
        cn_scale=0.55,
    )

Or as a CLI for quick testing:

    uv run python plantoid/plantoid_wrapper.py --poem ./poem.txt
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

import requests
import yaml

HERE = Path(__file__).resolve().parent
PROMPTS_DIR = HERE / "prompts"
LORA_INDEX_YAML = HERE / "lora_index.yaml"

# DEFAULT_SERVER = os.environ.get("PLANTOID_SERVER", "http://100.74.77.125:8000")
DEFAULT_SERVER = os.environ.get("PLANTOID_SERVER", "http://100.79.41.86:8002")


# ---------------------------------------------------------------------------
# LoRA index helpers (same surface as caller.py — kept local so the wrapper
# has no dependency on the per-plantoid simulator).
# ---------------------------------------------------------------------------

def _load_lora_index() -> dict:
    if not LORA_INDEX_YAML.is_file():
        raise FileNotFoundError(
            f"missing {LORA_INDEX_YAML}. "
            f"Run plantoid/refresh_lora_index.sh to generate it."
        )
    with LORA_INDEX_YAML.open() as f:
        idx = yaml.safe_load(f) or {}
    if not isinstance(idx.get("shorthands"), list) or not isinstance(
        idx.get("presets"), dict,
    ):
        raise ValueError(f"{LORA_INDEX_YAML} is malformed")
    return idx


def _validate_lora(spec: str, idx: dict) -> None:
    s = spec.strip()
    if not s or s.lower() == "none":
        return
    if s.lstrip("-").isdigit():
        if s not in idx["presets"]:
            raise ValueError(
                f"unknown preset index {s!r}. "
                f"Known: {sorted(int(k) for k in idx['presets'])}"
            )
        return
    candidates = [c.strip() for c in s.split(",") if c.strip()]
    unknown = [c for c in candidates if c not in set(idx["shorthands"])]
    if unknown:
        raise ValueError(
            f"unknown LoRA shorthand(s): {unknown}. See {LORA_INDEX_YAML}"
        )


def _lora_count(spec: str, idx: dict) -> int:
    s = spec.strip()
    if not s or s.lower() == "none":
        return 0
    if s.lstrip("-").isdigit():
        return len(idx["presets"].get(s, []))
    return len([c for c in s.split(",") if c.strip()])


# ---------------------------------------------------------------------------
# Audio duration. Used to derive fps from a target frame count.
# ---------------------------------------------------------------------------

def _audio_duration_s(path: Path) -> float:
    """Best-effort audio duration in seconds. Tries stdlib ``wave`` for .wav,
    then mutagen if installed, then ``ffprobe`` as a final fallback."""
    if path.suffix.lower() == ".wav":
        try:
            import wave
            with wave.open(str(path), "rb") as w:
                return w.getnframes() / float(w.getframerate())
        except Exception:
            pass
    try:
        from mutagen import File as _MutagenFile
        m = _MutagenFile(str(path))
        if m and getattr(m, "info", None) and m.info.length:
            return float(m.info.length)
    except Exception:
        pass
    import subprocess
    out = subprocess.check_output(
        ["ffprobe", "-v", "quiet",
         "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1",
         str(path)],
        text=True,
    ).strip()
    return float(out)


# ---------------------------------------------------------------------------
# Style-driven prompt generation. The style examples come from one of the
# glitchbox XL caption files under ./prompts/; the poem provides content;
# the LLM produces N concrete, visual prompts in the style of the examples.
# ---------------------------------------------------------------------------

def _detect_trigger(examples: list[str]) -> str:
    """Longest common WORD-prefix across all examples — the LoRA trigger
    phrase. e.g. for prompts_twisted_bodies_XL.txt every line begins with
    ``"twisted bodies "``, so this returns ``"twisted bodies"``. Returns
    ``""`` if there is no common prefix."""
    if not examples:
        return ""
    word_seqs = [ex.split() for ex in examples]
    if not all(word_seqs):
        return ""
    common: list[str] = []
    for i in range(min(len(ws) for ws in word_seqs)):
        first = word_seqs[0][i]
        if all(ws[i] == first for ws in word_seqs):
            common.append(first)
        else:
            break
    return " ".join(common)


def _apply_trigger(prompts: list[str], trigger: str) -> list[str]:
    """Idempotently prepend ``trigger`` (+ space) to any prompt that doesn't
    already start with it. Returns prompts unchanged if ``trigger`` is empty."""
    if not trigger:
        return list(prompts)
    prefix = trigger + " "
    return [
        p if p.lower().startswith(trigger.lower()) else prefix + p
        for p in prompts
    ]


def _load_style_examples(prompts_file: Path, n: int) -> list[str]:
    if not prompts_file.is_file():
        raise FileNotFoundError(f"prompts file missing: {prompts_file}")
    lines = [
        ln.strip() for ln in prompts_file.read_text().splitlines() if ln.strip()
    ]
    if len(lines) < n:
        raise ValueError(
            f"only {len(lines)} prompts in {prompts_file.name}, need at least {n}"
        )
    return lines[:n]


def prompts_from_poem(
    examples: list[str],
    poem_path: Path,
    n: int,
    model: str = "gpt-4o",
    temperature: float = 0.9,
) -> list[str]:
    """Generate ``n`` image-prompts that illustrate the poem at ``poem_path``,
    written in the style of ``examples``.

    ``examples`` are style references (raw glitchbox XL captions). The poem
    is the *content*: each generated prompt picks one image/idea/line from
    the poem and renders it as a concrete visual scene.

    Requires ``OPENAI_API_KEY`` in the environment.
    """
    poem_path = Path(poem_path)
    if not poem_path.is_file():
        raise FileNotFoundError(f"poem file missing: {poem_path}")
    poem = poem_path.read_text().strip()
    if not poem:
        raise ValueError(f"poem file is empty: {poem_path}")

    examples_block = "\n".join(f"- {ex}" for ex in examples)
    trigger = _detect_trigger(examples)

    trigger_rule = (
        f"\n\nEVERY prompt MUST start with the exact phrase "
        f"\"{trigger}\" (lowercase, verbatim). This is a LoRA trigger token, "
        f"not optional. Prompts without it are invalid."
        if trigger else ""
    )

    system = (
        "You write image-generation prompts for SDXL diffusion models in "
        "the style of glitchbox-XL captions. Each prompt is a single line: "
        "terse, concrete, sensory, packed with visual nouns and material "
        "detail (objects, postures, textures, light, color, framing). "
        "Avoid abstractions, metaphors, and adjectives without a visual "
        "anchor."
        + trigger_rule
    )
    user = (
        f"Style references — match the form, vocabulary, and density of these:\n"
        f"{examples_block}\n\n"
        f"Poem to illustrate:\n"
        f"---\n{poem}\n---\n\n"
        f"Write exactly {n} prompts. For each prompt, pick one idea, line, "
        f"or image from the poem and render it as a concrete visual scene — "
        f"NOT a paraphrase of the line. The viewer should see the image, "
        f"not read the poem. Return only the prompts, one per line, no "
        f"numbering, no commentary."
        + trigger_rule
    )

    import openai
    resp = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=temperature,
    )
    raw = resp.choices[0].message.content.strip()

    lines = [
        re.sub(r"^[\s\-\*\d\.\)]+", "", ln).strip()
        for ln in raw.splitlines()
        if ln.strip()
    ]
    if len(lines) < n:
        raise RuntimeError(
            f"LLM returned {len(lines)} prompts, asked for {n}:\n---\n{raw}\n---"
        )
    return _apply_trigger(lines[:n], trigger)


# ---------------------------------------------------------------------------
# HTTP submit / poll / download.
# ---------------------------------------------------------------------------

def _submit_job(
    server: str,
    plantoid_id: int,
    init_image: Path,
    audio_file: Path,
    prompts: list[str],
    lora: str,
    fps: int,
    controlnet: bool,
    cn_scale: float,
    strength: float,
    audio_mode: str,
    audio_reaction_output_gain: float,
    mode: str,
    h_smoothing: bool,
    lora_weights: Optional[str],
    seed: Optional[int],
) -> dict:
    files = {
        "init_image": (init_image.name, init_image.open("rb"),
                       "application/octet-stream"),
        "audio_file": (audio_file.name, audio_file.open("rb"),
                       "application/octet-stream"),
    }
    data = [
        ("lora", lora),
        ("fps", str(fps)),
        ("strength", str(strength)),
        ("controlnet", "true" if controlnet else "false"),
        ("cn_scale", str(cn_scale)),
        ("audio_mode", audio_mode),
        ("audio_reaction_output_gain", str(audio_reaction_output_gain)),
        ("mode", mode),
        ("h_smoothing", "true" if h_smoothing else "false"),
    ] + [("prompts_a", p) for p in prompts]
    if lora_weights:
        data.append(("lora_weights", lora_weights))
    if seed is not None:
        data.append(("seed", str(seed)))

    url = f"{server.rstrip('/')}/api/installations/plantoid{plantoid_id}"
    print(f"[plantoid{plantoid_id}] POST {url}")
    r = requests.post(url, files=files, data=data, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"server returned {r.status_code}: {r.text}")
    return r.json()


def _poll_job(server: str, job_id: str, poll_interval: float) -> str:
    """Poll until terminal. Returns run_id on success, raises on failure."""
    job_url = f"{server.rstrip('/')}/api/jobs/{job_id}"
    print(f"[plantoid] polling {job_url}")
    last_stage = None
    last_frame = -1
    while True:
        time.sleep(poll_interval)
        try:
            j = requests.get(job_url, timeout=10).json()
        except Exception as exc:
            print(f"[plantoid] poll failed: {exc}")
            continue
        prog = j.get("progress", {})
        stage, frame, total = prog.get("stage"), prog.get("frame", 0), prog.get("total", 0)
        if stage != last_stage or frame != last_frame:
            print(f"  [{j['status']}] stage={stage}  frame {frame}/{total}")
            last_stage, last_frame = stage, frame
        if j["status"] in ("complete", "failed", "cancelled"):
            print(f"[plantoid] terminal: {j['status']}  return_code={j.get('return_code')}")
            if j["status"] != "complete":
                tail = j.get("stdout_tail", []) or []
                err = j.get("error") or "(no error message)"
                raise RuntimeError(
                    f"installation job {j['status']}: {err}\n"
                    + "--- stdout tail ---\n"
                    + "\n".join(tail[-20:])
                )
            return j["run_id"]


def _download_video(server: str, run_id: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{run_id}.mp4"
    video_url = f"{server.rstrip('/')}/api/runs/{run_id}/file/video.mp4"
    print(f"[plantoid] downloading {video_url} → {out_path}")
    with requests.get(video_url, timeout=300, stream=True) as resp:
        resp.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in resp.iter_content(64 * 1024):
                f.write(chunk)
    return out_path


# ---------------------------------------------------------------------------
# Public API. Use this from the Plantoid runtime's behavior_library, in
# place of glitchbox_video_journey().
# ---------------------------------------------------------------------------

def plantoid_video_journey(
    plantoid_id,
    prompts: list[str],
    *, 
    lora: str = "28",
    poem_path=None,
    audio_path=None,
    init_image=None,
    trigger: str = None,
    n: int = 2,
    fps: Optional[int] = None,
    target_frames: int = 300,
    lora_weights: Optional[str] = None,
    controlnet: bool = True,
    cn_scale: float = 0.55,
    strength: float = 0.7,
    mode: str = "img2img",
    h_smoothing: bool = True,
    audio_mode: str = "passthrough",
    audio_reaction_output_gain: float = 1.0,
    seed: Optional[int] = None,
    server: str = DEFAULT_SERVER,
    output_dir = "/tmp",
    poll_interval: float = 2.0,
    llm_model: str = "gpt-4o",
) -> str:
    """Generate an installation video. Returns local MP4 path.

    Two ways to specify the prompts (exactly one required):

    Parameters
    ----------
    poem_path : path to a text file containing a poem. The wrapper LLM-generates
        ``n`` prompts illustrating it, in the style of ``style_prompts_file``.
        Mutually exclusive with ``prompts``.
    prompts : pre-built list of prompts to send as-is. The LoRA trigger phrase
        (detected from ``style_prompts_file``) is prepended to any prompt that
        doesn't already start with it. Skips the LLM step entirely. Mutually
        exclusive with ``poem_path``.
    trigger : lora trigger words
    audio_path : path to the audio file (drives video length, muxed into output).
    init_image : path to the visual anchor image.
       n : number of prompts to generate (≥ 2). More prompts = more transitions.
    fps : output frame rate.
    lora : preset index ("21"), single shorthand ("twisted-bodies-xl"), or
        comma-list. "none" / "" disables LoRA.
    lora_weights : comma-floats for ≥2 LoRAs (e.g. "0.7,0.3"). Equal-split if None.
    controlnet, cn_scale : depth-controlnet on/off, and its conditioning strength.
        cn_scale acts as the "init image grip" knob — lower = freer composition.
    mode : "img2img" anchors to init_image; "txt2img" generates from prompts only.
    h_smoothing : cross-frame smoothing on (default) / off.
    audio_mode, audio_reaction_output_gain : currently passthrough only on p14.
    seed : reproducibility. Omit for random; the actual seed is recorded
        in the run's manifest.yaml.
    server : installation server origin.
    plantoid_id : installation endpoint number ("plantoid14", "plantoid16", ...).
    output_dir : where to write the downloaded MP4.
    poll_interval : seconds between status polls.
    llm_model : OpenAI chat model used for prompt generation.
    """

    # Validate inputs: exactly one of poem_path / prompts; audio + init_image required.
    if (poem_path is None) == (prompts is None):
        raise ValueError("Provide exactly one of `poem_path` or `prompts`.")
    if audio_path is None or init_image is None:
        raise ValueError("audio_path and init_image are required.")

    if poem_path is not None:
        poem_path = Path(poem_path)
    audio_path = Path(audio_path)
    init_image = Path(init_image)
    output_dir = Path(output_dir)

    for label, p in (("audio_path", audio_path), ("init_image", init_image)):
        if not p.is_file():
            raise FileNotFoundError(f"{label} missing: {p}")

    # Derive fps from audio length when not given explicitly, aiming for
    # ~target_frames in the output. The server rounds frames up via
    # ceil(duration * fps), so the realised count is target_frames or one above.
    if fps is None:
        duration = _audio_duration_s(audio_path)
        if duration <= 0:
            raise ValueError(f"could not determine duration of {audio_path}")
        fps = max(1, round(target_frames / duration))
        print(f"[plantoid{plantoid_id}] audio={duration:.2f}s, "
              f"target={target_frames}f → fps={fps} "
              f"(≈{int(round(duration * fps))} frames)")

    # Validate LoRA spec locally before submitting.
    idx = _load_lora_index()
    _validate_lora(lora, idx)
    n_loras = _lora_count(lora, idx)
    if lora_weights is not None and n_loras < 2:
        raise ValueError(
            f"lora_weights only valid for ≥2 LoRAs (spec resolves to {n_loras})"
        )
    if lora_weights is None and n_loras >= 2:
        weights = [round(1.0 / n_loras, 4)] * n_loras
        lora_weights = ",".join(str(w) for w in weights)

    # Style file is consulted in BOTH paths — for trigger detection.
    # style_path = PROMPTS_DIR / style_prompts_file
    # examples = _load_style_examples(style_path, max(n, 2))
    # trigger = _detect_trigger(examples)
    # if trigger:
    #     print(f"[plantoid{plantoid_id}] detected LoRA trigger: {trigger!r}")

    if prompts is  None:
        raise ValueError("You need to provide a list of prompts !")

    if trigger:
        prompts = _apply_trigger(prompts, trigger)
    
    print(f"[plantoid{plantoid_id}] using {len(prompts)} provided prompts:")
    # else:
    #     # Poem-driven: LLM generates n prompts in the style of the examples.
    #     print(f"[plantoid{plantoid_id}] {n} style examples from {style_path.name}; "
    #           f"generating poem-inspired prompts from {poem_path.name}")
    #     prompts = prompts_from_poem(examples, poem_path, n, model=llm_model)

    for i, p in enumerate(prompts):
        print(f"  {i}: {p[:80]}{'…' if len(p) > 80 else ''}")

    # Submit, poll, download.
    job = _submit_job(
        server=server,
        plantoid_id=plantoid_id,
        init_image=init_image,
        audio_file=audio_path,
        prompts=prompts,
        lora=lora,
        fps=fps,
        controlnet=controlnet,
        cn_scale=cn_scale,
        strength=strength,
        audio_mode=audio_mode,
        audio_reaction_output_gain=audio_reaction_output_gain,
        mode=mode,
        h_smoothing=h_smoothing,
        lora_weights=lora_weights,
        seed=seed,
    )
    summary = job.get("summary", {})
    print(f"[plantoid{plantoid_id}] enqueued job {job['job_id'][:8]}  "
          f"frames={summary.get('frames')}  duration={summary.get('duration_s')}s")

    run_id = _poll_job(server, job["job_id"], poll_interval)
    return str(_download_video(server, run_id, output_dir))


# ---------------------------------------------------------------------------
# CLI for testing — mirrors caller.py's surface but takes a poem instead of
# a static prompts file.
# ---------------------------------------------------------------------------

def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="Plantoid installation wrapper — poem in, MP4 out.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--poem", type=Path, default=None,
                        help="Poem text file (the content to illustrate). "
                             "Mutually exclusive with --prompts-file-direct.")
    parser.add_argument("--prompts-file-direct", type=Path, default=None,
                        help="File of pre-built prompts (one per line). "
                             "Bypasses the LLM; trigger phrase from "
                             "--style-prompts-file is still prepended where "
                             "missing. Mutually exclusive with --poem.")
    parser.add_argument("--audio", type=Path,
                        default=HERE / "14" / "assets" / "audio.wav")
    parser.add_argument("--init-image", type=Path,
                        default=HERE / "14" / "assets" / "init_image.jpg")
    parser.add_argument("--style-prompts-file", type=str,
                        default="prompts_twisted_bodies_XL.txt",
                        help="Filename under ./prompts/ used as style references.")
    parser.add_argument("--n", type=int, default=6)
    parser.add_argument("--fps", type=int, default=None,
                        help="Output frame rate. When omitted, derived from "
                             "--target-frames and the audio length so the "
                             "output is roughly --target-frames frames.")
    parser.add_argument("--target-frames", type=int, default=300,
                        help="Target output frame count (default 300). "
                             "Ignored when --fps is given explicitly.")
    parser.add_argument("--lora", type=str, default="21")
    parser.add_argument("--lora-weights", type=str, default=None)
    parser.add_argument("--no-controlnet", dest="controlnet",
                        action="store_false", default=True)
    parser.add_argument("--cn-scale", type=float, default=0.55)
    parser.add_argument("--mode", default="img2img",
                        choices=["img2img", "txt2img"])
    parser.add_argument("--no-h-smoothing", dest="h_smoothing",
                        action="store_false", default=True)
    parser.add_argument("--audio-mode", default="passthrough",
                        choices=["passthrough"])
    parser.add_argument("--audio-reaction-output-gain", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--server", default=DEFAULT_SERVER)
    parser.add_argument("--plantoid-id", type=int, default=14)
    parser.add_argument("--output-dir", type=Path, default=Path("/tmp"))
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument("--llm-model", type=str, default="gpt-4o")
    args = parser.parse_args()

    if (args.poem is None) == (args.prompts_file_direct is None):
        parser.error("Pass exactly one of --poem or --prompts-file-direct.")

    direct_prompts = None
    if args.prompts_file_direct is not None:
        direct_prompts = [
            ln.strip()
            for ln in args.prompts_file_direct.read_text().splitlines()
            if ln.strip()
        ]
        if len(direct_prompts) < 2:
            parser.error(
                f"--prompts-file-direct must contain ≥2 non-blank lines "
                f"(got {len(direct_prompts)})"
            )

    try:
        path = plantoid_video_journey(
            poem_path=args.poem,
            audio_path=args.audio,
            init_image=args.init_image,
            prompts=direct_prompts,
            style_prompts_file=args.style_prompts_file,
            n=args.n,
            fps=args.fps,
            target_frames=args.target_frames,
            lora=args.lora,
            lora_weights=args.lora_weights,
            controlnet=args.controlnet,
            cn_scale=args.cn_scale,
            mode=args.mode,
            h_smoothing=args.h_smoothing,
            audio_mode=args.audio_mode,
            audio_reaction_output_gain=args.audio_reaction_output_gain,
            seed=args.seed,
            server=args.server,
            plantoid_id=args.plantoid_id,
            output_dir=args.output_dir,
            poll_interval=args.poll_interval,
            llm_model=args.llm_model,
        )
    except Exception as e:
        sys.exit(f"[plantoid_wrapper] failed: {e}")
    print(f"[plantoid_wrapper] mp4 → {path}")


if __name__ == "__main__":
    _cli()
