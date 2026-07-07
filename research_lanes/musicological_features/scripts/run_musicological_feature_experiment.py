from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from score_embedding_lab.config import DATA_PROCESSED, DATA_RAW_PREFIX_EXCERPTS
from score_embedding_lab.embedding_alignment import reorder_embeddings_by_excerpt_id
from score_embedding_lab.experimental_feature_evaluation import build_experimental_feature_report
from score_embedding_lab.feature_pipeline import build_excerpt_feature_frame, load_excerpt_feature_rows
from score_embedding_lab.similarity import (
    cosine_similarity_matrix,
    feature_columns_for_families,
    feature_dataframe_to_matrix,
    global_feature_columns,
    pairwise_similarity_table,
)


LANE_ROOT = ROOT / "research_lanes" / "musicological_features"
LANE_REPORTS_DIR = LANE_ROOT / "reports"
DEFAULT_FEATURE_SET = "core"
DEFAULT_FEATURES_OUTPUT = LANE_REPORTS_DIR / "mozart_chopin_experimental_features.csv"
DEFAULT_PAIRWISE_OUTPUT = LANE_REPORTS_DIR / "mozart_chopin_experimental_features_pairwise.csv"
DEFAULT_REPORT_OUTPUT = LANE_REPORTS_DIR / "mozart_chopin_experimental_features_report.md"
DEFAULT_AUDIT_OUTPUT = LANE_REPORTS_DIR / "feature_audit.csv"
DEFAULT_CORRELATIONS_OUTPUT = LANE_REPORTS_DIR / "feature_embedding_correlations.csv"
DEFAULT_FAMILY_SUMMARY_OUTPUT = LANE_REPORTS_DIR / "family_summary.csv"
DEFAULT_METADATA = LANE_ROOT / "feature_metadata" / "experimental_features_v0.yml"


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the experimental musicological feature lane.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DATA_PROCESSED / "prefix_excerpt_manifest.csv",
        help="Prefix excerpt manifest produced by scripts/extract_prefix_excerpts.py.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DATA_RAW_PREFIX_EXCERPTS,
        help="Fallback directory containing prefix MusicXML/MXL excerpt files.",
    )
    parser.add_argument(
        "--feature-sets",
        type=str,
        default=DEFAULT_FEATURE_SET,
        help="Comma-separated feature sets. Default is core-only.",
    )
    parser.add_argument(
        "--features-output",
        type=Path,
        default=DEFAULT_FEATURES_OUTPUT,
        help="CSV output for the extracted feature table.",
    )
    parser.add_argument(
        "--pairwise-output",
        type=Path,
        default=DEFAULT_PAIRWISE_OUTPUT,
        help="CSV output for the pairwise similarity table.",
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        default=DEFAULT_REPORT_OUTPUT,
        help="Markdown output for the experiment summary.",
    )
    parser.add_argument(
        "--audit-output",
        type=Path,
        default=DEFAULT_AUDIT_OUTPUT,
        help="CSV output for the feature audit table.",
    )
    parser.add_argument(
        "--correlations-output",
        type=Path,
        default=DEFAULT_CORRELATIONS_OUTPUT,
        help="CSV output for feature-to-embedding correlations.",
    )
    parser.add_argument(
        "--family-summary-output",
        type=Path,
        default=DEFAULT_FAMILY_SUMMARY_OUTPUT,
        help="CSV output for the family-level summary.",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=DEFAULT_METADATA,
        help="Experimental feature metadata YAML used by the evaluation report.",
    )
    parser.add_argument(
        "--embeddings",
        type=Path,
        default=DATA_PROCESSED / "audio_embeddings.npy",
        help="Embedding matrix produced by scripts/compute_embeddings.py.",
    )
    parser.add_argument(
        "--embedding-metadata",
        type=Path,
        default=DATA_PROCESSED / "audio_embeddings_metadata.csv",
        help="Embedding metadata CSV produced by scripts/compute_embeddings.py.",
    )
    parser.add_argument("--cv-threshold", type=float, default=0.05, help="Coefficient of variation threshold for the feature audit.")
    return parser


def _set_if_blank(row: dict, key: str, value) -> None:
    current = row.get(key)
    if key not in row or pd.isna(current) or current == "":
        row[key] = value


def _ignore_columns() -> list[str]:
    return [
        "source_id",
        "source_file",
        "source_path",
        "source_total_measures",
        "measure_start",
        "measure_end",
        "requested_measure_end",
        "window_size",
        "stride",
        "excerpt_id",
        "excerpt_file",
        "excerpt_path",
        "title",
        "composer",
        "midi_path",
        "audio_path",
        "sample_rate",
        "fluidsynth_bin",
        "soundfont_path",
        "embedding_backend",
        "embedding_source_path",
        "embedding_dim",
        "audio_file",
        "filename",
    ]


def _add_metadata_columns(pairwise: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    if pairwise.empty or "excerpt_id" not in features.columns:
        return pairwise

    lookup = features.assign(excerpt_id=features["excerpt_id"].astype(str)).set_index("excerpt_id")

    def _value_for(excerpt_id: str, column: str) -> str:
        if excerpt_id not in lookup.index or column not in lookup.columns:
            return ""
        value = lookup.at[excerpt_id, column]
        return "" if pd.isna(value) else str(value)

    for suffix in ("a", "b"):
        pairwise[f"title_{suffix}"] = pairwise[f"excerpt_{suffix}"].astype(str).map(lambda excerpt_id: _value_for(excerpt_id, "title"))
        pairwise[f"composer_{suffix}"] = pairwise[f"excerpt_{suffix}"].astype(str).map(lambda excerpt_id: _value_for(excerpt_id, "composer"))
    return pairwise


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    rows = load_excerpt_feature_rows(args.manifest, input_dir=args.input_dir, feature_sets=args.feature_sets)
    features = build_excerpt_feature_frame(rows)

    if features.empty:
        raise SystemExit("No excerpt features were loaded. Check the manifest or input directory.")

    args.features_output.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(args.features_output, index=False)

    ignore_columns = _ignore_columns()
    global_columns = global_feature_columns(features, ignore_columns=ignore_columns)
    feature_matrix, feature_columns = feature_dataframe_to_matrix(features, ignore_columns=ignore_columns, columns=global_columns)

    embeddings_available = args.embeddings.exists()
    if embeddings_available:
        embeddings = np.load(args.embeddings)
        metadata = pd.read_csv(args.embedding_metadata) if args.embedding_metadata.exists() else None
        ordered_embeddings = reorder_embeddings_by_excerpt_id(features, np.asarray(embeddings, dtype=float), metadata)
    else:
        ordered_embeddings = np.zeros((len(features), 0), dtype=float)

    symbolic_similarity = cosine_similarity_matrix(feature_matrix)
    embedding_similarity = cosine_similarity_matrix(ordered_embeddings)
    family_columns = feature_columns_for_families(features, ignore_columns=ignore_columns)
    extra_similarity_matrices = {
        "symbolic_global_similarity": symbolic_similarity,
        "symbolic_core_similarity": symbolic_similarity,
    }
    for family_name, columns in family_columns.items():
        if not columns:
            continue
        family_matrix, _ = feature_dataframe_to_matrix(features, ignore_columns=ignore_columns, columns=columns)
        extra_similarity_matrices[family_name] = cosine_similarity_matrix(family_matrix)

    ids = features["excerpt_id"].astype(str).tolist() if "excerpt_id" in features.columns else list(range(len(features)))
    pairwise = pairwise_similarity_table(
        ids,
        symbolic_similarity,
        embedding_similarity,
        extra_similarity_matrices=extra_similarity_matrices,
    )
    pairwise = _add_metadata_columns(pairwise, features)

    args.pairwise_output.parent.mkdir(parents=True, exist_ok=True)
    pairwise.to_csv(args.pairwise_output, index=False)

    evaluation_result, report = build_experimental_feature_report(
        features_frame=features,
        pairwise_frame=pairwise,
        metadata_path=args.metadata,
        feature_sets=args.feature_sets,
        cv_threshold=args.cv_threshold,
    )

    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    evaluation_result.audit_frame.to_csv(args.audit_output, index=False)
    evaluation_result.correlations_frame.to_csv(args.correlations_output, index=False)
    evaluation_result.family_summary_frame.to_csv(args.family_summary_output, index=False)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(report, encoding="utf-8")

    print(f"Wrote feature table to {args.features_output}")
    print(f"Wrote feature audit to {args.audit_output}")
    print(f"Wrote feature correlations to {args.correlations_output}")
    print(f"Wrote family summary to {args.family_summary_output}")
    print(f"Wrote pairwise table to {args.pairwise_output}")
    print(f"Wrote report to {args.report_output}")
    print(f"Symbolic core columns used: {', '.join(feature_columns) if feature_columns else '(none)'}")
    for family_name, columns in family_columns.items():
        print(f"{family_name} columns used: {', '.join(columns) if columns else '(none)'}")
    if not embeddings_available:
        print("Embedding matrix not found; pairwise embedding similarity was computed from an empty placeholder matrix.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
