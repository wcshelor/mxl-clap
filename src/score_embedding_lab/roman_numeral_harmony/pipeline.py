from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .analysis import analyzer_for_name
from .features import extract_rn_harmony_feature_families, extract_rn_harmony_features


EVENT_TABLE_COLUMNS = [
    "score_id",
    "backend_name",
    "backend_version",
    "onset_quarter",
    "duration_quarter",
    "measure_number",
    "beat",
    "local_key",
    "global_key",
    "roman_numeral",
    "figure",
    "chord_root",
    "bass_note",
    "inversion",
    "function_label",
    "confidence",
    "raw_label",
    "warning_flags",
    "pitch_classes",
    "root_pitch_class",
    "bass_pitch_class",
    "is_approximate",
]


def current_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def list_score_paths(input_dir: str | Path) -> list[Path]:
    root = Path(input_dir)
    if not root.exists():
        return []
    paths = sorted(
        path
        for path in root.rglob("*")
        if path.suffix.lower() in {".xml", ".musicxml", ".mxl"}
    )
    return paths


def load_scores_from_paths(paths: list[Path]) -> list[tuple[str, Path, object]]:
    from score_embedding_lab.io import load_score_auto

    loaded: list[tuple[str, Path, object]] = []
    for path in paths:
        score = load_score_auto(path)
        score_id = path.stem
        loaded.append((score_id, path, score))
    return loaded


def analyze_scores(
    paths: list[Path],
    *,
    backend: str,
    model_name: str | None = None,
    checkpoint_path: str | None = None,
) -> list[dict]:
    analyzer = analyzer_for_name(backend, model_name=model_name, checkpoint_path=checkpoint_path)
    from score_embedding_lab.io import get_excerpt_metadata

    rows: list[dict] = []
    for score_id, path, score in load_scores_from_paths(paths):
        result = analyzer.analyze_score(score, score_id=score_id)
        rows.append(
            {
                "score_id": score_id,
                "source_path": str(path),
                "backend": analyzer.name,
                "backend_version": analyzer.version,
                "backend_available": bool(result.backend_available),
                "success": bool(result.success),
                "warnings": result.warnings,
                "events": result.to_event_rows(),
                "feature_row": extract_rn_harmony_features(score, result),
                "feature_families": extract_rn_harmony_feature_families(score, result),
                "metadata": {
                    **get_excerpt_metadata(score, path),
                    **result.metadata,
                },
                "analysis_result": result,
            }
        )
    return rows


def save_event_tables(rows: list[dict], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths: list[Path] = []
    for row in rows:
        frame = pd.DataFrame(row["events"], columns=EVENT_TABLE_COLUMNS)
        output_path = output_dir / f'{row["score_id"]}__rn_events.csv'
        frame.to_csv(output_path, index=False)
        output_paths.append(output_path)
    return output_paths


def save_feature_table(rows: list[dict], output_path: Path) -> pd.DataFrame:
    frame = pd.DataFrame([row["feature_row"] | {"score_id": row["score_id"], "backend": row["backend"], "success": row["success"]} for row in rows])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    return frame


def save_manifest(
    rows: list[dict],
    *,
    run_id: str,
    backend: str,
    config: dict,
    output_path: Path,
    event_output_dir: Path,
    feature_output_path: Path,
    pairwise_output_path: Path | None = None,
) -> dict:
    payload = {
        "run_id": run_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "backend": backend,
        "config": config,
        "inputs": [
            {
                "score_id": row["score_id"],
                "source_path": row["source_path"],
                "success": bool(row["success"]),
                "warnings": row["warnings"],
            }
            for row in rows
        ],
        "outputs": {
            "event_tables_dir": str(event_output_dir),
            "feature_table": str(feature_output_path),
            "pairwise_table": str(pairwise_output_path) if pairwise_output_path else "",
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
