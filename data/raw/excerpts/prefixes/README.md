# prefix excerpts

Generated first-N-measure excerpts for the ten-piece Mozart/Chopin experiment corpus land here.

For the current use case, `scripts/extract_prefix_excerpts.py` writes the first 32- and 64-measure `.mxl` excerpts for each source piece into this directory.
If a source piece is shorter than the requested length, the extractor clamps the excerpt and keeps the requested length in the file name so 32/64 rows stay unique.
See `../full-pieces/README.md` for the exact source list.
