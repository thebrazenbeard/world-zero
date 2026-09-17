# World Zero Offline Reconstructibility Design

Date: 2026-09-17
Status: approved architectural addendum
Applies to: `impl/scientific-spine-v2` and successor implementation branches

## Purpose

World Zero must remain testable and reconstructible when external Python package indexes are unreachable. A lock file alone is insufficient: it preserves dependency selection, not artifact availability. World Zero therefore treats dependency identity and dependency availability as separate requirements.

## Build-evidence rule

A verification result must bind at least:

- World Zero source commit/tree;
- Python implementation and exact version;
- operating system and architecture;
- dependency-lock digest;
- offline-bundle manifest digest when the offline path is used;
- test/lint/type-check tool versions;
- command/result evidence.

The existing scientific run receipts remain separate from build-environment evidence. A green build does not qualify a scientific model, and a scientific result does not prove the build is reconstructible.

## Python policy

- Canonical qualification runtime: CPython 3.12.
- Compatibility runtime: CPython 3.13 may be tested, but it does not silently substitute for a missing CPython-3.12 qualification.
- `pyproject.toml` may allow both 3.12 and 3.13 so development can proceed in available environments.
- Platform-specific offline bundles are keyed by Python ABI, operating system and architecture.

The earlier 28/28 scientific-spine test result was produced on CPython 3.13.5. It is retained as valid behavioral evidence for that environment only; it is not relabeled as a CPython-3.12 pass.

## Dependency authority

`pyproject.toml` declares direct project/development dependencies. `uv.lock` is the connected-resolution lock once generated and committed. Offline bundle manifests bind the actual install artifacts by filename, size and SHA-256.

These serve different purposes:

1. `pyproject.toml`: intended dependency contract.
2. `uv.lock`: exact resolved dependency graph.
3. `third_party/wheels/<target>/MANIFEST.json`: exact locally available artifacts.
4. offline bootstrap verification: proof that the bundle is sufficient without an index.

No one layer substitutes for another.

## Bundle layout

```text
third_party/
  wheels/
    cp312-win_amd64/
      MANIFEST.json
      *.whl
    cp312-manylinux_x86_64/
      MANIFEST.json
      *.whl
    cp313-win_amd64/
      MANIFEST.json
      *.whl            # optional compatibility bundle
    cp313-manylinux_x86_64/
      MANIFEST.json
      *.whl            # optional compatibility bundle
  README.md
```

The initial in-tree bundle is the small bootstrap/development set required to run the scientific-spine verification suite: runtime schema dependencies plus pytest, Ruff, mypy and their transitive dependencies. Large numerical/scientific dependencies such as NumPy, SciPy and pandas are admitted later as separate platform bundles when those dependencies enter executable code.

## Bootstrap policy

Plain Python plus pip is the lowest-level bootstrap path. It must not require `uv`, PyPI or a warm package-manager cache.

Canonical offline install shape:

```bash
python -m pip install \
  --no-index \
  --find-links third_party/wheels/<target> \
  -r third_party/wheels/<target>/requirements.lock
```

`uv` remains the preferred connected project manager and may itself be included in the bundle, but it is not the only route to reconstruct the environment.

## Manifest contract

Each bundle manifest records:

- schema version;
- bundle ID;
- target Python ABI;
- OS/platform tag and architecture;
- generation timestamp;
- source dependency-lock digest;
- every wheel filename;
- byte size;
- SHA-256;
- package name/version when determinable;
- bundle status (`CANDIDATE`, `VERIFIED_OFFLINE`, `SUPERSEDED`);
- verification receipt IDs.

Unknown or unverified fields remain explicit; they are never fabricated from filenames if the metadata cannot be validated.

## Offline verification

A bundle earns `VERIFIED_OFFLINE` only after a clean environment:

1. verifies every artifact hash;
2. installs using `--no-index` and the bundle only;
3. imports required runtime packages;
4. runs pytest;
5. runs Ruff;
6. runs mypy;
7. records exact interpreter/platform/tool versions;
8. proves no dependency was supplied by a pre-existing environment or package-manager cache.

CI must use a fresh virtual environment and index-disabled installation. A connected install is not evidence for offline completeness.

## Update policy

Dependency updates create a new bundle/manifest; they do not mutate historical verification receipts. Old bundles may be marked `SUPERSEDED` but remain identifiable by digest.

A dependency bump requires:

- regenerated lock;
- regenerated target bundles;
- hash verification;
- connected test pass;
- offline reconstruction pass for required targets.

## Storage policy

The bootstrap/development wheelhouse is small enough to keep with repository history. Large future scientific bundles may be stored as immutable assets associated with World Zero while their manifests and digests remain in Git. A large external bundle does not qualify as reconstructible unless its own-repository location, digest and recovery procedure are recorded and tested.

## Failure semantics

- missing wheel -> `OFFLINE_BUNDLE_INCOMPLETE`;
- hash mismatch -> `OFFLINE_BUNDLE_TAMPERED_OR_DRIFTED`;
- incompatible Python/platform -> `OFFLINE_TARGET_MISMATCH`;
- index access required -> `OFFLINE_RECONSTRUCTION_FAIL`;
- test/lint/type-check failure after install -> preserve the exact failing qualification subject; do not relabel bundle verification as PASS.

## Current bootstrap versions

The currently observed implementation environment is CPython 3.13.5 with Pydantic 2.13.4, pytest 9.0.2 and PyYAML 6.0.3. Ruff and mypy were absent there. Current public package releases observed during this revision include Ruff 0.16.8, mypy 2.3.1, pytest 9.1.1, Pydantic 2.13.5 and PyYAML 6.0.3. Those observations inform the next lock-generation run but do not overwrite the exact versions associated with earlier test evidence.
