from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path

import numpy as np

CLAP_PROJECTION_DIM = 512


def _available_clap_backend() -> str | None:
    """Detect the CLAP backend supported by this scaffold."""
    try:
        __import__("laion_clap")
        return "laion-clap"
    except Exception:
        return None


@lru_cache(maxsize=1)
def _load_laion_clap_model():
    import laion_clap

    model = laion_clap.CLAP_Module(enable_fusion=False)
    model.load_ckpt()
    return model


def compute_clap_embeddings(audio_paths, backend: str | None = None) -> np.ndarray:
    """Compute CLAP embeddings for a batch of rendered audio files."""
    backend_name = backend or _available_clap_backend()
    if backend_name is None:
        raise NotImplementedError(
            "No CLAP backend is installed. Install laion-clap to enable audio embeddings, "
            "or use dummy_embedding_from_audio_path() for offline testing."
        )
    if backend_name != "laion-clap":
        raise NotImplementedError(f"Unsupported CLAP backend: {backend_name}")

    paths = [Path(path).expanduser() for path in audio_paths]
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"Audio file does not exist: {path}")

    if not paths:
        return np.zeros((0, CLAP_PROJECTION_DIM), dtype=np.float32)

    model = _load_laion_clap_model()
    filelist = [str(path) for path in paths]
    embeddings = model.get_audio_embedding_from_filelist(x=filelist, use_tensor=False)
    array = np.asarray(embeddings, dtype=np.float32)
    if array.ndim == 1:
        array = array.reshape(1, -1)
    return array


def compute_clap_embedding(audio_path: str | Path, backend: str | None = None) -> np.ndarray:
    """Compute a single CLAP embedding for one rendered audio file."""
    embeddings = compute_clap_embeddings([audio_path], backend=backend)
    if embeddings.shape[0] != 1:
        raise RuntimeError("Expected one embedding row for a single audio file.")
    return embeddings[0]


def dummy_embedding_from_audio_path(audio_path: str | Path, dim: int = 512) -> np.ndarray:
    """Deterministic placeholder embedding derived from the path string."""
    if dim <= 0:
        raise ValueError("dim must be positive")

    path = Path(audio_path)
    digest = hashlib.sha256(path.as_posix().encode("utf-8")).digest()
    seed = int.from_bytes(digest[:8], "big", signed=False)
    rng = np.random.default_rng(seed)
    vector = rng.standard_normal(dim).astype(np.float32)
    norm = float(np.linalg.norm(vector))
    if norm:
        vector /= norm
    return vector
