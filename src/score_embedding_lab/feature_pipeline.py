from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd

from .config import DATA_RAW_EXCERPTS_GENERATED
from .io import get_excerpt_metadata, list_excerpt_paths, load_score_auto
from .symbolic_features import extract_symbolic_features


DEFAULT_EXCERPT_COLUMNS = [
    "source_id",
    "source_file",
    "source_path",
    "title",
    "composer",
    "source_total_measures",
    "measure_start",
    "measure_end",
    "window_size",
    "stride",
    "excerpt_id",
    "excerpt_file",
    "excerpt_path",
]


def _set_if_blank(row: dict, key: str, value) -> None:
    current = row.get(key)
    if key not in row or pd.isna(current) or current == "":
        row[key] = value


def load_excerpt_feature_rows(
    manifest_path: str | Path | None,
    input_dir: str | Path = DATA_RAW_EXCERPTS_GENERATED,
    feature_sets: Sequence[str] | str | None = None,
) -> list[dict]:
    if manifest_path is not None:
        manifest = Path(manifest_path)
        if manifest.exists():
            frame = pd.read_csv(manifest)
            if frame.empty:
                return []

            rows: list[dict] = []
            for _, manifest_row in frame.iterrows():
                excerpt_path_value = manifest_row.get("excerpt_path", "")
                if pd.isna(excerpt_path_value) or not str(excerpt_path_value):
                    excerpt_path_value = Path(input_dir) / str(manifest_row.get("excerpt_file", ""))
                excerpt_path = Path(str(excerpt_path_value))
                try:
                    score = load_score_auto(excerpt_path)
                except Exception as exc:
                    print(f"Skipping {excerpt_path}: {exc}")
                    continue

                row = manifest_row.to_dict()
                excerpt_metadata = get_excerpt_metadata(score, excerpt_path)
                _set_if_blank(row, "excerpt_id", excerpt_metadata["excerpt_id"])
                _set_if_blank(row, "excerpt_file", excerpt_metadata["filename"])
                _set_if_blank(row, "excerpt_path", str(excerpt_path))
                _set_if_blank(row, "title", excerpt_metadata["title"])
                _set_if_blank(row, "composer", excerpt_metadata["composer"])
                row.update(extract_symbolic_features(score, feature_sets=feature_sets))
                rows.append(row)
            return rows

    rows = []
    for path in list_excerpt_paths(input_dir):
        try:
            score = load_score_auto(path)
        except Exception as exc:
            print(f"Skipping {path}: {exc}")
            continue

        row = get_excerpt_metadata(score, path)
        row.update(extract_symbolic_features(score, feature_sets=feature_sets))
        rows.append(row)
    return rows


def build_excerpt_feature_frame(rows: Iterable[dict]) -> pd.DataFrame:
    rows = list(rows)
    if rows:
        return pd.DataFrame(rows)
    return pd.DataFrame(columns=DEFAULT_EXCERPT_COLUMNS)
