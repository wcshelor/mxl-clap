from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from score_embedding_lab.config import DATA_PROCESSED
from score_embedding_lab.embedding_alignment import reorder_embeddings_by_excerpt_id
from score_embedding_lab.similarity import (
    FEATURE_FAMILIES,
    cosine_similarity_matrix,
    feature_columns_for_families,
    feature_dataframe_to_matrix,
    global_feature_columns,
    pairwise_similarity_table,
)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare symbolic and embedding similarity for excerpt pairs.")
    parser.add_argument(
        "--features",
        type=Path,
        default=DATA_PROCESSED / "symbolic_features.csv",
        help="CSV produced by extract_symbolic_features.py",
    )
    parser.add_argument(
        "--embeddings",
        type=Path,
        default=DATA_PROCESSED / "audio_embeddings.npy",
        help="NPY produced by compute_embeddings.py",
    )
    parser.add_argument(
        "--embedding-metadata",
        type=Path,
        default=DATA_PROCESSED / "audio_embeddings_metadata.csv",
        help="Embedding metadata CSV produced by compute_embeddings.py",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_PROCESSED / "pairwise_similarity.csv",
        help="CSV output for pairwise similarity results.",
    )
    return parser


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
    if not args.features.exists():
        raise SystemExit(f"Missing features CSV: {args.features}")
    if not args.embeddings.exists():
        raise SystemExit(f"Missing embeddings NPY: {args.embeddings}")

    features = pd.read_csv(args.features)
    embeddings = np.load(args.embeddings)
    metadata = pd.read_csv(args.embedding_metadata) if args.embedding_metadata.exists() else None

    ignore_columns = [
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
    global_columns = global_feature_columns(features, ignore_columns=ignore_columns)
    feature_matrix, feature_columns = feature_dataframe_to_matrix(features, ignore_columns=ignore_columns, columns=global_columns)
    ordered_embeddings = reorder_embeddings_by_excerpt_id(features, np.asarray(embeddings, dtype=float), metadata)

    symbolic_similarity = cosine_similarity_matrix(feature_matrix)
    embedding_similarity = cosine_similarity_matrix(ordered_embeddings)
    family_columns = feature_columns_for_families(features, ignore_columns=ignore_columns)
    extra_similarity_matrices = {
        "symbolic_global_similarity": symbolic_similarity,
        "symbolic_core_similarity": symbolic_similarity,
    }
    for column_name, family_prefixes in FEATURE_FAMILIES.items():
        family_key = column_name
        columns = family_columns.get(family_key, [])
        if not columns:
            continue
        family_matrix, _ = feature_dataframe_to_matrix(features, ignore_columns=ignore_columns, columns=columns)
        extra_similarity_matrices[column_name] = cosine_similarity_matrix(family_matrix)

    ids = features["excerpt_id"].astype(str).tolist() if "excerpt_id" in features.columns else list(range(len(features)))
    pairwise = pairwise_similarity_table(
        ids,
        symbolic_similarity,
        embedding_similarity,
        extra_similarity_matrices=extra_similarity_matrices,
    )
    pairwise = _add_metadata_columns(pairwise, features)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    pairwise.to_csv(args.output, index=False)
    print(f"Wrote {len(pairwise)} pair rows to {args.output}")
    print(f"Symbolic global feature columns used: {', '.join(feature_columns) if feature_columns else '(none)'}")
    for family_name, columns in family_columns.items():
        print(f"{family_name} columns used: {', '.join(columns) if columns else '(none)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
