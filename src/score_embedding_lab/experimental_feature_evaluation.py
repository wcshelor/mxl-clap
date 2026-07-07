from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .feature_audit import audit_numeric_features
from .feature_registry import EXPERIMENTAL_FEATURE_METADATA, feature_family_for_column


@dataclass(slots=True)
class ExperimentalFeatureEvaluationResult:
    audit_frame: pd.DataFrame
    correlations_frame: pd.DataFrame
    family_summary_frame: pd.DataFrame
    metadata_frame: pd.DataFrame


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows available._"

    columns = list(frame.columns)
    rows = frame.fillna("").astype(str).to_dict(orient="records")
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(row.get(column, "") for column in columns) + " |" for row in rows]
    return "\n".join([header, separator, *body])


def _safe_corr(left: pd.Series, right: pd.Series) -> float:
    subset = pd.concat([left, right], axis=1).dropna()
    if len(subset) < 2:
        return float("nan")
    if subset.iloc[:, 0].nunique() <= 1 or subset.iloc[:, 1].nunique() <= 1:
        return float("nan")
    return float(subset.iloc[:, 0].corr(subset.iloc[:, 1]))


def _experimental_numeric_columns(df: pd.DataFrame) -> list[str]:
    return [
        column
        for column in df.columns
        if column.startswith("experimental__") and pd.api.types.is_numeric_dtype(df[column])
    ]


def _pairwise_feature_similarity(value_a: float, value_b: float) -> float:
    return float(1.0 / (1.0 + abs(float(value_a) - float(value_b))))


def _composer_label_series(frame: pd.DataFrame) -> pd.Series | None:
    if "composer" not in frame.columns:
        return None

    cleaned = frame["composer"].fillna("").astype(str).str.strip()
    if cleaned.empty:
        return None

    labels = cleaned.str.lower()
    if not labels.str.contains("mozart|chopin").any():
        return None

    return labels.str.contains("chopin").astype(float)


def _pairwise_flag_series(pairwise: pd.DataFrame, frame: pd.DataFrame, label_column: str) -> pd.Series | None:
    if pairwise is None or pairwise.empty:
        return None
    if label_column not in pairwise.columns:
        return None
    return pd.to_numeric(pairwise[label_column], errors="coerce")


def load_feature_metadata(metadata_path: str | Path | None, feature_names: Iterable[str] | None = None) -> pd.DataFrame:
    if metadata_path is None:
        return pd.DataFrame.from_records(EXPERIMENTAL_FEATURE_METADATA.values())

    path = Path(metadata_path)
    if not path.exists():
        return pd.DataFrame.from_records(EXPERIMENTAL_FEATURE_METADATA.values())

    try:
        import yaml  # type: ignore
    except Exception:
        yaml = None

    if yaml is not None:
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            loaded = None
        if isinstance(loaded, dict):
            rows: list[dict[str, object]] = []
            for key, value in loaded.items():
                if not isinstance(value, dict) or not str(key).startswith("experimental__"):
                    continue
                row = {"name": key}
                row.update(value)
                rows.append(row)
            if rows:
                return pd.DataFrame.from_records(rows)
        elif isinstance(loaded, list):
            rows = [row for row in loaded if isinstance(row, dict) and str(row.get("name", "")).startswith("experimental__")]
            if rows:
                return pd.DataFrame.from_records(rows)

    if feature_names is None:
        return pd.DataFrame.from_records(EXPERIMENTAL_FEATURE_METADATA.values())

    rows = []
    for feature_name in feature_names:
        metadata = EXPERIMENTAL_FEATURE_METADATA.get(feature_name)
        if metadata is not None:
            rows.append(metadata)
    return pd.DataFrame.from_records(rows)


def feature_audit_frame(frame: pd.DataFrame, cv_threshold: float = 0.05) -> pd.DataFrame:
    feature_columns = _experimental_numeric_columns(frame)
    if not feature_columns:
        return pd.DataFrame(
            columns=[
                "feature_name",
                "family",
                "min",
                "max",
                "mean",
                "std",
                "unique_values",
                "missing_values",
                "coefficient_of_variation",
                "near_constant",
            ]
        )
    return audit_numeric_features(frame.loc[:, feature_columns], cv_threshold=cv_threshold)


def _pairwise_input_lookup(frame: pd.DataFrame) -> dict[str, dict[str, float]]:
    if "excerpt_id" not in frame.columns:
        return {}
    lookup: dict[str, dict[str, float]] = {}
    for _, row in frame.iterrows():
        excerpt_id = str(row["excerpt_id"])
        lookup[excerpt_id] = row.to_dict()
    return lookup


def _composer_binary_from_lookup(lookup: dict[str, dict[str, float]], excerpt_id: str) -> float | None:
    row = lookup.get(excerpt_id)
    if row is None:
        return None
    composer = str(row.get("composer", "") or "").strip().lower()
    if not composer:
        return None
    if "chopin" in composer:
        return 1.0
    if "mozart" in composer:
        return 0.0
    return None


def feature_embedding_correlations(frame: pd.DataFrame, pairwise: pd.DataFrame | None = None) -> pd.DataFrame:
    feature_columns = _experimental_numeric_columns(frame)
    if not feature_columns:
        return pd.DataFrame(
            columns=[
                "feature_name",
                "family",
                "composer_label_correlation",
                "same_composer_correlation",
                "clap_similarity_correlation",
                "symbolic_core_similarity_correlation",
                "clap_minus_core_similarity_correlation",
                "pairwise_similarity_mean",
                "pairwise_similarity_std",
                "pairwise_sample_count",
            ]
        )

    pairwise_available = pairwise is not None and not pairwise.empty and "excerpt_a" in pairwise.columns and "excerpt_b" in pairwise.columns
    excerpt_lookup = _pairwise_input_lookup(frame)
    composer_series = _composer_label_series(frame)

    same_composer_series = None
    clap_series = None
    symbolic_core_series = None
    clap_minus_core_series = None
    if pairwise_available:
        same_composer_values: list[float] = []
        clap_values: list[float] = []
        symbolic_core_values: list[float] = []
        clap_minus_core_values: list[float] = []
        for _, row in pairwise.iterrows():
            excerpt_a = str(row["excerpt_a"])
            excerpt_b = str(row["excerpt_b"])
            composer_a = _composer_binary_from_lookup(excerpt_lookup, excerpt_a)
            composer_b = _composer_binary_from_lookup(excerpt_lookup, excerpt_b)
            if composer_a is None or composer_b is None:
                same_composer_values.append(np.nan)
            else:
                same_composer_values.append(1.0 if composer_a == composer_b else 0.0)

            clap_value = pd.to_numeric(pd.Series([row.get("embedding_similarity")]), errors="coerce").iloc[0]
            clap_values.append(float(clap_value) if pd.notna(clap_value) else np.nan)

            symbolic_core_value = pd.to_numeric(pd.Series([row.get("symbolic_core_similarity")]), errors="coerce").iloc[0]
            symbolic_core_values.append(float(symbolic_core_value) if pd.notna(symbolic_core_value) else np.nan)

            if pd.notna(clap_value) and pd.notna(symbolic_core_value):
                clap_minus_core_values.append(float(clap_value) - float(symbolic_core_value))
            else:
                clap_minus_core_values.append(np.nan)

        same_composer_series = pd.Series(same_composer_values, index=pairwise.index, dtype=float)
        clap_series = pd.Series(clap_values, index=pairwise.index, dtype=float)
        symbolic_core_series = pd.Series(symbolic_core_values, index=pairwise.index, dtype=float)
        clap_minus_core_series = pd.Series(clap_minus_core_values, index=pairwise.index, dtype=float)

    rows: list[dict[str, object]] = []
    feature_lookup = frame.assign(excerpt_id=frame["excerpt_id"].astype(str)).set_index("excerpt_id") if "excerpt_id" in frame.columns else None

    for feature_name in feature_columns:
        series = pd.to_numeric(frame[feature_name], errors="coerce")
        family = feature_family_for_column(feature_name)
        composer_label_correlation = _safe_corr(series, composer_series) if composer_series is not None else float("nan")

        pairwise_feature_similarity = None
        if pairwise_available and feature_lookup is not None:
            pairwise_values: list[float] = []
            for _, row in pairwise.iterrows():
                excerpt_a = str(row["excerpt_a"])
                excerpt_b = str(row["excerpt_b"])
                if excerpt_a not in feature_lookup.index or excerpt_b not in feature_lookup.index:
                    pairwise_values.append(np.nan)
                    continue
                value_a = pd.to_numeric(pd.Series([feature_lookup.at[excerpt_a, feature_name]]), errors="coerce").iloc[0]
                value_b = pd.to_numeric(pd.Series([feature_lookup.at[excerpt_b, feature_name]]), errors="coerce").iloc[0]
                if pd.isna(value_a) or pd.isna(value_b):
                    pairwise_values.append(np.nan)
                else:
                    pairwise_values.append(_pairwise_feature_similarity(float(value_a), float(value_b)))
            pairwise_feature_similarity = pd.Series(pairwise_values, index=pairwise.index, dtype=float)

        rows.append(
            {
                "feature_name": feature_name,
                "family": family,
                "composer_label_correlation": composer_label_correlation,
                "same_composer_correlation": _safe_corr(pairwise_feature_similarity, same_composer_series) if pairwise_feature_similarity is not None and same_composer_series is not None else float("nan"),
                "clap_similarity_correlation": _safe_corr(pairwise_feature_similarity, clap_series) if pairwise_feature_similarity is not None and clap_series is not None else float("nan"),
                "symbolic_core_similarity_correlation": _safe_corr(pairwise_feature_similarity, symbolic_core_series) if pairwise_feature_similarity is not None and symbolic_core_series is not None else float("nan"),
                "clap_minus_core_similarity_correlation": _safe_corr(pairwise_feature_similarity, clap_minus_core_series) if pairwise_feature_similarity is not None and clap_minus_core_series is not None else float("nan"),
                "pairwise_similarity_mean": float(pairwise_feature_similarity.mean()) if pairwise_feature_similarity is not None else float("nan"),
                "pairwise_similarity_std": float(pairwise_feature_similarity.std(ddof=0)) if pairwise_feature_similarity is not None else float("nan"),
                "pairwise_sample_count": int(pairwise_feature_similarity.dropna().shape[0]) if pairwise_feature_similarity is not None else 0,
            }
        )

    correlations_frame = pd.DataFrame.from_records(rows)
    if not correlations_frame.empty:
        correlations_frame = correlations_frame.sort_values(["family", "clap_similarity_correlation", "composer_label_correlation", "feature_name"], ascending=[True, False, False, True], na_position="last").reset_index(drop=True)
    return correlations_frame


def family_summary_frame(audit_frame: pd.DataFrame, correlations_frame: pd.DataFrame) -> pd.DataFrame:
    if audit_frame.empty:
        return pd.DataFrame(
            columns=[
                "family",
                "feature_count",
                "non_constant_feature_count",
                "average_variance",
                "strongest_clap_positive_feature",
                "strongest_clap_positive_correlation",
                "strongest_clap_negative_feature",
                "strongest_clap_negative_correlation",
                "strongest_composer_feature",
                "strongest_composer_label_correlation",
            ]
        )

    rows: list[dict[str, object]] = []
    for family, family_audit in audit_frame.groupby("family", dropna=False):
        family_correlations = correlations_frame[correlations_frame["family"] == family] if not correlations_frame.empty else pd.DataFrame()
        average_variance = float((pd.to_numeric(family_audit["std"], errors="coerce") ** 2).mean()) if "std" in family_audit.columns else float("nan")
        useful_count = int((~family_audit["near_constant"]).sum()) if "near_constant" in family_audit.columns else 0

        strongest_clap_positive_feature = ""
        strongest_clap_positive_correlation = float("nan")
        strongest_clap_negative_feature = ""
        strongest_clap_negative_correlation = float("nan")
        strongest_composer_feature = ""
        strongest_composer_label_correlation = float("nan")

        if not family_correlations.empty:
            clap_sorted = family_correlations.dropna(subset=["clap_similarity_correlation"]).sort_values("clap_similarity_correlation", ascending=False)
            if not clap_sorted.empty:
                strongest_clap_positive_feature = str(clap_sorted.iloc[0]["feature_name"])
                strongest_clap_positive_correlation = float(clap_sorted.iloc[0]["clap_similarity_correlation"])
                strongest_clap_negative_feature = str(clap_sorted.iloc[-1]["feature_name"])
                strongest_clap_negative_correlation = float(clap_sorted.iloc[-1]["clap_similarity_correlation"])

            composer_sorted = family_correlations.dropna(subset=["composer_label_correlation"]).assign(abs_correlation=lambda df: df["composer_label_correlation"].abs()).sort_values("abs_correlation", ascending=False)
            if not composer_sorted.empty:
                strongest_composer_feature = str(composer_sorted.iloc[0]["feature_name"])
                strongest_composer_label_correlation = float(composer_sorted.iloc[0]["composer_label_correlation"])

        rows.append(
            {
                "family": family,
                "feature_count": int(len(family_audit)),
                "non_constant_feature_count": useful_count,
                "average_variance": average_variance,
                "strongest_clap_positive_feature": strongest_clap_positive_feature,
                "strongest_clap_positive_correlation": strongest_clap_positive_correlation,
                "strongest_clap_negative_feature": strongest_clap_negative_feature,
                "strongest_clap_negative_correlation": strongest_clap_negative_correlation,
                "strongest_composer_feature": strongest_composer_feature,
                "strongest_composer_label_correlation": strongest_composer_label_correlation,
            }
        )

    family_frame = pd.DataFrame.from_records(rows)
    if not family_frame.empty:
        family_frame = family_frame.sort_values(["average_variance", "family"], ascending=[False, True], na_position="last").reset_index(drop=True)
    return family_frame


def build_experimental_feature_report(
    features_frame: pd.DataFrame,
    pairwise_frame: pd.DataFrame | None,
    metadata_path: str | Path | None,
    feature_sets: str,
    cv_threshold: float = 0.05,
) -> tuple[ExperimentalFeatureEvaluationResult, str]:
    metadata_frame = load_feature_metadata(metadata_path, feature_names=_experimental_numeric_columns(features_frame))
    audit_frame = feature_audit_frame(features_frame, cv_threshold=cv_threshold)
    correlations_frame = feature_embedding_correlations(features_frame, pairwise_frame)
    family_frame = family_summary_frame(audit_frame, correlations_frame)

    result = ExperimentalFeatureEvaluationResult(
        audit_frame=audit_frame,
        correlations_frame=correlations_frame,
        family_summary_frame=family_frame,
        metadata_frame=metadata_frame,
    )

    included_piece_columns = [column for column in ["excerpt_id", "title", "composer", "measure_start", "measure_end"] if column in features_frame.columns]
    included_pieces_frame = features_frame.loc[:, included_piece_columns].drop_duplicates() if included_piece_columns else pd.DataFrame()
    near_constant_frame = audit_frame[audit_frame["near_constant"]] if not audit_frame.empty and "near_constant" in audit_frame.columns else pd.DataFrame()

    if not audit_frame.empty and not family_frame.empty:
        spread_family = family_frame.iloc[0]
        spread_text = (
            f"{spread_family['family']} has the largest average variance among the experimental families "
            f"(average variance {float(spread_family['average_variance']):.6f})."
        )
    else:
        spread_text = "No experimental families were enabled, so there is no experimental spread summary."

    if not correlations_frame.empty:
        clap_frame = correlations_frame.dropna(subset=["clap_similarity_correlation"]).sort_values("clap_similarity_correlation", ascending=False)
        divergence_frame = correlations_frame.dropna(subset=["clap_minus_core_similarity_correlation"]).assign(
            abs_gap=lambda df: df["clap_minus_core_similarity_correlation"].abs()
        ).sort_values("abs_gap", ascending=False)
        composer_frame = correlations_frame.dropna(subset=["composer_label_correlation"]).assign(
            abs_correlation=lambda df: df["composer_label_correlation"].abs()
        ).sort_values("abs_correlation", ascending=False)

        clap_text = (
            f"{clap_frame.iloc[0]['feature_name']} is the strongest CLAP-aligned feature if you look at pairwise feature similarity."
            if not clap_frame.empty
            else "No CLAP alignment summary was available."
        )
        divergence_text = (
            f"{divergence_frame.iloc[0]['feature_name']} has the largest CLAP-minus-core gap signal."
            if not divergence_frame.empty
            else "No CLAP-minus-core divergence summary was available."
        )
        composer_text = (
            f"{composer_frame.iloc[0]['feature_name']} is the strongest Mozart/Chopin separator in the row-level label check."
            if not composer_frame.empty
            else "No composer label summary was available."
        )
    else:
        clap_text = "No experimental CLAP alignment summary was available."
        divergence_text = "No experimental CLAP-minus-core divergence summary was available."
        composer_text = "No composer label summary was available."

    lines = [
        "# Experimental Musicological Feature Report",
        "",
        f"Feature sets: `{feature_sets}`",
        f"Feature rows: `{len(features_frame)}`",
        f"Experimental features audited: `{len(audit_frame)}`",
        "",
        "## Overview",
        "",
        f"- Dataset size: {len(features_frame)} excerpts",
        f"- {spread_text}",
        f"- {clap_text}",
        f"- {divergence_text}",
        f"- {composer_text}",
        "",
        "## Included Pieces",
        "",
        _markdown_table(included_pieces_frame),
        "",
        "## Audit Snapshot",
        "",
        _markdown_table(audit_frame.head(20)),
        "",
        "## Near-Constant Features",
        "",
        _markdown_table(near_constant_frame.head(20)),
        "",
        "## Feature-To-Embedding Correlations",
        "",
        _markdown_table(correlations_frame.head(20)),
        "",
        "## Family Summary",
        "",
        _markdown_table(family_frame),
        "",
    ]

    if not metadata_frame.empty:
        selected_columns = [
            column
            for column in [
                "name",
                "family",
                "feature_set",
                "status",
                "expected_direction_mozart_vs_chopin",
                "risk_level",
            ]
            if column in metadata_frame.columns
        ]
        if selected_columns:
            lines.extend([
                "## Metadata Snapshot",
                "",
                _markdown_table(metadata_frame.loc[:, selected_columns]),
                "",
            ])

    lines.extend(
        [
            "## Caveats",
            "",
            "- These are musicologically motivated proxies, not definitive analytical labels.",
            "- Pairwise correlations use a simple similarity transform based on absolute feature differences.",
            "- The tiny Mozart/Chopin demo set is hypothesis-generating only.",
        ]
    )

    return result, "\n".join(lines)
