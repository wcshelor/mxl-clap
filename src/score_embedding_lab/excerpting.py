from __future__ import annotations

import copy
import re
from pathlib import Path

import pandas as pd
from music21 import instrument, stream

from .io import get_excerpt_metadata, list_excerpt_paths, load_score_auto

SAFE_TOKEN_RE = re.compile(r"[^A-Za-z0-9]+")


def _slugify(value: str) -> str:
    token = SAFE_TOKEN_RE.sub("-", value).strip("-").lower()
    return token or "excerpt"


def build_excerpt_id(source_path: str | Path, measure_start: int, measure_end: int) -> str:
    source_token = _slugify(Path(source_path).stem)
    return f"{source_token}_m{measure_start:03d}_m{measure_end:03d}"


def build_prefix_excerpt_id(
    source_path: str | Path,
    measure_start: int,
    measure_end: int,
    requested_measure_end: int | None = None,
) -> str:
    """Build a prefix excerpt id, keeping clamped requests distinct."""
    excerpt_id = build_excerpt_id(source_path, measure_start, measure_end)
    if requested_measure_end is not None and int(requested_measure_end) != int(measure_end):
        excerpt_id = f"{excerpt_id}_req{int(requested_measure_end):03d}"
    return excerpt_id


def _write_excerpt_score(score, excerpt_path: Path) -> None:
    """Write a score to MusicXML/MXL, flattening as a fallback for tricky voices."""
    try:
        score.write("mxl", fp=str(excerpt_path))
        return
    except Exception:
        flattened = score.flatten()
        flattened.write("mxl", fp=str(excerpt_path))


def _force_piano_instrument(score):
    """Ensure the excerpt advertises a piano instrument for playback/export."""
    target = copy.deepcopy(score)
    parts = list(getattr(target, "parts", []))
    if parts:
        for part in parts:
            try:
                part.insert(0, instrument.Piano())
            except Exception:
                continue
        return target

    try:
        target.insert(0, instrument.Piano())
    except Exception:
        pass
    return target


def count_measures(score) -> int:
    """Return the highest measure number in the score, or a simple count fallback."""
    measure_numbers: list[int] = []

    for part in list(getattr(score, "parts", [])):
        try:
            measures = list(part.getElementsByClass(stream.Measure))
        except Exception:
            continue

        for measure in measures:
            number = getattr(measure, "number", None)
            if number is None:
                continue
            try:
                measure_numbers.append(int(number))
            except (TypeError, ValueError):
                continue

    if measure_numbers:
        return max(measure_numbers)

    try:
        all_measures = list(score.recurse().getElementsByClass(stream.Measure))
    except Exception:
        return 0
    return len(all_measures)


def iter_measure_windows(
    total_measures: int,
    window_size: int,
    stride: int,
    include_partial_final: bool = False,
) -> list[tuple[int, int]]:
    """Create contiguous measure windows using 1-based inclusive measure numbers."""
    if total_measures <= 0:
        return []
    if window_size <= 0:
        raise ValueError("window_size must be positive")
    if stride <= 0:
        raise ValueError("stride must be positive")

    if total_measures <= window_size:
        return [(1, total_measures)]

    windows: list[tuple[int, int]] = []
    last_full_start = total_measures - window_size + 1

    for start in range(1, last_full_start + 1, stride):
        end = start + window_size - 1
        windows.append((start, end))

    if include_partial_final:
        next_start = 1 if not windows else windows[-1][0] + stride
        if next_start <= total_measures:
            final_end = total_measures
            final_start = next_start
            if not windows or windows[-1] != (final_start, final_end):
                windows.append((final_start, final_end))

    return windows


def extract_measure_window(score, measure_start: int, measure_end: int):
    """Extract a contiguous measure span from a score."""
    try:
        excerpt = score.measures(measure_start, measure_end)
        if excerpt is not None:
            try:
                has_content = len(list(excerpt.recurse().notesAndRests)) > 0
            except Exception:
                has_content = True
            if has_content:
                if getattr(score, "metadata", None) is not None:
                    excerpt.metadata = copy.deepcopy(score.metadata)
                return _force_piano_instrument(excerpt)
    except Exception:
        pass

    excerpt_score = stream.Score()
    appended_parts = 0

    for part in list(getattr(score, "parts", [])):
        try:
            part_excerpt = part.measures(measure_start, measure_end)
        except Exception:
            continue
        if part_excerpt is None:
            continue
        excerpt_score.append(part_excerpt)
        appended_parts += 1

    if appended_parts == 0:
        raise ValueError(f"Could not extract measures {measure_start}-{measure_end} from score")

    if getattr(score, "metadata", None) is not None:
        excerpt_score.metadata = copy.deepcopy(score.metadata)
    return _force_piano_instrument(excerpt_score)


def _manifest_rows_for_source(
    source_path: str | Path,
    output_dir: str | Path,
    score,
    window_size: int,
    stride: int,
    include_partial_final: bool,
) -> list[dict[str, object]]:
    source_path = Path(source_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_metadata = get_excerpt_metadata(score, source_path)
    total_measures = count_measures(score)
    windows = iter_measure_windows(
        total_measures=total_measures,
        window_size=window_size,
        stride=stride,
        include_partial_final=include_partial_final,
    )
    if not windows:
        return []

    rows: list[dict[str, object]] = []
    for measure_start, measure_end in windows:
        excerpt_id = build_excerpt_id(source_path, measure_start, measure_end)
        excerpt_path = output_dir / f"{excerpt_id}.musicxml"
        excerpt_score = extract_measure_window(score, measure_start, measure_end)
        excerpt_score.write("musicxml", fp=str(excerpt_path))

        rows.append(
            {
                "source_id": source_metadata["excerpt_id"],
                "source_file": source_metadata["filename"],
                "source_path": source_metadata["source_path"],
                "title": source_metadata["title"],
                "composer": source_metadata["composer"],
                "source_total_measures": int(total_measures),
                "measure_start": int(measure_start),
                "measure_end": int(measure_end),
                "window_size": int(window_size),
                "stride": int(stride),
                "excerpt_id": excerpt_id,
                "excerpt_file": excerpt_path.name,
                "excerpt_path": str(excerpt_path),
            }
        )

    return rows


def _prefix_manifest_rows_for_source(
    source_path: str | Path,
    output_dir: str | Path,
    score,
    prefix_lengths: list[int],
) -> list[dict[str, object]]:
    source_path = Path(source_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_metadata = get_excerpt_metadata(score, source_path)
    total_measures = count_measures(score)

    rows: list[dict[str, object]] = []
    for requested_end in prefix_lengths:
        if requested_end <= 0:
            raise ValueError("prefix lengths must be positive")
        actual_end = min(int(requested_end), int(total_measures))
        excerpt_id = build_prefix_excerpt_id(source_path, 1, actual_end, requested_measure_end=requested_end)
        excerpt_path = output_dir / f"{excerpt_id}.mxl"
        excerpt_score = extract_measure_window(score, 1, actual_end)
        _write_excerpt_score(excerpt_score, excerpt_path)

        rows.append(
            {
                "source_id": source_metadata["excerpt_id"],
                "source_file": source_metadata["filename"],
                "source_path": source_metadata["source_path"],
                "title": source_metadata["title"],
                "composer": source_metadata["composer"],
                "source_total_measures": int(total_measures),
                "measure_start": 1,
                "measure_end": int(actual_end),
                "requested_measure_end": int(requested_end),
                "excerpt_id": excerpt_id,
                "excerpt_file": excerpt_path.name,
                "excerpt_path": str(excerpt_path),
            }
        )

    return rows


def extract_excerpts_from_file(
    source_path: str | Path,
    output_dir: str | Path,
    window_size: int = 4,
    stride: int = 4,
    include_partial_final: bool = False,
) -> list[dict[str, object]]:
    score = load_score_auto(source_path)
    return _manifest_rows_for_source(
        source_path=source_path,
        output_dir=output_dir,
        score=score,
        window_size=window_size,
        stride=stride,
        include_partial_final=include_partial_final,
    )


def extract_excerpts_from_directory(
    input_dir: str | Path,
    output_dir: str | Path,
    window_size: int = 4,
    stride: int = 4,
    include_partial_final: bool = False,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for source_path in list_excerpt_paths(input_dir):
        try:
            rows.extend(
                extract_excerpts_from_file(
                    source_path=source_path,
                    output_dir=output_dir,
                    window_size=window_size,
                    stride=stride,
                    include_partial_final=include_partial_final,
                )
            )
        except Exception as exc:
            print(f"Skipping {source_path}: {exc}")

    if not rows:
        return pd.DataFrame(
            columns=[
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
        )

    frame = pd.DataFrame(rows)
    sort_columns = [column for column in ("source_file", "measure_start", "measure_end", "excerpt_id") if column in frame.columns]
    if sort_columns:
        frame = frame.sort_values(sort_columns, kind="stable").reset_index(drop=True)
    return frame


def extract_prefix_excerpts_from_directory(
    input_dir: str | Path,
    output_dir: str | Path,
    prefix_lengths: list[int],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for source_path in list_excerpt_paths(input_dir):
        try:
            score = load_score_auto(source_path)
        except Exception as exc:
            print(f"Skipping {source_path}: {exc}")
            continue

        try:
            rows.extend(_prefix_manifest_rows_for_source(source_path, output_dir, score, prefix_lengths))
        except Exception as exc:
            print(f"Skipping {source_path}: {exc}")

    if not rows:
        return pd.DataFrame(
            columns=[
                "source_id",
                "source_file",
                "source_path",
                "title",
                "composer",
                "source_total_measures",
                "measure_start",
                "measure_end",
                "requested_measure_end",
                "excerpt_id",
                "excerpt_file",
                "excerpt_path",
            ]
        )

    frame = pd.DataFrame(rows)
    sort_columns = [column for column in ("source_file", "measure_end", "excerpt_id") if column in frame.columns]
    if sort_columns:
        frame = frame.sort_values(sort_columns, kind="stable").reset_index(drop=True)
    return frame
