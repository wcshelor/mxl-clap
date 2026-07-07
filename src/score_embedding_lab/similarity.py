from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from .feature_registry import CORE_GLOBAL_PREFIXES, SIMILARITY_FAMILY_PREFIXES


FEATURE_FAMILIES = SIMILARITY_FAMILY_PREFIXES

LEGACY_PITCH_COLUMNS = (
    "note_count",
    "ambitus_semitones",
    "pitch_range_semitones",
    "mean_pitch",
    "pitch_class_",
    "interval_",
)
LEGACY_RHYTHM_COLUMNS = (
    "total_duration_quarter_lengths",
    "note_density",
    "rhythmic_diversity",
    "duration_bin_",
)
LEGACY_TEXTURE_COLUMNS = (
    "chordified_chord_count",
)
LEGACY_HARMONY_COLUMNS = (
    "chordified_chord_count",
)
LEGACY_METADATA_COLUMNS = (
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
)


def cosine_similarity_matrix(vectors) -> np.ndarray:
    """Compute a cosine similarity matrix."""
    array = np.asarray(vectors, dtype=float)
    if array.ndim == 1:
        array = array.reshape(1, -1)
    if array.shape[0] == 0:
        return np.zeros((0, 0), dtype=float)
    if array.shape[1] == 0:
        return np.zeros((array.shape[0], array.shape[0]), dtype=float)

    norms = np.linalg.norm(array, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    normalized = array / norms
    return normalized @ normalized.T


def _is_numeric_series(series: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(series)


def _prefix_tuple(value: str | Sequence[str] | None) -> tuple[str, ...] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return (value,)
    return tuple(value)


def _column_starts_with_any(column: str, prefixes: tuple[str, ...] | None) -> bool:
    if prefixes is None:
        return True
    return any(column.startswith(prefix) for prefix in prefixes)


def numeric_feature_columns(
    df: pd.DataFrame,
    ignore_columns: Iterable[str] | None = None,
    include_prefixes: Sequence[str] | str | None = None,
) -> list[str]:
    ignore = set(ignore_columns) if ignore_columns is not None else set()
    prefixes = _prefix_tuple(include_prefixes)
    numeric_columns = [
        column
        for column in df.columns
        if column not in ignore and _is_numeric_series(df[column]) and _column_starts_with_any(column, prefixes)
    ]
    return numeric_columns


def feature_dataframe_to_matrix(
    df: pd.DataFrame,
    ignore_columns: Iterable[str] | None,
    include_prefixes: Sequence[str] | str | None = None,
    columns: Sequence[str] | None = None,
):
    """Select numeric columns from a dataframe and return a matrix plus the column names."""
    selected = df.drop(columns=[column for column in (ignore_columns or []) if column in df.columns], errors="ignore")
    numeric = selected.select_dtypes(include=["number"]).fillna(0.0)

    if columns is not None:
        ordered_columns = [column for column in columns if column in numeric.columns]
        numeric = numeric.loc[:, ordered_columns]
    else:
        prefixes = _prefix_tuple(include_prefixes)
        if prefixes is not None:
            ordered_columns = [column for column in numeric.columns if _column_starts_with_any(column, prefixes)]
            numeric = numeric.loc[:, ordered_columns]

    return numeric.to_numpy(dtype=float), list(numeric.columns)


def feature_columns_for_families(df: pd.DataFrame, ignore_columns: Iterable[str] | None = None) -> dict[str, list[str]]:
    prefixes_present = any(
        column.startswith(prefix)
        for column in df.columns
        for prefixes in FEATURE_FAMILIES.values()
        for prefix in prefixes
    )

    if prefixes_present:
        return {
            family_name: numeric_feature_columns(df, ignore_columns=ignore_columns, include_prefixes=prefixes)
            for family_name, prefixes in FEATURE_FAMILIES.items()
        }

    return {
        "pitch_similarity": [column for column in numeric_feature_columns(df, ignore_columns=ignore_columns) if _matches_legacy_family(column, LEGACY_PITCH_COLUMNS)],
        "rhythm_similarity": [column for column in numeric_feature_columns(df, ignore_columns=ignore_columns) if _matches_legacy_family(column, LEGACY_RHYTHM_COLUMNS)],
        "texture_similarity": [column for column in numeric_feature_columns(df, ignore_columns=ignore_columns) if _matches_legacy_family(column, LEGACY_TEXTURE_COLUMNS)],
        "harmony_similarity": [column for column in numeric_feature_columns(df, ignore_columns=ignore_columns) if _matches_legacy_family(column, LEGACY_HARMONY_COLUMNS)],
    }


def _matches_legacy_family(column: str, prefixes: Sequence[str]) -> bool:
    return any(column.startswith(prefix) for prefix in prefixes)


def global_feature_columns(df: pd.DataFrame, ignore_columns: Iterable[str] | None = None) -> list[str]:
    family_columns = feature_columns_for_families(df, ignore_columns=ignore_columns)
    prefixed_columns = [
        column
        for column in numeric_feature_columns(df, ignore_columns=ignore_columns)
        if column.startswith(CORE_GLOBAL_PREFIXES)
    ]
    if prefixed_columns:
        return prefixed_columns

    return [
        column
        for column in numeric_feature_columns(df, ignore_columns=ignore_columns)
        if not _matches_legacy_family(column, LEGACY_METADATA_COLUMNS)
    ]


def pairwise_similarity_table(
    ids,
    symbolic_similarity,
    embedding_similarity,
    extra_similarity_matrices: Mapping[str, np.ndarray] | None = None,
) -> pd.DataFrame:
    """Build a long-form pairwise similarity table from one or more similarity matrices."""
    ids = list(ids)
    symbolic_similarity = np.asarray(symbolic_similarity, dtype=float)
    embedding_similarity = np.asarray(embedding_similarity, dtype=float)
    extra_similarity_matrices = {
        name: np.asarray(matrix, dtype=float)
        for name, matrix in (extra_similarity_matrices or {}).items()
    }
    n = len(ids)
    records = []

    for i in range(n):
        for j in range(i + 1, n):
            record = {
                "excerpt_a": ids[i],
                "excerpt_b": ids[j],
                "pair_id": f"{ids[i]}__{ids[j]}",
                "symbolic_similarity": float(symbolic_similarity[i, j]) if symbolic_similarity.size else 0.0,
                "embedding_similarity": float(embedding_similarity[i, j]) if embedding_similarity.size else 0.0,
                "similarity_gap": (
                    float(embedding_similarity[i, j]) if embedding_similarity.size else 0.0
                )
                - (
                    float(symbolic_similarity[i, j]) if symbolic_similarity.size else 0.0
                ),
                "similarity_mean": (
                    (
                        float(embedding_similarity[i, j]) if embedding_similarity.size else 0.0
                    )
                    + (
                        float(symbolic_similarity[i, j]) if symbolic_similarity.size else 0.0
                    )
                )
                / 2.0,
            }
            for name, matrix in extra_similarity_matrices.items():
                record[name] = float(matrix[i, j]) if matrix.size else 0.0
            records.append(record)

    columns = [
        "excerpt_a",
        "excerpt_b",
        "pair_id",
        "symbolic_similarity",
        "embedding_similarity",
        "similarity_gap",
        "similarity_mean",
        *extra_similarity_matrices.keys(),
    ]
    return pd.DataFrame.from_records(records, columns=columns)
