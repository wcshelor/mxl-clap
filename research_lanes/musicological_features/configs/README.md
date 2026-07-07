# Configs

This directory is reserved for experiment-specific configuration files.

The current experiment is intentionally lightweight, so the primary controls live on the script CLI:

- feature set selection
- input manifest / excerpt directory
- output paths
- embedding file paths
- metadata file path for the experimental feature registry

If this lane grows, add small config files here rather than changing the baseline pipeline.
