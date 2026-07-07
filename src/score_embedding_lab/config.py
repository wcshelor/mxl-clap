from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_RAW_FULL_PIECES = DATA_RAW / "full-pieces"
DATA_RAW_EXCERPTS = DATA_RAW / "excerpts"
DATA_RAW_EXCERPTS_GENERATED = DATA_RAW_EXCERPTS / "generated"
DATA_RAW_PREFIX_EXCERPTS = DATA_RAW_EXCERPTS / "prefixes"
DATA_PROCESSED = DATA_DIR / "processed"
EXCERPT_MANIFEST = DATA_PROCESSED / "excerpt_manifest.csv"
AUDIO_MANIFEST = DATA_PROCESSED / "audio_manifest.csv"
DATA_MIDI_DIR = DATA_PROCESSED / "midi"
DATA_AUDIO_DIR = DATA_PROCESSED / "audio"
REPORTS_DIR = PROJECT_ROOT / "reports"
EXTERNAL_DIR = PROJECT_ROOT / "external"
EXTERNAL_MXL_TOOLBOX = EXTERNAL_DIR / "mxl-toolbox"
