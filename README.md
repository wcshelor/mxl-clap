# mxl-clap

This is a tiny exploratory scaffold for comparing symbolic MusicXML-derived score features with audio embeddings, especially CLAP-style embeddings, and using an LLM to generate musicological explanations of similarities between short score excerpts.

The project sits between symbolic computational musicology and modern audio-language embeddings. It is intentionally small and readable, and it does not claim that CLAP "understands" music.

For repository-wide agent guidance, see [AGENTS.md](./AGENTS.md).

## Research Question

Can audio embeddings of rendered score excerpts be related back to symbolic MusicXML features, and can an LLM generate plausible musicological explanations of the similarities and differences?

## Intended Pipeline

```text
MusicXML / MXL full piece
    -> deterministic measure excerpting
    -> symbolic feature extraction
    -> piano MIDI / WAV rendering
    -> CLAP / audio embedding
    -> similarity matrices
    -> LLM explanation table
```

## Tiny First Experiment

Start with the ten-piece Mozart/Chopin corpus documented in [data/raw/full-pieces/README.md](./data/raw/full-pieces/README.md). Keep `data/raw/full-pieces/` limited to those files when running the demo.

1. Put those full `.xml`, `.musicxml`, or `.mxl` files in `data/raw/full-pieces/`.
2. For the first 32 and 64 measures of each source piece, run:
   ```bash
   python scripts/extract_prefix_excerpts.py
   ```
   This writes one 32-measure and one 64-measure `.mxl` prefix excerpt per source piece, clamping shorter pieces to their available length and keeping clamped request lengths distinct in the file names.
3. Run deterministic excerpt extraction into `data/raw/excerpts/generated/` if you want sliding windows instead of prefixes.
4. Run symbolic feature extraction on the generated excerpts.
5. Audit the symbolic feature CSV to check which features are near-constant.
6. Render each excerpt to piano MIDI and WAV.
7. Compute CLAP embeddings from the rendered WAV files, or use the dummy backend first to verify the pipeline wiring.
8. Compare pairwise symbolic similarity, family-specific symbolic similarities, and embedding similarity.
9. Generate a Markdown table that can be pasted into an LLM prompt.

## Experimental Musicological Lane

The default symbolic pipeline stays `core` only. If you want to test a separate experimental lane with musicologically motivated proxies, use the research lane under `research_lanes/musicological_features/`.

Example commands:

```bash
python scripts/extract_symbolic_features.py --feature-sets core
python scripts/extract_symbolic_features.py --feature-sets core,experimental_texture_v0
python scripts/extract_symbolic_features.py --feature-sets core,experimental_musicological_all_v0
python research_lanes/musicological_features/scripts/run_musicological_feature_experiment.py --feature-sets core,experimental_musicological_all_v0
python research_lanes/musicological_features/scripts/evaluate_experimental_features.py
```

The experimental lane is intentionally narrow:

- it keeps the baseline symbolic pipeline intact
- it adds optional feature sets for chromaticism, texture, rhythm/phrase regularity, light harmony, heavy harmony, and syntax-interaction proxies
- it writes separate pairwise, audit, correlation, and family-summary outputs
- it treats the resulting comparison as hypothesis-generating only
- it reuses the same ten-piece Mozart/Chopin prefix excerpts as the rest of the demo

If you want to use the larger Mozart pool already present in the repo, use the checked-in manifest at `data/processed/prefix_excerpt_manifest_mozart.csv` and the matching excerpts under `data/raw/excerpts/prefixes_mozart/`. You only need to regenerate them if you change the source pieces.

```bash
python scripts/render_audio.py --manifest data/processed/prefix_excerpt_manifest_mozart.csv --excerpt-dir data/raw/excerpts/prefixes_mozart --manifest-output data/processed/audio_manifest_mozart.csv --midi-dir data/processed/midi/mozart_expanded --audio-dir data/processed/audio/mozart_expanded
python scripts/compute_embeddings.py --manifest data/processed/audio_manifest_mozart.csv --output-dir data/processed/embeddings/mozart_expanded
python research_lanes/musicological_features/scripts/run_musicological_feature_experiment.py --manifest data/processed/prefix_excerpt_manifest_mozart.csv --feature-sets core,experimental_musicological_all_v0 --embeddings data/processed/embeddings/mozart_expanded/audio_embeddings.npy --embedding-metadata data/processed/embeddings/mozart_expanded/embedding_metadata.csv
```

That gives you a Mozart-heavy exploratory run without changing the repo’s checked-in data.

If you want one combined Mozart + Chopin corpus, build a curated manifest rather than pointing the extractor at the entire `data/raw/full-pieces/` tree, because the tree contains duplicate Mozart filenames at multiple locations.

## Roman Numeral Harmony Lane

There is a separate experimental lane for Roman numeral and functional harmony analysis under `research_lanes/roman_numeral_harmony/`.

It is intentionally separate from the current symbolic pipeline and uses an adapter-based backend design so the default `music21_light` analysis can run without any heavy model dependency.

Use this lane when you want to inspect:

- Roman numeral syntax
- harmonic rhythm and cadence-like motion
- texture and melody interactions with harmony
- pairwise similarity derived from Roman numeral features

The intended workflow is:

1. Run the light backend first.
2. Inspect the cached event tables in `research_lanes/roman_numeral_harmony/cache/<run_id>/events/`.
3. Evaluate the features in `research_lanes/roman_numeral_harmony/reports/`.
4. Only then try an optional RNBert or MusicBERT-style backend if you have a separate environment or checkpoint.

## Non-Goals

- No training.
- No claim of music understanding.
- No large benchmark.
- No automatic musicological truth claims.
- No vendored CLAP checkpoints.
- No vendored piano soundfonts.

## Project Layout

- `environment.yml`: Conda/Mamba environment definition.
- `pyproject.toml`: Python package metadata and build configuration.
- `src/score_embedding_lab/`: core Python package.
- `scripts/`: small CLI-style utilities.
- `data/raw/full-pieces/`: source MusicXML/MXL pieces.
- `data/raw/excerpts/prefixes/`: generated first-N-measure excerpts.
- `data/raw/excerpts/generated/`: generated excerpt files.
- `data/processed/`: generated CSV, NPY, MIDI, and WAV artifacts.
- `reports/`: generated Markdown summaries.
- `research_lanes/musicological_features/`: experimental lane for musicologically motivated symbolic features.
- `research_lanes/musicological_features/feature_metadata/`: machine-readable experimental feature metadata.
- `research_lanes/roman_numeral_harmony/`: experimental Roman numeral / functional harmony lane.
- `research_lanes/roman_numeral_harmony/feature_metadata/`: machine-readable metadata for the Roman numeral lane.
- `external/mxl-toolbox/`: optional external checkout or vendored toolbox.

## Quick Start

Create the environment with Mamba or Conda:

```bash
mamba env create -f environment.yml
conda activate mxl-clap
python -m pip install -e .
```

Generate excerpts and run the pipeline:

```bash
python scripts/extract_excerpts.py
python scripts/extract_symbolic_features.py
python scripts/audit_symbolic_features.py
python -m pip install laion-clap
export MXL_CLAP_SOUND_FONT=/path/to/acoustic-grand.sf2
python scripts/render_audio.py
python scripts/compute_embeddings.py
python scripts/compare_excerpts.py
python scripts/make_llm_prompt_table.py
```

If you only want a no-model smoke test, run `python scripts/compute_embeddings.py --backend dummy`. The real CLAP path uses `laion-clap` and downloads its checkpoint the first time it runs.

For a pure dummy-backend run, the embedding script also accepts directory-style output:

```bash
python scripts/compute_embeddings.py \
  --audio-dir data/processed/audio/mozart_chopin_demo \
  --backend dummy \
  --output-dir data/processed/embeddings/mozart_chopin_demo
```

That writes `audio_embeddings.npy` and `embedding_metadata.csv` into the output directory.

## External Prerequisites

- `fluidsynth` must be installed and available on `PATH`.
- A General MIDI soundfont (`.sf2`) must be available locally if you want to render MIDI to WAV or compute new audio embeddings.
- Point the renderer at it with `--soundfont /absolute/path/to/file.sf2` or set `MXL_CLAP_SOUND_FONT=/absolute/path/to/file.sf2` in your shell. The code also accepts the alias `MXL_CLAP_SOUNDFONT`.
- If MusicXML repeat markup is malformed, the MIDI writer falls back to a flattened score so rendering can still proceed.
- The CLAP backend is not vendored. Install `laion-clap` in the environment before using `scripts/compute_embeddings.py` with the default backend.
- The dummy backend is available without CLAP and is intended for end-to-end pipeline smoke tests.
- `scripts/compare_excerpts.py` now writes family-specific similarity columns alongside the global score.
- `scripts/extract_symbolic_features.py` accepts `--feature-sets core` and optional experimental feature sets.
- `research_lanes/musicological_features/scripts/run_musicological_feature_experiment.py` defaults to the shared prefix excerpt manifest for the ten-piece Mozart/Chopin corpus and stays core-only unless you pass experimental feature sets.
- `research_lanes/roman_numeral_harmony/scripts/run_rn_harmony_experiment.py` defaults to the light backend and writes inspectable Roman numeral event caches plus family-specific similarity outputs.
- `scripts/extract_prefix_excerpts.py` already supports longer prefix lengths such as `32` and `64`; shorter pieces are clamped to their available measure count.

## External MXL Toolbox

If you have the separate MXL toolbox, clone it into `external/mxl-toolbox/`. The first implementation in this repo uses a `music21` fallback and does not assume the toolbox is present.
