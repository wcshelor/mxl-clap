# Roman Numeral Harmony Research Lane

This lane is experimental.

It is separate from the main symbolic pipeline and is intended for AI-assisted Roman numeral and functional harmony analysis on MusicXML/MXL scores.

The point of this lane is not to prove composer labels. It is to test whether harmony syntax, bass motion, texture, and melody-harmony relationships explain score similarity in a more interpretable way than the existing compressed symbolic baseline.

## Comparison Targets

This lane is designed to compare:

- core symbolic features
- lighter musicological features
- Roman numeral / functional harmony features
- CLAP embedding similarities

The outputs should be treated as exploratory, especially on short excerpts and chromatic piano textures.

## Backends

### Level 1: `music21_light`

This is the default backend.

It uses `music21` chordification plus Roman numeral utilities to generate approximate harmony events. It is intentionally lightweight and should run without any extra model dependencies.

### Level 2: `rnbert`

This is an optional backend adapter for RNBert or a HuggingFace MusicBERT/RNBert-style model.

The adapter in this repository is a stub. It keeps the interface and config wiring in place, but it does not ship a required model or inference stack. If the backend is unavailable, the lane should fall back to the lightweight backend or report the backend as unavailable without crashing the run.

### Level 3: future backends

The adapter interface is meant to allow future Roman numeral analyzers, annotated corpora, or manually corrected Roman numeral files to slot in later with minimal disruption.

## Outputs

The lane writes inspectable intermediate files into:

- `research_lanes/roman_numeral_harmony/cache/<run_id>/events/<score_id>__rn_events.csv`
- `research_lanes/roman_numeral_harmony/cache/<run_id>/run_manifest.json`

Final report artifacts are written under:

- `research_lanes/roman_numeral_harmony/reports/`

Feature names are prefixed with `experimental__`.

## Configuration

The default config is `configs/rn_harmony_default.yml`.

The optional RNBert config is `configs/rnbert_experimental.yml`.

Keep any extra model dependencies out of the main environment unless they are needed for the default backend.

## Run

Default light backend:

```bash
python research_lanes/roman_numeral_harmony/scripts/run_rn_harmony_experiment.py \
  --input-dir data/raw/full-pieces \
  --backend music21_light
```

Optional RNBert stub:

```bash
python research_lanes/roman_numeral_harmony/scripts/run_rn_harmony_experiment.py \
  --input-dir data/raw/full-pieces \
  --backend rnbert \
  --config research_lanes/roman_numeral_harmony/configs/rnbert_experimental.yml
```

If you want to compare against CLAP embeddings or existing symbolic similarities, pass those tables to the evaluation script after the run. The evaluation step is designed to remain optional.

## Limits

- Roman numeral outputs are model predictions, not ground truth.
- The `music21_light` backend is approximate.
- The `rnbert` backend is optional and currently a stub.
- Interaction features are heuristic alignments, not a substitute for annotated musicological analysis.
- These features are meant for hypothesis generation and manual inspection.
