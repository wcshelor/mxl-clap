from __future__ import annotations

from pathlib import Path

from score_embedding_lab.feature_registry import (
    EXPERIMENTAL_FEATURE_METADATA,
    experimental_families_for_feature_sets,
    normalize_feature_sets,
)


def test_metadata_yaml_contains_all_experimental_feature_keys():
    metadata_path = Path(__file__).resolve().parents[1] / "research_lanes" / "musicological_features" / "feature_metadata" / "experimental_features_v0.yml"
    text = metadata_path.read_text(encoding="utf-8")

    assert metadata_path.exists()
    for feature_name in EXPERIMENTAL_FEATURE_METADATA:
        assert feature_name in text


def test_musicological_all_feature_set_normalizes_to_core_plus_experimental_sets():
    feature_sets = normalize_feature_sets("core,experimental_musicological_all_v0")

    assert feature_sets[0] == "core"
    assert "experimental_musicological_all_v0" in feature_sets


def test_musicological_all_feature_set_expands_to_all_families():
    families = experimental_families_for_feature_sets("core,experimental_musicological_all_v0")

    assert families == (
        "experimental_chromaticism",
        "experimental_texture",
        "experimental_rhythm_phrase",
        "experimental_harmony_light",
        "experimental_harmony_heavy",
        "experimental_syntax_interaction",
    )
