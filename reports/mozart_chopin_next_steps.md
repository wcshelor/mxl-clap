# Mozart/Chopin Next Steps

1. Add a small plotting script for a `symbolic_similarity` vs `embedding_similarity` scatterplot, colored by within-composer vs cross-composer pairs.
2. Add a heatmap figure for the CLAP pairwise matrix so the strongest and weakest pairings are visible at a glance.
3. Add explicit style metadata to the excerpt manifests and pairwise table, including a `style_period` field if the corpus supports it.
4. Compare the real CLAP outputs against the dummy backend on the same excerpt set so the report can separate pipeline wiring from embedding behavior.
5. Expand the excerpt set with more Mozart and Chopin movements, or alternate measure ranges, to see whether the current tendencies survive beyond the current ten-piece corpus.

## Optional presentation work

- Add a one-slide summary with three examples: expected match, cross-composer near-match, and symbolic-vs-CLAP mismatch.
- Add a short note explaining that the current symbolic feature set is coarse and should not be treated as a benchmark-level analysis.
