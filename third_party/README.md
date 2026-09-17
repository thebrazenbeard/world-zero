# World Zero third-party dependency bundles

World Zero keeps dependency resolution and dependency availability as separate evidence.

`pyproject.toml` declares the direct dependency contract. `uv.lock` will record the exact connected resolution. Platform-specific wheelhouses under `third_party/wheels/` provide install artifacts when package indexes are unavailable.

Required qualification targets are `cp312-win_amd64` and `cp312-manylinux_x86_64`. CPython 3.13 bundles are compatibility subjects, not substitutes for CPython 3.12 qualification.

A wheelhouse is not trusted merely because files exist. Its `MANIFEST.json` must pass `python -m tools.verify_wheelhouse <wheelhouse>`, and an offline qualification must install into a fresh virtual environment using `python -m tools.bootstrap_offline --wheelhouse <wheelhouse> --venv <path>`.

The offline bootstrap uses pip with both `--no-index` and `--no-cache-dir`; successful installation therefore cannot silently rely on PyPI or a warm pip cache.
