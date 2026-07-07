# full pieces

This folder holds the source MusicXML files already checked into the repo.

There are two useful corpus slices here:

- the canonical 10-piece Mozart/Chopin demo set below
- a larger Mozart-only pool under `mozart/` that can be used for expanded exploratory runs

The prefix extractor walks directories recursively, so you can point it at either the demo set or the full tree depending on the run you want.

| Composer | Piece | File |
| --- | --- | --- |
| Mozart | K.545 Sonata in C major, I | `mozart_1st-movement-allegro-from-piano-sonata-facile-c-major-kv-545-mvt1.musicxml` |
| Mozart | K.310 Sonata in A minor, I | `mozart_piano-sonata-a-minor-kv-310-300d-mvt1.musicxml` |
| Mozart | K.332 Sonata in F major, I | `mozart_piano-sonata-f-major-kv-332-300k-mvt1.musicxml` |
| Mozart | Rondo in A minor K.511 | `mozart_rondo-a-minor-kv-511-mvt1.musicxml` |
| Mozart | Fantasy in D minor K.397 | `mozart_fantasy-d-minor-kv-397-385g-mvt1.musicxml` |
| Chopin | Prelude Op. 28 No. 1 | `chopin_prelude-a-major-op.-28,7-mvt1.musicxml` |
| Chopin | Prelude Op. 28 No. 4 | `chopin_prelude-e-minor-op.-28,4-mvt1.musicxml` |
| Chopin | Prelude Op. 28 No. 6 | `chopin_prelude-b-minor-op.-28,6-mvt1.musicxml` |
| Chopin | Prelude Op. 28 No. 15, "Raindrop" | `chopin_prelude-raindrop-d-flat-major-op.-28,15-mvt1.musicxml` |
| Chopin | Nocturne Op. 9 No. 2 | `chopin_nocturne-e-flat-major-op.-9,2-mvt1.musicxml` |

To regenerate the canonical 10-piece prefix manifest, run:

```bash
python scripts/extract_prefix_excerpts.py --input-dir data/raw/full-pieces
```

To build a Mozart-expanded prefix manifest from the recursive Mozart tree, use:

```bash
python scripts/extract_prefix_excerpts.py --input-dir data/raw/full-pieces/mozart
```

The Mozart subtree currently contains 70 MusicXML files in this checkout, so the expanded run is much larger than the 10-piece demo.

Do not point the prefix extractor at the full `data/raw/full-pieces/` tree for the expanded run unless you first deduplicate source files. This checkout contains Mozart copies both at the top level and under `mozart/`, and the excerpt IDs are derived from filename stems.
