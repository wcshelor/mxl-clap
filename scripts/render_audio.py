from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from score_embedding_lab.audio_rendering import DEFAULT_SAMPLE_RATE, render_score_to_wav, _resolve_fluidsynth_binary, _resolve_soundfont_path
from score_embedding_lab.config import AUDIO_MANIFEST, DATA_AUDIO_DIR, DATA_MIDI_DIR, DATA_RAW_EXCERPTS_GENERATED, EXCERPT_MANIFEST
from score_embedding_lab.io import load_score_auto


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render generated score excerpts to piano MIDI and WAV.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=EXCERPT_MANIFEST,
        help="Excerpt manifest produced by scripts/extract_excerpts.py.",
    )
    parser.add_argument(
        "--excerpt-dir",
        type=Path,
        default=DATA_RAW_EXCERPTS_GENERATED,
        help="Fallback directory for excerpt MusicXML files when the manifest omits a path.",
    )
    parser.add_argument("--midi-dir", type=Path, default=DATA_MIDI_DIR, help="Directory for MIDI output.")
    parser.add_argument("--audio-dir", type=Path, default=DATA_AUDIO_DIR, help="Directory for WAV output.")
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=AUDIO_MANIFEST,
        help="CSV manifest that records the rendered MIDI and WAV paths.",
    )
    parser.add_argument(
        "--soundfont",
        type=Path,
        default=None,
        help="Path to a GM soundfont (.sf2). If omitted, MXL_CLAP_SOUND_FONT is used.",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=DEFAULT_SAMPLE_RATE,
        help="Target WAV sample rate for rendering.",
    )
    parser.add_argument(
        "--fluidsynth-bin",
        type=str,
        default="fluidsynth",
        help="FluidSynth executable name or path.",
    )
    return parser


def _resolve_excerpt_path(manifest_row: pd.Series, fallback_dir: Path) -> Path:
    excerpt_path_value = manifest_row.get("excerpt_path", "")
    if isinstance(excerpt_path_value, str) and excerpt_path_value:
        return Path(excerpt_path_value)

    excerpt_file = manifest_row.get("excerpt_file", "")
    if isinstance(excerpt_file, str) and excerpt_file:
        return fallback_dir / excerpt_file

    raise ValueError("Manifest row does not contain an excerpt_path or excerpt_file value.")


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    if not args.manifest.exists():
        raise SystemExit(f"Missing excerpt manifest: {args.manifest}")

    try:
        _resolve_fluidsynth_binary(args.fluidsynth_bin)
        resolved_soundfont = _resolve_soundfont_path(args.soundfont)
    except (FileNotFoundError, NotImplementedError) as exc:
        raise SystemExit(str(exc))

    frame = pd.read_csv(args.manifest)
    if frame.empty:
        print(f"No excerpt rows found in {args.manifest}")
        return 0

    args.midi_dir.mkdir(parents=True, exist_ok=True)
    args.audio_dir.mkdir(parents=True, exist_ok=True)

    rendered_rows: list[dict[str, object]] = []
    for _, manifest_row in frame.iterrows():
        excerpt_path = _resolve_excerpt_path(manifest_row, args.excerpt_dir)
        try:
            score = load_score_auto(excerpt_path)
        except Exception as exc:
            print(f"Skipping {excerpt_path}: {exc}")
            continue

        excerpt_id = str(manifest_row.get("excerpt_id", excerpt_path.stem))
        midi_path = args.midi_dir / f"{excerpt_id}.mid"
        audio_path = args.audio_dir / f"{excerpt_id}.wav"

        try:
            render_score_to_wav(
                score=score,
                midi_path=midi_path,
                out_path=audio_path,
                soundfont_path=resolved_soundfont,
                sample_rate=args.sample_rate,
                fluidsynth_bin=args.fluidsynth_bin,
            )
        except (FileNotFoundError, NotImplementedError, RuntimeError, ValueError) as exc:
            raise SystemExit(str(exc))
        print(f"Wrote MIDI: {midi_path}")
        print(f"Wrote WAV: {audio_path}")

        rendered_row = manifest_row.to_dict()
        rendered_row.update(
            {
                "midi_path": str(midi_path),
                "audio_path": str(audio_path),
                "sample_rate": int(args.sample_rate),
                "fluidsynth_bin": args.fluidsynth_bin,
                "soundfont_path": str(resolved_soundfont),
            }
        )
        rendered_rows.append(rendered_row)

    if rendered_rows:
        rendered_frame = pd.DataFrame(rendered_rows)
    else:
        rendered_frame = pd.DataFrame(
            columns=list(frame.columns)
            + ["midi_path", "audio_path", "sample_rate", "fluidsynth_bin", "soundfont_path"]
        )
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    rendered_frame.to_csv(args.manifest_output, index=False)
    print(f"Wrote {len(rendered_frame)} rendered rows to {args.manifest_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
