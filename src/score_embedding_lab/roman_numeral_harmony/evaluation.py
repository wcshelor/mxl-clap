from __future__ import annotations

from collections import Counter, defaultdict
from math import sqrt
from statistics import mean
from typing import Iterable

import numpy as np
import pandas as pd


def _safe_corr(a: pd.Series, b: pd.Series) -> float:
    joined = pd.concat([a, b], axis=1).dropna()
    if len(joined) < 2:
        return 0.0
    x = joined.iloc[:, 0].astype(float).to_numpy()
    y = joined.iloc[:, 1].astype(float).to_numpy()
    if np.std(x) == 0 or np.std(y) == 0:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def feature_audit_frame(features: pd.DataFrame, *, feature_prefix: str = "experimental__rn_harmony__") -> pd.DataFrame:
    rows = []
    numeric = features.select_dtypes(include=["number"])
    for column in numeric.columns:
        if not column.startswith(feature_prefix) and not column.startswith("experimental__harmony_texture__") and not column.startswith("experimental__harmony_melody__"):
            continue
        series = numeric[column]
        values = series.dropna().astype(float)
        mean_value = float(values.mean()) if not values.empty else 0.0
        std_value = float(values.std(ddof=0)) if len(values) > 1 else 0.0
        cv = float(abs(std_value / mean_value)) if mean_value not in (0.0, -0.0) else 0.0
        rows.append(
            {
                "feature": column,
                "min": float(values.min()) if not values.empty else 0.0,
                "max": float(values.max()) if not values.empty else 0.0,
                "mean": mean_value,
                "std": std_value,
                "unique_count": int(values.nunique(dropna=True)),
                "coefficient_of_variation": cv,
                "near_constant": bool(values.nunique(dropna=True) <= 1 or cv < 0.05),
                "missing_count": int(series.isna().sum()),
            }
        )
    return pd.DataFrame(rows)


def feature_embedding_correlations(
    features: pd.DataFrame,
    pairwise: pd.DataFrame | None,
    *,
    feature_prefixes: Iterable[str] = ("experimental__rn_harmony__", "experimental__harmony_texture__", "experimental__harmony_melody__"),
) -> pd.DataFrame:
    rows = []
    if pairwise is not None and not pairwise.empty:
        similarity_columns = [
            column
            for column in pairwise.columns
            if column in {
                "experimental_rn_harmony_similarity",
                "experimental_harmony_texture_similarity",
                "experimental_harmony_melody_similarity",
                "experimental_rn_all_similarity",
            }
        ]
        for column in similarity_columns:
            row = {"feature": column}
            for target in ("clap_similarity", "symbolic_similarity", "similarity_gap"):
                row[f"correlation_with_{target}"] = _safe_corr(pairwise[column], pairwise[target]) if target in pairwise.columns else 0.0
            rows.append(row)
        if rows:
            return pd.DataFrame(rows)

    if "composer" in features.columns:
        composers = features["composer"].dropna().astype(str)
        if composers.nunique() == 2:
            label = composers.map({name: index for index, name in enumerate(sorted(composers.unique()))})
            for column in features.columns:
                if not any(str(column).startswith(prefix) for prefix in feature_prefixes):
                    continue
                if not pd.api.types.is_numeric_dtype(features[column]):
                    continue
                rows.append(
                    {
                        "feature": column,
                        "correlation_with_composer_label": _safe_corr(features[column], label),
                    }
                )
    return pd.DataFrame(rows)


def family_summary_frame(features: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for family in ("experimental__rn_harmony__", "experimental__harmony_texture__", "experimental__harmony_melody__"):
        columns = [column for column in features.columns if column.startswith(family)]
        if not columns:
            continue
        rows.append(
            {
                "family": family.rstrip("_"),
                "feature_count": len(columns),
                "mean_feature_value": float(features[columns].mean(numeric_only=True).mean()) if columns else 0.0,
            }
        )
    return pd.DataFrame(rows)


def ranked_feature_candidates(audit: pd.DataFrame, correlations: pd.DataFrame | None = None) -> pd.DataFrame:
    frame = audit.copy()
    if frame.empty:
        return frame
    frame = frame.sort_values(by=["near_constant", "coefficient_of_variation", "std"], ascending=[True, False, False])
    frame.insert(0, "rank", range(1, len(frame) + 1))
    return frame
