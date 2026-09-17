# World Zero Offline Reconstructibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make World Zero's bootstrap/scientific-spine verification environment reconstructible without PyPI or another package index.

**Architecture:** `pyproject.toml` declares the supported runtime/tooling contract; a lock records connected resolution; `third_party/wheels/<target>` carries or references exact wheel artifacts with SHA-256 manifests; stdlib-only verifier/bootstrap tooling proves bundle integrity and performs index-disabled installation. CPython 3.12 is the qualification runtime, while CPython 3.13 remains an explicitly separate compatibility subject.

**Tech Stack:** CPython 3.12/3.13, pip offline installation, uv for connected resolution, SHA-256 manifests, pytest, Ruff, mypy, Pydantic, PyYAML, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-17-world-zero-offline-reconstructibility-design.md`

## Global Constraints

- An offline PASS requires a fresh environment installed with package-index access disabled.
- A warm package-manager cache is not dependency availability evidence.
- CPython 3.13 evidence never silently substitutes for CPython 3.12 qualification.
- Artifact availability and dependency resolution are separate evidence classes.
- Every vendored artifact is bound by filename, byte size and SHA-256.
- Bootstrap verification tooling must use the Python standard library only.
- Large numerical dependencies are not added to the bootstrap bundle before executable code needs them.
- Historical manifests/receipts are immutable subjects; newer bundles supersede rather than rewrite them.

---

### Task O1: Project dependency contract and environment identity

**Files:**
- Create: `pyproject.toml`
- Create: `src/worldzero/buildenv.py`
- Create: `tests/build/test_environment_identity.py`

**Interfaces:**
- Produces: `EnvironmentIdentity`, `capture_environment_identity() -> EnvironmentIdentity`.

- [ ] **Step 1: Write RED environment-identity tests**

```python
from worldzero.buildenv import capture_environment_identity


def test_environment_identity_records_exact_python_version():
    identity = capture_environment_identity()
    assert identity.python_version.count(".") >= 2
    assert identity.python_implementation == "CPython"


def test_environment_identity_records_platform_and_machine():
    identity = capture_environment_identity()
    assert identity.platform
    assert identity.machine
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/build/test_environment_identity.py -q`
Expected: FAIL because `worldzero.buildenv` is absent.

- [ ] **Step 3: Add project metadata and minimal implementation**

`pyproject.toml` declares Python `>=3.12,<3.14`; runtime dependencies include Pydantic and PyYAML; development dependency group includes pytest, Ruff, mypy and YAML stubs. Keep dependency declarations direct; exact transitive resolution belongs in the lock/bundle.

`capture_environment_identity()` uses only `platform`, `sys` and immutable dataclass fields.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
pytest tests/build/test_environment_identity.py tests/science -q
python -m compileall -q src
```

Expected: PASS in the currently available environment, with the receipt explicitly identifying that environment.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/worldzero/buildenv.py tests/build/test_environment_identity.py
git commit -m "build: declare World Zero Python environment contract"
```

---

### Task O2: Wheelhouse manifest and integrity verifier

**Files:**
- Create: `tools/verify_wheelhouse.py`
- Create: `tests/build/test_wheelhouse_manifest.py`
- Create: `tests/build/fixtures/wheelhouse/MANIFEST.json`
- Create: `tests/build/fixtures/wheelhouse/demo-1.0-py3-none-any.whl`
- Create: `specs/OFFLINE_WHEELHOUSE_MANIFEST_V1.schema.json`

**Interfaces:**
- Produces: `load_manifest(path)`, `verify_wheelhouse(path) -> VerificationResult`.

- [ ] **Step 1: Write RED tests for valid, missing and altered artifacts**

```python
def test_verified_manifest_accepts_matching_artifact(tmp_path):
    # fixture copied to tmp_path
    assert verify_wheelhouse(tmp_path).ok is True


def test_missing_artifact_fails_closed(tmp_path):
    # delete fixture wheel after copying
    result = verify_wheelhouse(tmp_path)
    assert result.ok is False
    assert result.code == "OFFLINE_BUNDLE_INCOMPLETE"


def test_hash_mismatch_fails_closed(tmp_path):
    # alter fixture wheel bytes after copying
    result = verify_wheelhouse(tmp_path)
    assert result.ok is False
    assert result.code == "OFFLINE_BUNDLE_TAMPERED_OR_DRIFTED"
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/build/test_wheelhouse_manifest.py -q`
Expected: FAIL because verifier is absent.

- [ ] **Step 3: Implement stdlib-only manifest validation**

Use `json`, `hashlib`, `pathlib`, `dataclasses` only. Validate schema version, target fields, duplicate filenames, exact byte sizes and SHA-256. Reject undeclared wheel files unless manifest policy explicitly permits them.

- [ ] **Step 4: Verify GREEN**

Run: `pytest tests/build/test_wheelhouse_manifest.py tests/build/test_environment_identity.py tests/science -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/verify_wheelhouse.py tests/build specs/OFFLINE_WHEELHOUSE_MANIFEST_V1.schema.json
git commit -m "build: verify offline wheelhouse integrity"
```

---

### Task O3: Connected bundle builder and offline bootstrap

**Files:**
- Create: `tools/build_wheelhouse.py`
- Create: `tools/bootstrap_offline.py`
- Create: `third_party/README.md`
- Create: `third_party/wheels/.gitkeep`
- Create: `tests/build/test_bootstrap_commands.py`

**Interfaces:**
- Produces CLI contracts:
  - `python tools/build_wheelhouse.py --target <target> --requirements <file>`
  - `python tools/bootstrap_offline.py --wheelhouse <path> --venv <path>`

- [ ] **Step 1: Write RED command-construction tests**

```python
def test_bootstrap_disables_indexes():
    command = build_pip_install_command(Path("wheelhouse"), Path("requirements.lock"))
    assert "--no-index" in command
    assert "--find-links" in command


def test_bundle_builder_requires_binary_artifacts():
    command = build_download_command(Path("requirements.lock"), Path("wheelhouse"))
    assert "--only-binary=:all:" in command
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/build/test_bootstrap_commands.py -q`
Expected: FAIL.

- [ ] **Step 3: Implement command builders and safe execution**

The connected builder invokes pip download/wheel resolution into a clean target directory, hashes every resulting wheel, writes `requirements.lock` and `MANIFEST.json`, then invokes the verifier. The offline bootstrap first verifies the manifest, creates a new virtual environment, and invokes that environment's pip with `--no-index --find-links` against the bundle. No fallback to an index is allowed.

- [ ] **Step 4: Verify GREEN without network**

Unit tests must inspect command construction and verifier behavior without reaching an index. Actual connected bundle population is a separate effect and receives its own exact receipt.

Run: `pytest tests/build tests/science -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools third_party tests/build
git commit -m "build: add offline wheelhouse build and bootstrap tooling"
```

---

### Task O4: Populate and qualify required bootstrap targets

**Required targets:**
- `cp312-win_amd64`
- `cp312-manylinux_x86_64`

**Compatibility targets, when practical:**
- `cp313-win_amd64`
- `cp313-manylinux_x86_64`

**Files:**
- Populate: `third_party/wheels/<target>/`
- Create: `docs/qualification/OFFLINE_BOOTSTRAP_<target>_V1.md`
- Create/commit: `uv.lock`

- [ ] **Step 1: Generate connected lock from `pyproject.toml`**

Run in a network-capable environment:

```bash
uv lock
```

Record exact uv version and lock SHA-256.

- [ ] **Step 2: Build each required wheelhouse from the frozen dependency set**

The builder must download/build no source package during offline qualification; final required-target bundle contains wheels only.

- [ ] **Step 3: Verify manifest hashes**

```bash
python tools/verify_wheelhouse.py third_party/wheels/<target>
```

Expected: PASS.

- [ ] **Step 4: Prove clean offline bootstrap**

Create a fresh environment with no inherited site packages and run:

```bash
python tools/bootstrap_offline.py \
  --wheelhouse third_party/wheels/<target> \
  --venv .offline-verify/<target>
```

Then from that environment run:

```bash
python -m pytest -q
ruff check src tests tools
mypy src/worldzero
```

Network/package-index access must remain disabled for installation.

- [ ] **Step 5: Record qualification evidence**

Document exact target, Python version, manifest digest, lock digest, tool versions, commands and results. Do not mark a target verified from another OS/ABI.

- [ ] **Step 6: Commit bundle plus qualification subject**

```bash
git add uv.lock third_party/wheels docs/qualification
git commit -m "build: freeze verified offline bootstrap bundles"
```

---

### Task O5: CI offline-reconstruction gate

**Files:**
- Create: `.github/workflows/offline-bootstrap.yml`

- [ ] **Step 1: Add a required-target matrix**

Run required Linux CPython-3.12 bundle verification on every scientific-spine PR. Windows CPython-3.12 runs in the matrix when the Windows bundle exists.

- [ ] **Step 2: Ensure install step cannot reach an index**

Set `PIP_NO_INDEX=1` and use `bootstrap_offline.py`. Do not call `uv sync` or `pip install` against an index in the offline job.

- [ ] **Step 3: Run verification suite**

Run pytest, Ruff and mypy from the reconstructed environment and record versions.

- [ ] **Step 4: Read back CI evidence**

A green workflow is build/offline-reconstruction evidence for its exact commit/target only; it is not scientific qualification.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/offline-bootstrap.yml
git commit -m "ci: verify World Zero without package indexes"
```

## Self-review

- The plan distinguishes dependency declaration, resolution and artifact availability.
- It does not treat CPython 3.13 tests as CPython 3.12 qualification.
- The verifier/bootstrap path has no third-party Python dependency.
- Actual wheelhouse population is not claimed until a network-capable target builder produces and then offline-verifies it.
- Large future numerical dependency bundles remain out of the bootstrap scope until required by executable sectors.
