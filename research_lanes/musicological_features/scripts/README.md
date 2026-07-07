# Scripts

This directory contains the lane-specific drivers for the experimental musicological feature workflow.

The main entry points are:

- `run_musicological_feature_experiment.py`
- `evaluate_experimental_features.py`

`run_musicological_feature_experiment.py` reuses the shared symbolic extractor, computes family-specific similarities, and writes the feature table, pairwise similarity table, audit, correlation, family summary, and Markdown report.

`evaluate_experimental_features.py` re-evaluates an existing feature table and pairwise table, which is useful when you want to regenerate the analysis tables without rerunning the full extraction pipeline.
