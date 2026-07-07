from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from score_embedding_lab.config import DATA_PROCESSED, DATA_RAW_FULL_PIECES, DATA_RAW_EXCERPTS_GENERATED
from score_embedding_lab.excerpting import extract_excerpts_from_directory


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Slice full MusicXML pieces into deterministic measure excerpts.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DATA_RAW_FULL_PIECES,
        help="Directory containing full MusicXML/MXL source pieces.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DATA_RAW_EXCERPTS_GENERATED,
        help="Directory where generated excerpt files will be written.",
    )
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=DATA_PROCESSED / "excerpt_manifest.csv",
        help="CSV manifest describing the generated excerpts.",
    )
    parser.add_argument("--window-size", type=int, default=4, help="Measure window size for each excerpt.")
    parser.add_argument("--stride", type=int, default=4, help="Measure stride between excerpt starts.")
    parser.add_argument(
        "--include-partial-final",
        action="store_true",
        help="Emit a trailing shorter excerpt when the final window does not fill the full window size.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    frame = extract_excerpts_from_directory(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        window_size=args.window_size,
        stride=args.stride,
        include_partial_final=args.include_partial_final,
    )

    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.manifest_output, index=False)
    print(f"Wrote {len(frame)} excerpt rows to {args.manifest_output}")
    print(f"Generated excerpt files in {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
