from __future__ import annotations

import copy
import os
import shutil
import subprocess
from pathlib import Path

from music21 import instrument
from music21.repeat import ExpanderException

DEFAULT_SAMPLE_RATE = 48000


def _resolve_soundfont_path(soundfont_path: str | Path | None) -> Path:
    candidate = soundfont_path or os.environ.get("MXL_CLAP_SOUND_FONT") or os.environ.get("MXL_CLAP_SOUNDFONT")
    if candidate is None:
        raise NotImplementedError(
            "No soundfont configured. Pass --soundfont or set MXL_CLAP_SOUND_FONT to a GM piano soundfont."
        )

    resolved = Path(candidate).expanduser()
    if not resolved.exists():
        raise FileNotFoundError(f"Soundfont does not exist: {resolved}")
    return resolved


def _resolve_fluidsynth_binary(fluidsynth_bin: str) -> str:
    resolved = shutil.which(fluidsynth_bin)
    if resolved is None:
        raise NotImplementedError(
            f"Could not find '{fluidsynth_bin}' on PATH. Install FluidSynth before rendering audio."
        )
    return resolved


def _coerce_score_to_piano(score):
    score_copy = copy.deepcopy(score)
    parts = list(getattr(score_copy, "parts", []))
    if not parts:
        raise ValueError("The score does not contain any parts to render.")

    for part in parts:
        try:
            part.insert(0, instrument.Piano())
        except Exception as exc:
            raise ValueError(f"Could not assign a piano instrument to part {part!r}") from exc

    return score_copy


def write_midi(score, out_path: str | Path):
    """Write a piano-oriented MIDI file from a music21 score.

    If music21 cannot expand malformed repeats, fall back to a flattened
    stream so audio rendering can still proceed.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    piano_score = _coerce_score_to_piano(score)
    try:
        piano_score.write("midi", fp=str(out_path))
    except ExpanderException:
        piano_score.flatten().write("midi", fp=str(out_path))
    return out_path


def render_midi_to_wav(
    midi_path: str | Path,
    out_path: str | Path,
    soundfont_path: str | Path | None = None,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    fluidsynth_bin: str = "fluidsynth",
):
    """Render a MIDI file to WAV with FluidSynth and a GM soundfont."""
    midi_path = Path(midi_path)
    out_path = Path(out_path)
    if not midi_path.exists():
        raise FileNotFoundError(f"MIDI file does not exist: {midi_path}")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")

    soundfont = _resolve_soundfont_path(soundfont_path)
    fluidsynth = _resolve_fluidsynth_binary(fluidsynth_bin)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        fluidsynth,
        "-ni",
        "-F",
        str(out_path),
        "-r",
        str(int(sample_rate)),
        str(soundfont),
        str(midi_path),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        details = stderr or stdout or "FluidSynth returned a non-zero exit code."
        raise RuntimeError(f"FluidSynth failed while rendering {midi_path}: {details}") from exc
    return out_path


def render_score_to_wav(
    score,
    midi_path: str | Path,
    out_path: str | Path,
    soundfont_path: str | Path | None = None,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    fluidsynth_bin: str = "fluidsynth",
):
    """Write MIDI for a score and render it to WAV."""
    midi_path = write_midi(score, midi_path)
    return render_midi_to_wav(
        midi_path=midi_path,
        out_path=out_path,
        soundfont_path=soundfont_path,
        sample_rate=sample_rate,
        fluidsynth_bin=fluidsynth_bin,
    )


def render_audio_placeholder(
    midi_path: str | Path,
    out_path: str | Path,
    soundfont_path: str | Path | None = None,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    fluidsynth_bin: str = "fluidsynth",
):
    """Compatibility wrapper for the old placeholder name."""
    return render_midi_to_wav(
        midi_path=midi_path,
        out_path=out_path,
        soundfont_path=soundfont_path,
        sample_rate=sample_rate,
        fluidsynth_bin=fluidsynth_bin,
    )
