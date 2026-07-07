# Feature Metadata

This directory holds the machine-readable metadata for the experimental musicological lane.

The current registry is:

- `experimental_features_v0.yml`

It documents the experimental proxy features, their family membership, the feature set they belong to, and the main caveats to keep in view during later evaluation.

The evaluation script reads this file when available, but the code also keeps a mirrored Python registry so the lane still works if YAML parsing is unavailable in a minimal environment.
