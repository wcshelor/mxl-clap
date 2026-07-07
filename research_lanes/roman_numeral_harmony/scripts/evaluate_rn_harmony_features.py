from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from score_embedding_lab.roman_numeral_harmony.evaluation import (
    feature_audit_frame,
    feature_embedding_correlations,
    family_summary_frame,
    ranked_feature_candidates,
)


LANE_ROOT = ROOT / "research_lanes" / "roman_numeral_harmony"
DEFAULT_METADATA = LANE_ROOT / "feature_metadata" / "experimental_rn_harmony_features_v0.yml"


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate Roman numeral harmony features.")
    parser.add_argument("--features", type=Path, required=True, help="Feature table CSV produced by the lane runner.")
    parser.add_argument("--pairwise", type=Path, default=None, help="Optional pairwise similarity CSV.")
    parser.add_argument("--clap-pairwise", type=Path, default=None, help="Optional CLAP pairwise similarity CSV.")
    parser.add_argument("--symbolic-pairwise", type=Path, default=None, help="Optional core symbolic pairwise similarity CSV.")
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA, help="Feature metadata YAML.")
    parser.add_argument("--output-dir", type=Path, default=LANE_ROOT / "reports", help="Output directory for evaluation tables.")
    return parser


def _read_optional(path: Path | None) -> pd.DataFrame | None:
    if path is None or not path.exists():
        return None
    return pd.read_csv(path)


def _load_metadata(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _merge_pairwise_tables(base: pd.DataFrame, clap: pd.DataFrame | None, symbolic: pd.DataFrame | None) -> pd.DataFrame:
    frame = base.copy()
    for extra, suffix in ((clap, "clap"), (symbolic, "symbolic")):
        if extra is None or extra.empty:
            continue
        join_frame = extra.copy()
        if "pair_id" not in join_frame.columns and {"score_a", "score_b"}.issubset(join_frame.columns):
            join_frame["pair_id"] = join_frame["score_a"].astype(str) + "__" + join_frame["score_b"].astype(str)
        columns = [column for column in join_frame.columns if column.endswith("_similarity") or column == "pair_id" or column.startswith("experimental_")]
        frame = frame.merge(join_frame[columns], on="pair_id", how="left", suffixes=("", f"_{suffix}"))
    return frame


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    features = pd.read_csv(args.features)
    pairwise = pd.read_csv(args.pairwise) if args.pairwise and args.pairwise.exists() else None
    clap = _read_optional(args.clap_pairwise)
    symbolic = _read_optional(args.symbolic_pairwise)
    metadata = _load_metadata(args.metadata)

    audit = feature_audit_frame(features)
    family = family_summary_frame(features)
    correlations = feature_embedding_correlations(features, pairwise)
    ranked = ranked_feature_candidates(audit, correlations)

    if pairwise is not None and not pairwise.empty:
        pairwise = _merge_pairwise_tables(pairwise, clap, symbolic)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    audit_output = args.output_dir / "feature_audit.csv"
    family_output = args.output_dir / "family_summary.csv"
    correlations_output = args.output_dir / "feature_embedding_correlations.csv"
    ranked_output = args.output_dir / "ranked_feature_candidates.csv"
    audit.to_csv(audit_output, index=False)
    family.to_csv(family_output, index=False)
    correlations.to_csv(correlations_output, index=False)
    ranked.to_csv(ranked_output, index=False)
    if pairwise is not None and not pairwise.empty:
        pairwise_output = args.output_dir / "pairwise_with_external_similarity.csv"
        pairwise.to_csv(pairwise_output, index=False)

    report = [
        "# Roman Numeral Harmony Evaluation",
        "",
        f"- Feature rows: `{len(features)}`",
        f"- Feature count: `{len([c for c in features.columns if c.startswith('experimental__')])}`",
        f"- Metadata entries: `{len(metadata)}`",
        "",
        "## Outputs",
        f"- Feature audit: `{audit_output}`",
        f"- Family summary: `{family_output}`",
        f"- Feature correlations: `{correlations_output}`",
        f"- Ranked candidates: `{ranked_output}`",
    ]
    report_output = args.output_dir / "rn_harmony_evaluation_report.md"
    report_output.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote {report_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
