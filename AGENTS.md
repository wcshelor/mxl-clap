# AGENTS

This repository is small on purpose. Agents working here should keep the documentation unusually explicit and current.

## Priority

Documentation is part of the deliverable, not an afterthought.

When code, scripts, file layouts, environment setup, or assumptions change, update the docs in the same change whenever possible.

## Required behavior

- Keep `README.md` detailed, accurate, and easy to follow.
- Keep setup instructions aligned with the actual environment file and package metadata.
- Prefer concrete commands, file paths, and caveats over vague summaries.
- Keep non-goals and limitations visible so the project does not drift into overclaiming.
- Update examples and expected outputs when behavior changes.
- If a workflow changes, update the relevant script docstrings and inline comments too.
- When environment state matters, prefer asking the user to run terminal commands and paste the output instead of assuming the local runtime matches the repo instructions.
- Do not spend time trying to guess missing dependencies or interpreter details when the user can provide the command output directly.

## Editing standard

- Treat stale documentation as a bug.
- Favor short, direct explanations, but do not omit important setup or limitation details.
- If a change affects reproducibility, note the exact command or file involved.

## Current setup files

- `environment.yml` is the Conda/Mamba environment entrypoint.
- `pyproject.toml` is the Python package metadata and build configuration.
- `README.md` should point to both.
