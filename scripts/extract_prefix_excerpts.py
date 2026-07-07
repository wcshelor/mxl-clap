from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from score_embedding_lab.config import DATA_PROCESSED, DATA_RAW_FULL_PIECES, DATA_RAW_PREFIX_EXCERPTS
from score_embedding_lab.excerpting import extract_prefix_excerpts_from_directory


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Slice full MusicXML pieces into prefix excerpts.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DATA_RAW_FULL_PIECES,
        help="Directory containing full MusicXML/MXL source pieces.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DATA_RAW_PREFIX_EXCERPTS,
        help="Directory where generated prefix excerpt files will be written.",
    )
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=DATA_PROCESSED / "prefix_excerpt_manifest.csv",
        help="CSV manifest describing the generated prefix excerpts.",
    )
    parser.add_argument(
        "--prefix-lengths",
        type=int,
        nargs="+",
        default=[32, 64],
        help="Measure endpoints to extract from the start of each piece.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    frame = extract_prefix_excerpts_from_directory(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        prefix_lengths=args.prefix_lengths,
    )

    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.manifest_output, index=False)
    print(f"Wrote {len(frame)} prefix excerpt rows to {args.manifest_output}")
    print(f"Generated prefix excerpt files in {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
