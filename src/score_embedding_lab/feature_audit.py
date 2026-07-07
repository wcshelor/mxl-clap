from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .feature_registry import feature_family_for_column


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows available._"

    columns = list(frame.columns)
    rows = frame.fillna("").astype(str).to_dict(orient="records")
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(row.get(column, "") for column in columns) + " |" for row in rows]
    return "\n".join([header, separator, *body])


def audit_numeric_features(
    df: pd.DataFrame,
    cv_threshold: float = 0.05,
) -> pd.DataFrame:
    """Summarize numeric feature columns for audit and drift checks."""
    records: list[dict[str, object]] = []
    numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()

    for column in numeric_columns:
        series = pd.to_numeric(df[column], errors="coerce")
        non_null = series.dropna()
        missing_values = int(series.isna().sum())
        value_count = int(non_null.nunique())
        minimum = float(non_null.min()) if not non_null.empty else np.nan
        maximum = float(non_null.max()) if not non_null.empty else np.nan
        mean_value = float(non_null.mean()) if not non_null.empty else np.nan
        std_value = float(non_null.std(ddof=0)) if not non_null.empty else np.nan
        if not non_null.empty and mean_value == 0.0:
            coefficient_of_variation = 0.0 if std_value == 0.0 else np.inf
        elif not non_null.empty:
            coefficient_of_variation = float(std_value / abs(mean_value))
        else:
            coefficient_of_variation = np.nan

        near_constant = bool(
            value_count <= 1
            or (not np.isnan(std_value) and std_value <= 1e-9)
            or (np.isfinite(coefficient_of_variation) and coefficient_of_variation < cv_threshold)
        )

        records.append(
            {
                "feature_name": column,
                "family": feature_family_for_column(column),
                "min": minimum,
                "max": maximum,
                "mean": mean_value,
                "std": std_value,
                "unique_values": value_count,
                "missing_values": missing_values,
                "coefficient_of_variation": coefficient_of_variation,
                "near_constant": near_constant,
            }
        )

    audit_frame = pd.DataFrame.from_records(records)
    if not audit_frame.empty:
        audit_frame = audit_frame.sort_values(
            ["near_constant", "coefficient_of_variation", "family", "feature_name"],
            ascending=[False, True, True, True],
            na_position="last",
        ).reset_index(drop=True)
    return audit_frame


def build_audit_summary_markdown(
    audit_frame: pd.DataFrame,
    source_path: str | Path,
    cv_threshold: float = 0.05,
    top_k: int = 10,
) -> str:
    """Create a short markdown summary for the symbolic feature audit."""
    total = len(audit_frame)
    near_constant = int(audit_frame["near_constant"].sum()) if not audit_frame.empty else 0
    near_constant_frame = audit_frame[audit_frame["near_constant"]].head(top_k)
    variable_frame = audit_frame.sort_values(
        ["coefficient_of_variation", "feature_name"],
        ascending=[False, True],
        na_position="last",
    ).head(top_k)

    lines = [
        "# Symbolic Feature Audit",
        "",
        f"Source CSV: `{source_path}`",
        f"Near-constant threshold: coefficient of variation `< {cv_threshold}` or a single unique value.",
        "",
        f"- Numeric features audited: {total}",
        f"- Near-constant features flagged: {near_constant}",
        "",
        "## Most Stable Features",
        "",
    ]

    if near_constant_frame.empty:
        lines.append("_No near-constant features detected._")
    else:
        selected_columns = [
            column
            for column in ["feature_name", "family", "unique_values", "missing_values", "coefficient_of_variation"]
            if column in near_constant_frame.columns
        ]
        lines.append(_markdown_table(near_constant_frame.loc[:, selected_columns]))

    lines.extend(["", "## Most Variable Features", ""])
    if variable_frame.empty:
        lines.append("_No numeric features detected._")
    else:
        selected_columns = [
            column
            for column in ["feature_name", "family", "mean", "std", "missing_values", "coefficient_of_variation"]
            if column in variable_frame.columns
        ]
        lines.append(_markdown_table(variable_frame.loc[:, selected_columns]))

    return "\n".join(lines)
