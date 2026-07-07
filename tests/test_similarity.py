from __future__ import annotations

import numpy as np
import pandas as pd

from score_embedding_lab.clap_embeddings import dummy_embedding_from_audio_path
from score_embedding_lab.similarity import cosine_similarity_matrix, feature_columns_for_families, pairwise_similarity_table


def test_cosine_similarity_matrix_shape_and_diagonal():
    vectors = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]], dtype=float)
    similarity = cosine_similarity_matrix(vectors)

    assert similarity.shape == (3, 3)
    assert np.allclose(np.diag(similarity), 1.0)
    assert np.isclose(similarity[0, 1], 0.0)


def test_dummy_embedding_is_deterministic():
    first = dummy_embedding_from_audio_path("example.wav", dim=32)
    second = dummy_embedding_from_audio_path("example.wav", dim=32)
    third = dummy_embedding_from_audio_path("other.wav", dim=32)

    assert np.allclose(first, second)
    assert not np.allclose(first, third)


def test_pairwise_similarity_table_includes_extra_families():
    ids = ["a", "b"]
    symbolic = np.array([[1.0, 0.5], [0.5, 1.0]], dtype=float)
    embedding = np.array([[1.0, 0.25], [0.25, 1.0]], dtype=float)
    extra = {"pitch_similarity": np.array([[1.0, 0.75], [0.75, 1.0]], dtype=float)}

    frame = pairwise_similarity_table(ids, symbolic, embedding, extra_similarity_matrices=extra)

    assert list(frame["pair_id"]) == ["a__b"]
    assert "pitch_similarity" in frame.columns
    assert frame.loc[0, "pitch_similarity"] == 0.75


def test_feature_columns_for_families_recognizes_experimental_prefixes():
    frame = pd.DataFrame(
        {
            "experimental__chromaticism__accidental_density": [0.1, 0.2],
            "experimental__texture__mean_notes_per_onset": [1.0, 2.0],
            "experimental__rhythm_phrase__duration_entropy": [0.5, 0.6],
            "experimental__harmony_light__triad_ratio": [0.7, 0.8],
            "experimental__harmony_heavy__tonic_ratio": [0.4, 0.3],
            "experimental__syntax_interaction__non_chord_tone_ratio": [0.2, 0.1],
        }
    )

    families = feature_columns_for_families(frame)

    assert families["experimental_chromaticism_similarity"] == ["experimental__chromaticism__accidental_density"]
    assert families["experimental_texture_similarity"] == ["experimental__texture__mean_notes_per_onset"]
    assert families["experimental_rhythm_phrase_similarity"] == ["experimental__rhythm_phrase__duration_entropy"]
    assert families["experimental_harmony_light_similarity"] == ["experimental__harmony_light__triad_ratio"]
    assert families["experimental_harmony_heavy_similarity"] == ["experimental__harmony_heavy__tonic_ratio"]
    assert families["experimental_syntax_interaction_similarity"] == ["experimental__syntax_interaction__non_chord_tone_ratio"]
    assert families["experimental_musicological_all_similarity"]
