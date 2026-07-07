from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Iterable

from music21 import converter

from .config import DATA_RAW_EXCERPTS, EXTERNAL_MXL_TOOLBOX


def load_score(path: str | Path):
    """Load a score with music21."""
    return converter.parse(str(path))


def _try_external_toolbox_loader():
    """Return a parser from an optional external MXL toolbox if one is discoverable."""
    if not EXTERNAL_MXL_TOOLBOX.exists():
        return None

    toolbox_path = str(EXTERNAL_MXL_TOOLBOX.resolve())
    if toolbox_path not in sys.path:
        sys.path.insert(0, toolbox_path)

    for module_name in ("mxltoolbox", "mxl_toolbox"):
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        for attr_name in ("load_score", "load_mxl", "parse_score", "parse_mxl", "read_score"):
            loader = getattr(module, attr_name, None)
            if callable(loader):
                return loader
    return None


def load_score_auto(path: str | Path):
    """Try the external toolbox first, then fall back to music21."""
    loader = _try_external_toolbox_loader()
    if loader is not None:
        try:
            return loader(path)
        except Exception:
            pass
    return load_score(path)


def get_excerpt_metadata(score, path: str | Path) -> dict[str, str]:
    """Return small metadata for a score excerpt."""
    source_path = Path(path)
    metadata = getattr(score, "metadata", None)
    title = ""
    composer = ""
    if metadata is not None:
        for attr_name in ("title", "movementName", "movementTitle", "workTitle"):
            title = getattr(metadata, attr_name, "") or ""
            if title:
                break
        composer = getattr(metadata, "composer", "") or ""

    return {
        "excerpt_id": source_path.stem,
        "title": title or source_path.stem,
        "composer": composer or "",
        "filename": source_path.name,
        "source_path": str(source_path),
    }


def list_excerpt_paths(root: str | Path = DATA_RAW_EXCERPTS) -> list[Path]:
    """List MusicXML / MXL files under the excerpt directory."""
    root_path = Path(root)
    if not root_path.exists():
        return []

    patterns = ("*.xml", "*.musicxml", "*.mxl")
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(root_path.rglob(pattern))
    return sorted({path.resolve() for path in paths})


def list_audio_paths(root: str | Path) -> list[Path]:
    """List rendered WAV files under a directory."""
    root_path = Path(root)
    if not root_path.exists():
        return []
    return sorted(root_path.rglob("*.wav"))
