from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from score_embedding_lab.config import DATA_PROCESSED, REPORTS_DIR
from score_embedding_lab.feature_audit import audit_numeric_features, build_audit_summary_markdown


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit numeric symbolic features in a CSV.")
    parser.add_argument(
        "--input",
        type=Path,
        default=DATA_PROCESSED / "symbolic_features.csv",
        help="Symbolic feature CSV to audit.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=REPORTS_DIR / "symbolic_feature_audit.csv",
        help="CSV output for the feature audit.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=REPORTS_DIR / "symbolic_feature_audit.md",
        help="Markdown summary output for the feature audit.",
    )
    parser.add_argument("--cv-threshold", type=float, default=0.05, help="Coefficient of variation threshold for near-constant features.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    if not args.input.exists():
        raise SystemExit(f"Missing symbolic feature CSV: {args.input}")

    frame = pd.read_csv(args.input)
    audit_frame = audit_numeric_features(frame, cv_threshold=args.cv_threshold)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    audit_frame.to_csv(args.output_csv, index=False)
    summary = build_audit_summary_markdown(audit_frame, args.input, cv_threshold=args.cv_threshold)
    args.output_md.write_text(summary, encoding="utf-8")

    print(f"Wrote symbolic feature audit to {args.output_csv}")
    print(f"Wrote symbolic feature audit summary to {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
