from __future__ import annotations

from collections.abc import Mapping

import pandas as pd


def _as_dict(row) -> dict:
    if isinstance(row, Mapping):
        return dict(row)
    if hasattr(row, "to_dict"):
        return dict(row.to_dict())
    return dict(row)


def _format_feature_summary(summary) -> str:
    data = _as_dict(summary)
    preferred_keys = [
        "note_count",
        "total_duration_quarter_lengths",
        "note_density",
        "ambitus_semitones",
        "pitch_range_semitones",
        "mean_pitch",
        "rhythmic_diversity",
        "chordified_chord_count",
    ]
    lines = []
    seen = set()
    for key in preferred_keys:
        if key in data:
            lines.append(f"- {key}: {data[key]}")
            seen.add(key)
    for key in sorted(k for k in data.keys() if k not in seen):
        if key.startswith(("pitch_class_", "interval_", "duration_bin_")):
            lines.append(f"- {key}: {data[key]}")
    return "\n".join(lines) if lines else "- (no features available)"


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows available._"

    columns = list(frame.columns)
    rows = frame.fillna("").astype(str).to_dict(orient="records")
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(row.get(column, "") for column in columns) + " |" for row in rows]
    return "\n".join([header, separator, *body])


def make_pair_explanation_prompt(row, feature_summary_a, feature_summary_b) -> str:
    """Create a prompt for an LLM to explain one pairwise comparison."""
    data = _as_dict(row)
    excerpt_a = data.get("excerpt_a", "excerpt_a")
    excerpt_b = data.get("excerpt_b", "excerpt_b")

    return "\n".join(
        [
            "You are comparing two short score excerpts. Keep the explanation cautious and musicologically grounded.",
            "Do not claim that the embedding model understands music.",
            "",
            f"Excerpt A: {excerpt_a}",
            f"Excerpt B: {excerpt_b}",
            "",
            f"Symbolic similarity: {data.get('symbolic_similarity', '')}",
            f"Embedding similarity: {data.get('embedding_similarity', '')}",
            f"Similarity gap: {data.get('similarity_gap', '')}",
            "",
            "Feature summary for excerpt A:",
            _format_feature_summary(feature_summary_a),
            "",
            "Feature summary for excerpt B:",
            _format_feature_summary(feature_summary_b),
            "",
            "Please answer in 3 short parts:",
            "1. What seems similar at the notated level?",
            "2. Does the embedding similarity look plausible given the symbolic evidence?",
            "3. What uncertainty or limitation should be stated?",
        ]
    )


def make_comparison_table_for_llm(pairwise_results) -> str:
    """Create a Markdown table that can be pasted into an LLM prompt."""
    if not isinstance(pairwise_results, pd.DataFrame):
        pairwise_results = pd.DataFrame(pairwise_results)

    columns = [
        "excerpt_a",
        "excerpt_b",
        "symbolic_similarity",
        "embedding_similarity",
        "similarity_gap",
    ]
    present_columns = [column for column in columns if column in pairwise_results.columns]
    table = pairwise_results.loc[:, present_columns].copy()
    return _markdown_table(table)
