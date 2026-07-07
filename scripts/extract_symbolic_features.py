from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from score_embedding_lab.config import DATA_PROCESSED, DATA_RAW_EXCERPTS
from score_embedding_lab.feature_pipeline import build_excerpt_feature_frame, load_excerpt_feature_rows


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract simple symbolic features from MusicXML excerpts.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DATA_PROCESSED / "excerpt_manifest.csv",
        help="Excerpt manifest produced by scripts/extract_excerpts.py.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DATA_RAW_EXCERPTS / "generated",
        help="Fallback directory containing MusicXML/MXL excerpt files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_PROCESSED / "symbolic_features.csv",
        help="CSV path for extracted features.",
    )
    parser.add_argument(
        "--feature-sets",
        type=str,
        default="core",
        help="Comma-separated feature sets to enable. Default: core only.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    rows = load_excerpt_feature_rows(args.manifest, input_dir=args.input_dir, feature_sets=args.feature_sets)
    frame = build_excerpt_feature_frame(rows)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False)
    print(f"Wrote {len(frame)} excerpt rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
