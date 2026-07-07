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
from score_embedding_lab.llm_explanations import make_comparison_table_for_llm, make_pair_explanation_prompt


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a Markdown prompt table for LLM review.")
    parser.add_argument(
        "--pairwise",
        type=Path,
        default=DATA_PROCESSED / "pairwise_similarity.csv",
        help="Pairwise similarity CSV produced by compare_excerpts.py",
    )
    parser.add_argument(
        "--features",
        type=Path,
        default=DATA_PROCESSED / "symbolic_features.csv",
        help="Feature CSV produced by extract_symbolic_features.py",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPORTS_DIR / "llm_prompt_table.md",
        help="Markdown report path.",
    )
    parser.add_argument("--max-examples", type=int, default=3, help="Number of pair prompts to include as examples.")
    return parser


def _feature_summary(row: pd.Series) -> dict:
    keys = [
        "note_count",
        "total_duration_quarter_lengths",
        "note_density",
        "ambitus_semitones",
        "mean_pitch",
        "rhythmic_diversity",
        "chordified_chord_count",
    ]
    summary = {}
    for key in keys:
        if key in row and pd.notna(row[key]):
            summary[key] = row[key]
    return summary


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    if not args.pairwise.exists():
        raise SystemExit(f"Missing pairwise CSV: {args.pairwise}")

    pairwise = pd.read_csv(args.pairwise)
    features = pd.read_csv(args.features) if args.features.exists() else pd.DataFrame()

    feature_lookup = {}
    if not features.empty and "excerpt_id" in features.columns:
        feature_lookup = {str(row["excerpt_id"]): row for _, row in features.iterrows()}

    table = make_comparison_table_for_llm(pairwise)
    selected = pairwise.sort_values("embedding_similarity", ascending=False).head(args.max_examples) if not pairwise.empty else pairwise

    lines = [
        "# LLM Prompt Table",
        "",
        "Use the table below to judge whether the embedding similarity seems musicologically plausible.",
        "Treat the comparison as exploratory rather than definitive.",
        "",
        "## Pairwise Summary",
        "",
        table,
        "",
    ]

    if not selected.empty:
        lines.extend(["## Example Pair Prompts", ""])
        for _, row in selected.iterrows():
            a = str(row.get("excerpt_a", ""))
            b = str(row.get("excerpt_b", ""))
            prompt = make_pair_explanation_prompt(
                row,
                _feature_summary(feature_lookup.get(a, pd.Series(dtype=float))),
                _feature_summary(feature_lookup.get(b, pd.Series(dtype=float))),
            )
            lines.extend([f"### {a} vs {b}", "", "```text", prompt, "```", ""])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote LLM prompt table to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
