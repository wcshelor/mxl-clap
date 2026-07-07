from __future__ import annotations

import subprocess
from pathlib import Path

from music21 import meter, note, stream

import score_embedding_lab.audio_rendering as audio_rendering


def make_tiny_score() -> stream.Score:
    score = stream.Score()
    part = stream.Part()
    measure = stream.Measure(number=1)
    measure.insert(0, meter.TimeSignature("4/4"))
    measure.append(note.Note("C4", quarterLength=4))
    part.append(measure)
    score.append(part)
    return score


def test_coerce_score_to_piano_adds_piano_instrument():
    coerced = audio_rendering._coerce_score_to_piano(make_tiny_score())
    instruments = list(coerced.parts[0].recurse().getElementsByClass("Instrument"))
    assert any(inst.__class__.__name__ == "Piano" for inst in instruments)


def test_render_midi_to_wav_builds_fluidsynth_command(tmp_path: Path, monkeypatch):
    midi_path = tmp_path / "excerpt.mid"
    wav_path = tmp_path / "excerpt.wav"
    soundfont_path = tmp_path / "piano.sf2"
    midi_path.write_bytes(b"midi")
    soundfont_path.write_bytes(b"soundfont")

    commands = {}

    def fake_which(name: str) -> str:
        return f"/usr/bin/{name}"

    def fake_run(command, check, capture_output, text):
        commands["command"] = command
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(audio_rendering.shutil, "which", fake_which)
    monkeypatch.setattr(audio_rendering.subprocess, "run", fake_run)

    result = audio_rendering.render_midi_to_wav(
        midi_path=midi_path,
        out_path=wav_path,
        soundfont_path=soundfont_path,
        sample_rate=48000,
        fluidsynth_bin="fluidsynth",
    )

    assert result == wav_path
    assert commands["command"] == [
        "/usr/bin/fluidsynth",
        "-ni",
        "-F",
        str(wav_path),
        "-r",
        "48000",
        str(soundfont_path),
        str(midi_path),
    ]


def test_render_midi_to_wav_requires_soundfont_and_binary(tmp_path: Path, monkeypatch):
    midi_path = tmp_path / "excerpt.mid"
    midi_path.write_bytes(b"midi")
    missing_soundfont = tmp_path / "missing.sf2"

    monkeypatch.setattr(audio_rendering.shutil, "which", lambda _: None)

    try:
        audio_rendering.render_midi_to_wav(
            midi_path=midi_path,
            out_path=tmp_path / "excerpt.wav",
            soundfont_path=missing_soundfont,
        )
    except NotImplementedError as exc:
        assert "FluidSynth" in str(exc)
    else:
        raise AssertionError("Expected a missing FluidSynth error.")

    monkeypatch.setattr(audio_rendering.shutil, "which", lambda name: f"/usr/bin/{name}")

    try:
        audio_rendering.render_midi_to_wav(
            midi_path=midi_path,
            out_path=tmp_path / "excerpt.wav",
            soundfont_path=missing_soundfont,
        )
    except FileNotFoundError as exc:
        assert "Soundfont" in str(exc)
    else:
        raise AssertionError("Expected a missing soundfont error.")
