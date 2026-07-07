# Musicological Features Research Lane

This lane is experimental.

It does not replace the baseline symbolic pipeline in `scripts/extract_symbolic_features.py`. The default behavior in the main pipeline remains `core` only.

The goal here is hypothesis generation: compare the current computational symbolic baseline against a modular set of musicologically motivated proxy features and see which families spread the Mozart/Chopin demo corpus more clearly.

This lane reuses the same ten-piece Mozart/Chopin prefix corpus as the rest of the demo. The exact source list lives in [data/raw/full-pieces/README.md](../../data/raw/full-pieces/README.md), and the default prefix excerpt manifest is expected to come from those files rather than a separate excerpting pass.

## Corpus

| Composer | Pieces |
| --- | --- |
| Mozart | K.545 Sonata in C major, I; K.310 Sonata in A minor, I; K.332 Sonata in F major, I; Rondo in A minor K.511; Fantasy in D minor K.397 |
| Chopin | Prelude Op. 28 No. 1; Prelude Op. 28 No. 4; Prelude Op. 28 No. 6; Prelude Op. 28 No. 15, "Raindrop"; Nocturne Op. 9 No. 2 |

## Working Hypothesis

The main comparison target is the familiar Classical-versus-Romantic contrast:

- Mozart / Classical clarity, regularity, and tonal restraint
- Chopin / Romantic chromatic, textural, and harmonic expansion

The features in this lane are proxies, not claims of objective musicological truth. They are meant to be read as rough measurements that may help explain a tiny demo set, not as a composer-classification system.

## Feature Sets

The current registry supports these feature sets:

- `core`
- `experimental_chromaticism_v0`
- `experimental_texture_v0`
- `experimental_rhythm_phrase_v0`
- `experimental_harmony_light_v0`
- `experimental_harmony_heavy_v0`
- `experimental_syntax_interaction_v0`
- `experimental_musicological_all_v0`

Legacy aliases such as `experimental_musicological_v0` are still accepted, but the canonical lane now uses the family-specific names above.

## Outputs

The lane scripts write their outputs under `research_lanes/musicological_features/reports/`:

- `mozart_chopin_experimental_features.csv`
- `mozart_chopin_experimental_features_pairwise.csv`
- `mozart_chopin_experimental_features_report.md`
- `feature_audit.csv`
- `feature_embedding_correlations.csv`
- `family_summary.csv`

The metadata registry lives under `research_lanes/musicological_features/feature_metadata/`:

- `experimental_features_v0.yml`

## Run

Core-only feature extraction:

```bash
python scripts/extract_symbolic_features.py --feature-sets core
```

Opt into one or more experimental families:

```bash
python scripts/extract_symbolic_features.py --feature-sets core,experimental_texture_v0
python scripts/extract_symbolic_features.py --feature-sets core,experimental_musicological_all_v0
```

Run the lane driver for the Mozart/Chopin prefix corpus:

```bash
python research_lanes/musicological_features/scripts/run_musicological_feature_experiment.py --feature-sets core,experimental_musicological_all_v0
```

If you want to use the larger Mozart pool that already exists in the repo, use the checked-in manifest at `data/processed/prefix_excerpt_manifest_mozart.csv` and the matching excerpts under `data/raw/excerpts/prefixes_mozart/`. Regenerate them only if you change the source pieces.

```bash
python scripts/render_audio.py --manifest data/processed/prefix_excerpt_manifest_mozart.csv --excerpt-dir data/raw/excerpts/prefixes_mozart --manifest-output data/processed/audio_manifest_mozart.csv --midi-dir data/processed/midi/mozart_expanded --audio-dir data/processed/audio/mozart_expanded
python scripts/compute_embeddings.py --manifest data/processed/audio_manifest_mozart.csv --output-dir data/processed/embeddings/mozart_expanded
python research_lanes/musicological_features/scripts/run_musicological_feature_experiment.py --manifest data/processed/prefix_excerpt_manifest_mozart.csv --feature-sets core,experimental_musicological_all_v0 --embeddings data/processed/embeddings/mozart_expanded/audio_embeddings.npy --embedding-metadata data/processed/embeddings/mozart_expanded/embedding_metadata.csv
```

Re-evaluate an existing feature table and pairwise similarity table:

```bash
python research_lanes/musicological_features/scripts/evaluate_experimental_features.py \
  --features research_lanes/musicological_features/reports/mozart_chopin_experimental_features.csv \
  --pairwise research_lanes/musicological_features/reports/mozart_chopin_experimental_features_pairwise.csv
```

If you need to regenerate the shared prefix excerpts, the current prefix extractor already supports 32- and 64-measure spans:

```bash
python scripts/extract_prefix_excerpts.py --prefix-lengths 32 64
```

When a source piece is shorter than the requested prefix length, the extractor clamps the excerpt to the available length and records the actual measure end in the manifest. Clamped prefix rows keep the requested length in the file name so the 32- and 64-measure entries remain distinct.

## Limits

- Tiny ten-piece demo set only.
- Proxy features only.
- No claim that these features recover composer intent or objective stylistic truth.
- Results should be treated as exploratory unless they hold up on a much larger and more varied corpus.
- Heavy harmony features are backend-dependent and currently use a `music21` Roman numeral adapter in this repo.
- If that analysis is unavailable or unstable, the heavy-harmony columns fall back to safe defaults and expose availability flags.
