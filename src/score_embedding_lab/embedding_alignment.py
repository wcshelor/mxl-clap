from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


def reorder_embeddings_by_excerpt_id(
    features: pd.DataFrame,
    embeddings: np.ndarray,
    metadata: pd.DataFrame | None,
    *,
    feature_id_column: str = "excerpt_id",
    metadata_id_column: str = "excerpt_id",
) -> np.ndarray:
    if features.empty:
        return np.zeros((0, embeddings.shape[1] if embeddings.ndim == 2 else 0), dtype=float)

    if embeddings.ndim == 1:
        embeddings = embeddings.reshape(1, -1)

    if metadata is None or metadata.empty or feature_id_column not in features.columns or metadata_id_column not in metadata.columns:
        if len(embeddings) != len(features):
            raise ValueError(
                "Embedding matrix row count does not match the feature rows. "
                "Use embeddings computed from the same manifest as the feature table."
            )
        return embeddings

    if len(metadata) != len(embeddings):
        raise ValueError(
            f"Embedding metadata row count ({len(metadata)}) does not match the embedding matrix row count ({len(embeddings)}). "
            "The metadata CSV must be produced from the same embedding run as the NPY file."
        )

    lookup = {
        str(row[metadata_id_column]): np.asarray(embeddings[i], dtype=float)
        for i, row in metadata.reset_index(drop=True).iterrows()
    }
    feature_ids = [str(excerpt_id) for excerpt_id in features[feature_id_column].astype(str).tolist()]
    ordered: list[np.ndarray] = []
    missing_feature_ids: list[str] = []
    for excerpt_id in feature_ids:
        embedding = lookup.get(excerpt_id)
        if embedding is None:
            missing_feature_ids.append(excerpt_id)
        else:
            ordered.append(embedding)

    if missing_feature_ids:
        feature_id_set = set(feature_ids)
        extra_metadata_ids = [excerpt_id for excerpt_id in lookup if excerpt_id not in feature_id_set]
        raise ValueError(
            "Embedding metadata does not align with the feature rows. "
            f"Matched {len(feature_ids) - len(missing_feature_ids)} of {len(feature_ids)} excerpt ids. "
            f"Missing feature ids (first 10): {missing_feature_ids[:10]}. "
            f"Extra embedding ids (first 10): {extra_metadata_ids[:10]}. "
            "Generate embeddings from the same manifest/audio manifest that produced the features, "
            "or pass the matching --embeddings and --embedding-metadata files for this corpus."
        )

    return np.vstack(ordered)
