from __future__ import annotations

import math

from music21 import meter, note, stream
from music21.chord import Chord

from score_embedding_lab.experimental_musicological import extract_experimental_musicological_feature_families
from score_embedding_lab.symbolic_features import extract_symbolic_features


def make_experimental_score():
    score = stream.Score()
    upper = stream.Part()
    lower = stream.Part()
    upper.append(meter.TimeSignature("4/4"))
    lower.append(meter.TimeSignature("4/4"))

    upper_measure_one = stream.Measure(number=1)
    upper_measure_one.append(Chord(["C4", "E4", "G4"], quarterLength=1))
    upper_measure_one.append(note.Rest(quarterLength=1))
    upper_measure_one.append(note.Note("D4", quarterLength=2))
    upper_measure_two = stream.Measure(number=2)
    upper_measure_two.append(note.Note("F#4", quarterLength=1))
    upper_measure_two.append(note.Note("G4", quarterLength=1))
    upper_measure_two.append(note.Note("A4", quarterLength=2))

    lower_measure_one = stream.Measure(number=1)
    lower_measure_one.append(note.Note("C3", quarterLength=2))
    lower_measure_one.append(note.Note("G2", quarterLength=2))
    lower_measure_two = stream.Measure(number=2)
    lower_measure_two.append(note.Note("C3", quarterLength=4))

    upper.append(upper_measure_one)
    upper.append(upper_measure_two)
    lower.append(lower_measure_one)
    lower.append(lower_measure_two)
    score.append(upper)
    score.append(lower)
    return score


def test_experimental_feature_families_return_dicts():
    families = extract_experimental_musicological_feature_families(make_experimental_score())

    assert set(families) == {
        "experimental_chromaticism",
        "experimental_texture",
        "experimental_rhythm_phrase",
        "experimental_harmony_light",
        "experimental_harmony_heavy",
        "experimental_syntax_interaction",
    }
    assert "experimental__chromaticism__accidental_density" in families["experimental_chromaticism"]
    assert "experimental__texture__mean_notes_per_onset" in families["experimental_texture"]
    assert "experimental__rhythm_phrase__duration_entropy" in families["experimental_rhythm_phrase"]
    assert "experimental__harmony_light__triad_ratio" in families["experimental_harmony_light"]
    assert "experimental__harmony_heavy__rn_backend_available" in families["experimental_harmony_heavy"]
    assert "experimental__syntax_interaction__non_chord_tone_ratio" in families["experimental_syntax_interaction"]
    assert "experimental__chromaticism__melodic_semitone_motion_ratio" in families["experimental_chromaticism"]
    assert "experimental__texture__left_right_register_gap_mean" in families["experimental_texture"]
    assert "experimental__rhythm_phrase__rest_punctuation_ratio" in families["experimental_rhythm_phrase"]
    assert "experimental__harmony_light__vertical_chromaticity_ratio" in families["experimental_harmony_light"]
    assert "experimental__harmony_heavy__cadence_like_V_I_count" in families["experimental_harmony_heavy"]
    assert "experimental__syntax_interaction__dissonance_on_strong_beat_ratio" in families["experimental_syntax_interaction"]
    assert all(math.isfinite(float(value)) for family in families.values() for value in family.values())
    assert all(key.startswith("experimental__") for family in families.values() for key in family)


def test_symbolic_feature_extraction_can_enable_experimental_sets():
    features = extract_symbolic_features(make_experimental_score(), feature_sets=["core", "experimental_musicological_all_v0"])

    assert "experimental__chromaticism__accidental_density" in features
    assert "experimental__texture__mean_notes_per_onset" in features
    assert "experimental__rhythm_phrase__duration_entropy" in features
    assert "experimental__harmony_light__triad_ratio" in features
    assert "experimental__harmony_heavy__rn_backend_available" in features
    assert "experimental__syntax_interaction__non_chord_tone_ratio" in features
    assert "experimental__chromaticism__melodic_semitone_motion_ratio" in features
    assert all(math.isfinite(float(value)) for value in features.values())


def test_missing_roman_numeral_backend_does_not_crash(monkeypatch):
    import score_embedding_lab.experimental_musicological as experimental_musicological

    def boom(_score):
        raise RuntimeError("backend missing")

    monkeypatch.setattr(experimental_musicological, "analyze_roman_numerals", boom)

    families = experimental_musicological.extract_experimental_musicological_feature_families(make_experimental_score())

    assert families["experimental_harmony_heavy"]["experimental__harmony_heavy__rn_backend_available"] == 0.0
    assert families["experimental_harmony_heavy"]["experimental__harmony_heavy__rn_event_count"] == 0.0
    assert families["experimental_harmony_heavy"]["experimental__harmony_heavy__tonic_ratio"] == 0.0
