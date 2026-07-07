from __future__ import annotations

from pathlib import Path
import unittest

try:
    from music21 import chord, meter, note, stream
except Exception:  # pragma: no cover - optional dependency
    chord = None
    meter = None
    note = None
    stream = None

from score_embedding_lab.roman_numeral_harmony.analyzers.music21_light import Music21LightRomanNumeralAnalyzer
from score_embedding_lab.roman_numeral_harmony.analyzers.rnbert import RNBertRomanNumeralAnalyzer
from score_embedding_lab.roman_numeral_harmony.features import extract_rn_harmony_features
from score_embedding_lab.roman_numeral_harmony.models import RomanNumeralAnalysisResult, RomanNumeralEvent
from score_embedding_lab.roman_numeral_harmony.pipeline import save_event_tables


def make_tiny_score():
    if chord is None or meter is None or note is None or stream is None:
        raise unittest.SkipTest("music21 is not installed in this runtime.")
    score = stream.Score()
    part = stream.Part()
    part.append(meter.TimeSignature("4/4"))
    measure_one = stream.Measure(number=1)
    measure_one.append(chord.Chord(["C4", "E4", "G4"], quarterLength=2))
    measure_one.append(chord.Chord(["G3", "B3", "D4"], quarterLength=2))
    measure_two = stream.Measure(number=2)
    measure_two.append(note.Note("C4", quarterLength=4))
    part.append(measure_one)
    part.append(measure_two)
    score.append(part)
    return score


def test_music21_light_backend_returns_event_rows():
    if chord is None or meter is None or note is None or stream is None:
        raise unittest.SkipTest("music21 is not installed in this runtime.")
    analyzer = Music21LightRomanNumeralAnalyzer()
    result = analyzer.analyze_score(make_tiny_score(), score_id="tiny")

    assert result.backend_name == "music21_light"
    assert result.backend_available is True
    assert isinstance(result.events, list)
    assert result.events

    row = result.events[0].to_row()
    required_keys = {
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
    }
    assert required_keys.issubset(row)


def test_rnbert_adapter_reports_unavailable_cleanly(monkeypatch):
    from score_embedding_lab.roman_numeral_harmony.analyzers import rnbert as rnbert_module

    monkeypatch.setattr(rnbert_module, "find_spec", lambda name: None)
    analyzer = RNBertRomanNumeralAnalyzer()
    result = analyzer.analyze_score(make_tiny_score(), score_id="tiny")

    assert analyzer.is_available() is False
    assert result.backend_available is False
    assert result.success is False
    assert result.events == []
    assert any("stub" in warning.lower() for warning in result.warnings)


def test_feature_extraction_from_tiny_rn_event_table():
    score = None
    result = RomanNumeralAnalysisResult(
        score_id="tiny",
        backend_name="music21_light",
        backend_version="0.1",
        success=True,
        backend_available=True,
        global_key="C major",
        warnings=[],
        metadata={"pitch_class_set": [0, 2, 4, 5, 7, 9, 11]},
        events=[
            RomanNumeralEvent(
                score_id="tiny",
                backend_name="music21_light",
                backend_version="0.1",
                onset_quarter=0.0,
                duration_quarter=2.0,
                measure_number=1,
                beat=1.0,
                local_key="C major",
                global_key="C major",
                roman_numeral="I",
                figure="I",
                chord_root="C",
                bass_note="C",
                inversion="0",
                function_label="tonic",
                confidence=1.0,
                raw_label="I",
                warning_flags=(),
                pitch_classes=(0, 4, 7),
                root_pitch_class=0,
                bass_pitch_class=0,
                is_approximate=True,
            ),
            RomanNumeralEvent(
                score_id="tiny",
                backend_name="music21_light",
                backend_version="0.1",
                onset_quarter=2.0,
                duration_quarter=2.0,
                measure_number=1,
                beat=3.0,
                local_key="C major",
                global_key="C major",
                roman_numeral="V",
                figure="V",
                chord_root="G",
                bass_note="G",
                inversion="0",
                function_label="dominant",
                confidence=1.0,
                raw_label="V",
                warning_flags=(),
                pitch_classes=(2, 7, 11),
                root_pitch_class=7,
                bass_pitch_class=7,
                is_approximate=True,
            ),
        ],
    )

    features = extract_rn_harmony_features(score, result)

    assert features["experimental__rn_harmony__backend_available"] == 1.0
    assert features["experimental__rn_harmony__analysis_success"] == 1.0
    assert features["experimental__rn_harmony__rn_event_count"] == 2.0
    assert features["experimental__rn_harmony__dominant_function_ratio"] == 0.5
    assert all(key.startswith("experimental__") for key in features)
    assert all(value == value for value in features.values())


def test_empty_event_table_writes_stable_schema(tmp_path):
    rows = [
        {
            "score_id": "empty",
            "backend": "rnbert",
            "events": [],
        }
    ]
    output_paths = save_event_tables(rows, tmp_path)
    text = output_paths[0].read_text(encoding="utf-8")

    assert "score_id" in text
    assert "backend_name" in text
    assert "onset_quarter" in text
