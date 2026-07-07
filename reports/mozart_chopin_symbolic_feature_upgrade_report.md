# Mozart/Chopin Symbolic Feature Upgrade Report

## What Changed

The symbolic feature space now separates pitch, rhythm, texture, harmony, and metadata-derived features. This makes it easier to see which musical dimensions actually move the similarity scores.

## Audit Snapshot

The upgraded symbolic CSV contains 163 numeric columns.

- 26 features are flagged as near-constant under the audit rule
- the flattest columns are mostly rare harmony/common-name bins and a few IOI bins
- the feature space is therefore much richer than the old flat CSV, but still sparse in the harmony layer

## Three Presentation Examples

| Pair | Symbolic Global | Pitch | Rhythm | Texture | Harmony | CLAP |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Chopin Prelude No. 4, 8 vs 16 measures | 0.986744 | 0.986277 | 0.939975 | 0.979133 | 0.999944 | 0.992023 |
| Chopin Prelude No. 4, 8 measures vs Mozart Sonata No. 8 in A minor, 16 measures | 0.985891 | 0.986507 | 0.763505 | 0.985809 | 0.999877 | 0.840731 |
| Chopin Prelude No. 1, 8 measures vs Chopin Prelude No. 4, 8 measures | 0.921179 | 0.910752 | 0.683678 | 0.986496 | 0.999857 | 0.499603 |

## Interpretation

### 1. Expected match

The Chopin Prelude No. 4 8 vs 16 measure pair is the clean baseline. Every feature family is high, and CLAP is also very high. This is the case where the symbolic and audio views agree most clearly.

### 2. Mozart-vs-Chopin near-match

The Chopin Prelude No. 4 8 measures vs Mozart Sonata No. 8 in A minor, 16 measures pair is the most useful cross-composer example. The pitch and texture families are still very high, and the overall symbolic score stays near ceiling, but rhythm drops more noticeably and CLAP is lower than the symbolic score would suggest.

This is a good reminder that very similar piano surface features can bridge the composer boundary even when the symbolic aggregate stays high.

### 3. Surprising mismatch

The Chopin Prelude No. 1 vs Prelude No. 4 comparison is the strongest mismatch. The symbolic global score is still high, and texture/harmony remain close to ceiling, but rhythm is substantially lower and CLAP drops much more sharply.

That pattern suggests the current symbolic aggregate still overweights broad pitch/texture similarity and underweights rhythmic profile, phrasing, and temporal contour. In other words, the new feature families help explain why the old symbolic score was too compressed.

## What the Family Scores Say

- `pitch_similarity` is still very high across almost everything, so pitch alone does not separate the excerpts well.
- `texture_similarity` is also near ceiling for most pairs, which means the excerpted piano writing is broadly similar at the onset/chord level.
- `rhythm_similarity` is the most informative family in this tiny demo. It is the main place where the more similar-looking pairs start to separate from the more surprising ones.
- `harmony_similarity` is effectively saturated here because the chordify-based layer is too coarse for these short excerpts.

## Conclusion

The feature upgrade improves interpretability more than it improves separation. The old global symbolic score was too flat; the new family scores show that rhythm is carrying the most useful contrast, while pitch, texture, and harmony are still close to ceiling on this miniature corpus.

That means the current symbolic features are now good enough for a proof-of-concept comparison with CLAP, but they still need more rhythmic detail and a less saturated harmony layer before they can be treated as a serious analytical representation.
