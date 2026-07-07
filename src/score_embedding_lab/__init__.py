"""Tiny scaffold for excerpting, symbolic features, audio embeddings, and similarity."""

from .config import (
    AUDIO_MANIFEST,
    DATA_AUDIO_DIR,
    DATA_MIDI_DIR,
    DATA_PROCESSED,
    DATA_RAW_EXCERPTS,
    DATA_RAW_EXCERPTS_GENERATED,
    DATA_RAW_FULL_PIECES,
    DATA_RAW_PREFIX_EXCERPTS,
    EXCERPT_MANIFEST,
    EXTERNAL_MXL_TOOLBOX,
)

__all__ = [
    "DATA_PROCESSED",
    "DATA_RAW_EXCERPTS",
    "DATA_RAW_EXCERPTS_GENERATED",
    "DATA_RAW_FULL_PIECES",
    "DATA_RAW_PREFIX_EXCERPTS",
    "DATA_MIDI_DIR",
    "DATA_AUDIO_DIR",
    "EXCERPT_MANIFEST",
    "AUDIO_MANIFEST",
    "EXTERNAL_MXL_TOOLBOX",
]

__version__ = "0.1.0"
