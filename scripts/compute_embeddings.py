from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from score_embedding_lab.clap_embeddings import compute_clap_embeddings, dummy_embedding_from_audio_path
from score_embedding_lab.config import AUDIO_MANIFEST, DATA_AUDIO_DIR, DATA_PROCESSED
from score_embedding_lab.io import list_audio_paths


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compute embeddings for rendered audio excerpts.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=AUDIO_MANIFEST,
        help="Audio manifest produced by scripts/render_audio.py.",
    )
    parser.add_argument(
        "--audio-dir",
        type=Path,
        default=DATA_AUDIO_DIR,
        help="Fallback directory containing rendered WAV files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Directory for the embedding outputs. If set, writes audio_embeddings.npy and "
            "embedding_metadata.csv inside the directory."
        ),
    )
    parser.add_argument(
        "--backend",
        choices=["dummy", "laion-clap"],
        default="laion-clap",
        help="Embedding backend to use.",
    )
    parser.add_argument("--dim", type=int, default=512, help="Embedding dimension for dummy vectors.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_PROCESSED / "audio_embeddings.npy",
        help="NPY file for the embedding matrix.",
    )
    parser.add_argument(
        "--metadata-output",
        type=Path,
        default=DATA_PROCESSED / "audio_embeddings_metadata.csv",
        help="CSV file for embedding metadata.",
    )
    return parser


def _load_audio_rows(args: argparse.Namespace) -> tuple[list[Path], list[dict[str, object]]]:
    if args.audio_dir != DATA_AUDIO_DIR:
        audio_paths = list_audio_paths(args.audio_dir)
        if audio_paths:
            rows = [
                {
                    "excerpt_id": path.stem,
                    "audio_path": str(path),
                    "audio_file": path.name,
                }
                for path in audio_paths
            ]
            return audio_paths, rows

    if args.manifest.exists():
        frame = pd.read_csv(args.manifest)
        if frame.empty:
            return [], []

        audio_paths: list[Path] = []
        rows: list[dict[str, object]] = []
        for _, manifest_row in frame.iterrows():
            audio_path_value = manifest_row.get("audio_path", "")
            if isinstance(audio_path_value, str) and audio_path_value:
                audio_path = Path(audio_path_value)
            else:
                excerpt_id = str(manifest_row.get("excerpt_id", "")).strip()
                if not excerpt_id:
                    continue
                audio_path = args.audio_dir / f"{excerpt_id}.wav"

            audio_paths.append(audio_path)
            rows.append(manifest_row.to_dict())
        return audio_paths, rows

    audio_paths = list_audio_paths(args.audio_dir)
    rows = [
        {
            "excerpt_id": path.stem,
            "audio_path": str(path),
            "audio_file": path.name,
        }
        for path in audio_paths
    ]
    return audio_paths, rows


def _compute_embeddings(audio_paths: list[Path], backend: str, dim: int) -> np.ndarray:
    for path in audio_paths:
        if not path.exists():
            raise FileNotFoundError(f"Audio file does not exist: {path}")

    if not audio_paths:
        if backend == "dummy":
            return np.zeros((0, dim), dtype=np.float32)
        return np.zeros((0, 512), dtype=np.float32)

    if backend == "dummy":
        vectors = [dummy_embedding_from_audio_path(path, dim=dim) for path in audio_paths]
        return np.vstack(vectors)

    return compute_clap_embeddings(audio_paths, backend=backend)


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    if args.output_dir is not None:
        args.output = args.output_dir / "audio_embeddings.npy"
        args.metadata_output = args.output_dir / "embedding_metadata.csv"
    audio_paths, metadata_rows = _load_audio_rows(args)

    try:
        embeddings = _compute_embeddings(audio_paths, args.backend, args.dim)
    except (FileNotFoundError, NotImplementedError, RuntimeError, ValueError) as exc:
        raise SystemExit(str(exc))

    metadata_rows_out: list[dict[str, object]] = []
    for index, (row, audio_path) in enumerate(zip(metadata_rows, audio_paths)):
        embedding = embeddings[index]
        updated_row = dict(row)
        updated_row.update(
            {
                "embedding_backend": args.backend,
                "embedding_source_path": str(audio_path),
                "embedding_dim": int(len(embedding)),
            }
        )
        metadata_rows_out.append(updated_row)

    if metadata_rows_out:
        metadata_frame = pd.DataFrame(metadata_rows_out)
    else:
        metadata_frame = pd.DataFrame(
            columns=list(metadata_rows[0].keys()) + ["embedding_backend", "embedding_source_path", "embedding_dim"]
            if metadata_rows
            else ["excerpt_id", "audio_path", "audio_file", "embedding_backend", "embedding_source_path", "embedding_dim"]
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.metadata_output.parent.mkdir(parents=True, exist_ok=True)
    np.save(args.output, embeddings.astype(np.float32, copy=False))
    metadata_frame.to_csv(args.metadata_output, index=False)
    print(f"Wrote embeddings with shape {embeddings.shape} to {args.output}")
    print(f"Wrote metadata rows to {args.metadata_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
