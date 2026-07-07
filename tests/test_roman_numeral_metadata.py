from __future__ import annotations

from pathlib import Path

import yaml

from score_embedding_lab.roman_numeral_harmony.analyzers.music21_light import Music21LightRomanNumeralAnalyzer
from score_embedding_lab.roman_numeral_harmony.features import extract_rn_harmony_features
from score_embedding_lab.roman_numeral_harmony.models import RomanNumeralAnalysisResult, RomanNumeralEvent


def test_metadata_contains_all_implemented_rn_feature_keys():
    metadata_path = Path(__file__).resolve().parents[1] / "research_lanes" / "roman_numeral_harmony" / "feature_metadata" / "experimental_rn_harmony_features_v0.yml"
    metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))

    result = RomanNumeralAnalysisResult(
        score_id="tiny",
        backend_name="music21_light",
        backend_version="0.1",
        success=True,
        backend_available=True,
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
            )
        ],
    )
    features = extract_rn_harmony_features(None, result)
    feature_keys = [key for key in features if key.startswith("experimental__")]

    for key in feature_keys:
        assert key in metadata
