from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from score_embedding_lab.roman_numeral_harmony.evaluation import (
    feature_audit_frame,
    family_summary_frame,
    ranked_feature_candidates,
)
from score_embedding_lab.roman_numeral_harmony.pipeline import (
    analyze_scores,
    current_run_id,
    list_score_paths,
    save_event_tables,
    save_feature_table,
    save_manifest,
)
from score_embedding_lab.similarity import cosine_similarity_matrix, feature_dataframe_to_matrix


LANE_ROOT = ROOT / "research_lanes" / "roman_numeral_harmony"
DEFAULT_CONFIG = LANE_ROOT / "configs" / "rn_harmony_default.yml"
DEFAULT_CACHE_ROOT = LANE_ROOT / "cache"
DEFAULT_REPORTS_ROOT = LANE_ROOT / "reports"


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the experimental Roman numeral harmony lane.")
    parser.add_argument("--input-dir", type=Path, default=ROOT / "data" / "raw" / "full-pieces", help="Directory to scan for MusicXML/MXL files.")
    parser.add_argument("--manifest", type=Path, default=None, help="Optional CSV manifest with score paths.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="YAML config for the lane.")
    parser.add_argument("--backend", type=str, default=None, help="Analyzer backend name. Overrides the config when set.")
    parser.add_argument("--model-name", type=str, default=None, help="Optional model name for RNBert-style backends.")
    parser.add_argument("--checkpoint-path", type=str, default=None, help="Optional checkpoint path for RNBert-style backends.")
    parser.add_argument("--run-id", type=str, default=None, help="Override the generated run id.")
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE_ROOT, help="Root directory for cached RN event tables.")
    parser.add_argument("--reports-root", type=Path, default=DEFAULT_REPORTS_ROOT, help="Root directory for report tables.")
    parser.add_argument("--features-output", type=Path, default=None, help="Override the feature table output path.")
    parser.add_argument("--pairwise-output", type=Path, default=None, help="Override the pairwise similarity output path.")
    parser.add_argument("--report-output", type=Path, default=None, help="Override the markdown report output path.")
    return parser


def _load_config(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _manifest_paths(manifest: Path, input_dir: Path) -> list[Path]:
    frame = pd.read_csv(manifest)
    path_columns = ["excerpt_path", "source_path", "path", "file_path"]
    paths: list[Path] = []
    for _, row in frame.iterrows():
        path_value = None
        for column in path_columns:
            value = row.get(column)
            if pd.notna(value) and str(value).strip():
                path_value = Path(str(value))
                break
        if path_value is None:
            continue
        if not path_value.is_absolute():
            candidate = input_dir / path_value
            path_value = candidate if candidate.exists() else path_value
        paths.append(path_value)
    return paths


def _family_columns(features: pd.DataFrame) -> dict[str, list[str]]:
    return {
        "experimental_rn_harmony_similarity": [column for column in features.columns if column.startswith("experimental__rn_harmony__")],
        "experimental_harmony_texture_similarity": [column for column in features.columns if column.startswith("experimental__harmony_texture__")],
        "experimental_harmony_melody_similarity": [column for column in features.columns if column.startswith("experimental__harmony_melody__")],
        "experimental_rn_all_similarity": [
            column
            for column in features.columns
            if column.startswith("experimental__rn_harmony__")
            or column.startswith("experimental__harmony_texture__")
            or column.startswith("experimental__harmony_melody__")
        ],
    }


def _pairwise_table(features: pd.DataFrame) -> pd.DataFrame:
    ids = features["score_id"].astype(str).tolist()
    family_columns = _family_columns(features)
    matrices: dict[str, np.ndarray] = {}
    for name, columns in family_columns.items():
        if columns:
            matrix, _ = feature_dataframe_to_matrix(features, ignore_columns=["score_id", "backend", "success"], columns=columns)
            matrices[name] = cosine_similarity_matrix(matrix)
        else:
            matrices[name] = np.zeros((len(features), len(features)), dtype=float)
    records = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            record = {
                "score_a": ids[i],
                "score_b": ids[j],
                "pair_id": f"{ids[i]}__{ids[j]}",
            }
            for name, matrix in matrices.items():
                record[name] = float(matrix[i, j]) if matrix.size else 0.0
            records.append(record)
    return pd.DataFrame.from_records(records)


def _read_manifest_or_paths(args) -> list[Path]:
    if args.manifest is not None and args.manifest.exists():
        return _manifest_paths(args.manifest, args.input_dir)
    return list_score_paths(args.input_dir)


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    config = _load_config(args.config)
    backend = (args.backend or config.get("backend") or "music21_light").strip()
    model_name = args.model_name or config.get("model_name")
    checkpoint_path = args.checkpoint_path or config.get("checkpoint_path")
    run_id = args.run_id or current_run_id()

    input_paths = _read_manifest_or_paths(args)
    if not input_paths:
        raise SystemExit("No MusicXML/MXL inputs found.")

    cache_root = args.cache_root / run_id
    events_dir = cache_root / "events"
    reports_root = args.reports_root
    reports_root.mkdir(parents=True, exist_ok=True)

    rows = analyze_scores(
        input_paths,
        backend=backend,
        model_name=model_name,
        checkpoint_path=checkpoint_path,
    )
    if not rows:
        raise SystemExit("No scores could be analyzed.")

    save_event_tables(rows, events_dir)

    feature_output = args.features_output or (reports_root / f"{run_id}_rn_harmony_features.csv")
    pairwise_output = args.pairwise_output or (reports_root / f"{run_id}_rn_pairwise_similarities.csv")
    report_output = args.report_output or (reports_root / f"{run_id}_rn_harmony_report.md")
    features = save_feature_table(rows, feature_output)
    pairwise = _pairwise_table(features)
    pairwise_output.parent.mkdir(parents=True, exist_ok=True)
    pairwise.to_csv(pairwise_output, index=False)

    audit = feature_audit_frame(features)
    family = family_summary_frame(features)
    ranked = ranked_feature_candidates(audit)

    audit_output = reports_root / f"{run_id}_feature_audit.csv"
    family_output = reports_root / f"{run_id}_family_summary.csv"
    events_summary_output = reports_root / f"{run_id}_rn_events_summary.csv"
    audit.to_csv(audit_output, index=False)
    family.to_csv(family_output, index=False)
    pd.DataFrame(
        [
            {
                "score_id": row["score_id"],
                "backend": row["backend"],
                "success": row["success"],
                "event_count": len(row["events"]),
                "warning_count": len(row["warnings"]),
            }
            for row in rows
        ]
    ).to_csv(events_summary_output, index=False)

    manifest_output = cache_root / "run_manifest.json"
    save_manifest(
        rows,
        run_id=run_id,
        backend=backend,
        config={"backend": backend, **config},
        output_path=manifest_output,
        event_output_dir=events_dir,
        feature_output_path=feature_output,
        pairwise_output_path=pairwise_output,
    )

    report_lines = [
        "# Roman Numeral Harmony Experiment",
        "",
        f"- Run id: `{run_id}`",
        f"- Backend: `{backend}`",
        f"- Inputs: `{len(input_paths)}`",
        f"- Successful analyses: `{int(features['success'].sum())}`",
        "",
        "## Outputs",
        f"- Feature table: `{feature_output}`",
        f"- Pairwise table: `{pairwise_output}`",
        f"- Feature audit: `{audit_output}`",
        f"- Family summary: `{family_output}`",
        f"- Event summary: `{events_summary_output}`",
        f"- Run manifest: `{manifest_output}`",
        "",
        "## Top Feature Candidates",
    ]
    if not ranked.empty:
        for _, row in ranked.head(10).iterrows():
            report_lines.append(f"- `{row['feature']}` near_constant={bool(row['near_constant'])} cv={row['coefficient_of_variation']:.3f}")
    else:
        report_lines.append("- No features were available.")
    report_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"Wrote events under {events_dir}")
    print(f"Wrote feature table to {feature_output}")
    print(f"Wrote pairwise table to {pairwise_output}")
    print(f"Wrote feature audit to {audit_output}")
    print(f"Wrote family summary to {family_output}")
    print(f"Wrote event summary to {events_summary_output}")
    print(f"Wrote report to {report_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
