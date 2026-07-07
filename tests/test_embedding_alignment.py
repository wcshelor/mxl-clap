from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from score_embedding_lab.embedding_alignment import reorder_embeddings_by_excerpt_id


def test_reorder_embeddings_by_excerpt_id_handles_superset_metadata():
    features = pd.DataFrame({"excerpt_id": ["b", "a"]})
    embeddings = np.asarray([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]], dtype=float)
    metadata = pd.DataFrame({"excerpt_id": ["a", "b", "c"]})

    ordered = reorder_embeddings_by_excerpt_id(features, embeddings, metadata)

    assert ordered.shape == (2, 2)
    assert np.allclose(ordered[0], [2.0, 2.0])
    assert np.allclose(ordered[1], [1.0, 1.0])


def test_reorder_embeddings_by_excerpt_id_reports_missing_ids():
    features = pd.DataFrame({"excerpt_id": ["a", "b"]})
    embeddings = np.asarray([[1.0, 1.0]], dtype=float)
    metadata = pd.DataFrame({"excerpt_id": ["a"]})

    with pytest.raises(ValueError, match="Matched 1 of 2 excerpt ids"):
        reorder_embeddings_by_excerpt_id(features, embeddings, metadata)
