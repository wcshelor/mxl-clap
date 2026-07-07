from __future__ import annotations

from music21 import meter, note, stream
from music21.chord import Chord

from score_embedding_lab.symbolic_features import extract_symbolic_features


def make_tiny_score():
    score = stream.Score()
    part = stream.Part()
    part.append(meter.TimeSignature("4/4"))
    part.append(Chord(["C4", "E4", "G4"], quarterLength=1))
    part.append(note.Note("D4", quarterLength=1))
    part.append(note.Note("F4", quarterLength=2))
    score.append(part)
    return score


def test_extract_symbolic_features_returns_expected_keys():
    features = extract_symbolic_features(make_tiny_score())
    core_only = extract_symbolic_features(make_tiny_score(), feature_sets=["core"])

    assert features["note_count"] == 5.0
    assert features["total_duration_quarter_lengths"] == 4.0
    assert features["note_density"] == 1.25
    assert "ambitus_semitones" in features
    assert "mean_pitch" in features
    assert "rhythmic_diversity" in features
    assert "chordified_chord_count" in features
    assert "pitch__pitch_class_entropy" in features
    assert "rhythm__duration_entropy" in features
    assert "texture__mean_notes_per_onset" in features
    assert "harmony__chordified_event_count" in features
    assert "metadata__part_count" in features
    pitch_hist_total = sum(value for key, value in features.items() if key.startswith("pitch_class_"))
    assert abs(pitch_hist_total - 1.0) < 1e-9
    assert features["texture__mean_notes_per_onset"] > 1.0
    assert features["harmony__chordified_event_count"] > 0
    assert features == core_only
