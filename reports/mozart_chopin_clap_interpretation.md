# Mozart/Chopin CLAP Interpretation

## Scope

This is a tiny proof-of-concept, not a benchmark. The analysis uses an earlier 8-excerpt run:

- 2 Mozart excerpts
- 2 Chopin excerpts
- each excerpt present at 8-measure and 16-measure lengths
- this is legacy output; rerun the pipeline for the current 32-measure and 64-measure workflow

The CLAP backend recorded in the embedding metadata is `laion-clap` with 512-dimensional embeddings.

## Sanity Checks

- `symbolic_features_mozart_chopin.csv` has 8 rows and 8 unique excerpt IDs.
- `embedding_metadata.csv` has 8 rows and 8 unique excerpt IDs.
- `pairwise_similarity_mozart_chopin.csv` has 28 rows, which matches the expected `8 choose 2`.
- There are no missing values in the pairwise table.
- The pairwise table preserves `title_a/b` and `composer_a/b`.
- `style_period` is not present in the current outputs, so this report can only compare composer/title level metadata.
- Similarity values are not identical across pairs, so the output is not degenerate.

## What the Numbers Suggest

### Within-composer vs cross-composer

The averages are close:

- within-composer mean symbolic similarity: `0.946`
- within-composer mean CLAP similarity: `0.777`
- cross-composer mean symbolic similarity: `0.950`
- cross-composer mean CLAP similarity: `0.753`

Interpretation:

- The symbolic feature space is very coarse here. Almost everything is highly similar, so it does not separate Mozart from Chopin cleanly.
- CLAP shows a modest tendency to keep same-composer pairs higher than cross-composer pairs, but the gap is small.
- The strongest signal is not "Mozart vs Chopin" as a composer label; it is broad solo-piano texture, density, and register.

### Agreement between symbolic and CLAP similarity

There is one clear high-agreement region:

- same-piece 8 vs 16 measure pairs are always near the top
- the highest pair is Chopin Prelude No. 4, 8 vs 16 measures: symbolic `0.988`, CLAP `0.992`
- Mozart's 8 vs 16 pairs are also high: symbolic around `0.953-0.970`, CLAP around `0.923-0.946`

Where the measures diverge:

- several pairs have symbolic similarity above `0.95` but CLAP only in the `0.64-0.84` range
- one Chopin pair is especially striking: A major Prelude 8 measures vs E minor Prelude 8 measures has symbolic `0.914` but CLAP `0.500`

Musically, that kind of mismatch is plausible because the symbolic feature vector is dominated by broad counts and distributions, while CLAP is hearing the rendered audio surface. In this dataset, the embedding seems more sensitive to:

- texture density
- register
- rhythmic profile
- accompaniment figuration
- how "thick" the piano render sounds

### Broad Mozart/Chopin interpretation

The excerpts are too few for a firm stylistic conclusion, but the features do support a cautious reading:

- The Mozart excerpts include lighter, more periodic, and somewhat more diatonic-feeling material.
- The Chopin excerpts include denser piano writing, larger spans, and more overtly Romantic surface motion.
- CLAP does not simply collapse these into a composer label. It still treats some cross-composer piano excerpts as relatively similar when the rendered surface is similar.

That means the experiment is useful as a bridge between symbolic features and audio embeddings, but not as evidence that CLAP "understands" style in a musicological sense.

## Best Presentation Examples

| Pair | Symbolic | CLAP | Why it matters |
| --- | ---: | ---: | --- |
| Chopin Prelude No. 4, 8 vs 16 measures | `0.988` | `0.992` | Clean expected match. Same piece, same composer, same sonic profile. Good slide opener because both symbolic and audio views agree. |
| Chopin Prelude No. 4, 8 measures vs Mozart Sonata No. 8 in A minor, 16 measures | `0.987` | `0.841` | Strong Mozart-vs-Chopin contrast that still sounds surprisingly close in CLAP space. Useful for showing that surface piano texture can outweigh composer identity. |
| Chopin Prelude No. 1, 8 measures vs Chopin Prelude No. 4, 8 measures | `0.914` | `0.500` | Interesting mismatch. Symbolic counts still see both as broadly similar short piano excerpts, but CLAP separates them much more strongly. Good example of audio-embedding sensitivity to actual rendered texture. |

## Recommended Visualization

The easiest useful figure is a scatterplot of `symbolic_similarity` vs `embedding_similarity`, with points colored by within-composer vs cross-composer pairs.

Optional second figure:

- a clustered heatmap of CLAP similarities ordered by composer and excerpt length

## Conclusion

CLAP similarity does show some musically meaningful grouping, but only at a coarse level.

What agrees:

- same-piece halves are consistently close
- some same-composer piano excerpts remain high in both symbolic and CLAP space

What diverges:

- symbolic similarity is uniformly high and compresses many distinctions
- CLAP is more sensitive to the rendered audio surface than to the symbolic feature counts
- some pairs that look very close symbolically are not especially close in embedding space

Next step: add richer symbolic features and a small visualization script, then repeat the comparison with more excerpts and a broader set of measures. That would make it easier to tell whether CLAP is tracking style, texture, or just general solo-piano similarity.
