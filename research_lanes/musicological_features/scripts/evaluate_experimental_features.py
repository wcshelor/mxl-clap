from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from score_embedding_lab.experimental_feature_evaluation import build_experimental_feature_report


LANE_ROOT = ROOT / "research_lanes" / "musicological_features"
LANE_REPORTS_DIR = LANE_ROOT / "reports"
DEFAULT_FEATURES = LANE_REPORTS_DIR / "mozart_chopin_experimental_features.csv"
DEFAULT_PAIRWISE = LANE_REPORTS_DIR / "mozart_chopin_experimental_features_pairwise.csv"
DEFAULT_METADATA = LANE_ROOT / "feature_metadata" / "experimental_features_v0.yml"


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate the experimental musicological feature lane.")
    parser.add_argument("--features", type=Path, default=DEFAULT_FEATURES, help="Experimental feature CSV.")
    parser.add_argument(
        "--pairwise",
        type=Path,
        default=DEFAULT_PAIRWISE,
        help="Pairwise similarity CSV produced by the research lane.",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=DEFAULT_METADATA,
        help="Feature metadata YAML for the experimental lane.",
    )
    parser.add_argument(
        "--output-audit",
        type=Path,
        default=LANE_REPORTS_DIR / "feature_audit.csv",
        help="CSV output for the experimental feature audit.",
    )
    parser.add_argument(
        "--output-correlations",
        type=Path,
        default=LANE_REPORTS_DIR / "feature_embedding_correlations.csv",
        help="CSV output for feature-to-embedding correlations.",
    )
    parser.add_argument(
        "--output-family-summary",
        type=Path,
        default=LANE_REPORTS_DIR / "family_summary.csv",
        help="CSV output for the family-level summary.",
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        default=LANE_REPORTS_DIR / "mozart_chopin_experimental_features_report.md",
        help="Markdown report output for the evaluation summary.",
    )
    parser.add_argument(
        "--feature-sets",
        type=str,
        default="core",
        help="Comma-separated feature sets used for the run. Recorded in the report only.",
    )
    parser.add_argument("--cv-threshold", type=float, default=0.05, help="Coefficient of variation threshold for the audit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    if not args.features.exists():
        raise SystemExit(f"Missing feature CSV: {args.features}")

    features = pd.read_csv(args.features)
    pairwise = pd.read_csv(args.pairwise) if args.pairwise.exists() else None

    result, report = build_experimental_feature_report(
        features_frame=features,
        pairwise_frame=pairwise,
        metadata_path=args.metadata,
        feature_sets=args.feature_sets,
        cv_threshold=args.cv_threshold,
    )

    args.output_audit.parent.mkdir(parents=True, exist_ok=True)
    result.audit_frame.to_csv(args.output_audit, index=False)
    args.output_correlations.parent.mkdir(parents=True, exist_ok=True)
    result.correlations_frame.to_csv(args.output_correlations, index=False)
    args.output_family_summary.parent.mkdir(parents=True, exist_ok=True)
    result.family_summary_frame.to_csv(args.output_family_summary, index=False)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(report, encoding="utf-8")

    print(f"Wrote experimental feature audit to {args.output_audit}")
    print(f"Wrote feature-to-embedding correlations to {args.output_correlations}")
    print(f"Wrote family summary to {args.output_family_summary}")
    print(f"Wrote experimental feature report to {args.report_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
