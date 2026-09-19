import hashlib
import io
from pathlib import Path

import pytest
import yaml

import worldzero.data.acquisition as acquisition_module

from worldzero.data.acquisition import _copy_verified_candidate, fetch_admitted_dataset


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def test_verified_candidate_is_published_atomically(tmp_path: Path):
    payload = b"world-zero-source-bytes"
    output = tmp_path / "source.bin"

    result = _copy_verified_candidate(
        io.BytesIO(payload),
        output_path=output,
        dataset_id="fixture",
        requested_url="https://example.invalid/source.bin",
        expected_length=len(payload),
        expected_sha256=_sha(payload),
    )

    assert output.read_bytes() == payload
    assert result.content_sha256 == _sha(payload)
    assert result.content_length_bytes == len(payload)
    assert result.requested_url == "https://example.invalid/source.bin"
    assert result.resolved_url == "https://example.invalid/source.bin"
    assert list(tmp_path.glob(".*.candidate")) == []


def test_digest_mismatch_preserves_existing_output(tmp_path: Path):
    output = tmp_path / "source.bin"
    output.write_bytes(b"known-good")
    candidate = b"different-candidate"

    with pytest.raises(ValueError, match="digest"):
        _copy_verified_candidate(
            io.BytesIO(candidate),
            output_path=output,
            dataset_id="fixture",
            requested_url="https://example.invalid/source.bin",
            expected_length=len(candidate),
            expected_sha256="0" * 64,
        )

    assert output.read_bytes() == b"known-good"
    assert list(tmp_path.glob(".*.candidate")) == []


def test_oversized_candidate_fails_before_publication(tmp_path: Path):
    output = tmp_path / "source.bin"
    output.write_bytes(b"known-good")

    with pytest.raises(ValueError, match="exceeds admitted content length"):
        _copy_verified_candidate(
            io.BytesIO(b"12345"),
            output_path=output,
            dataset_id="fixture",
            requested_url="https://example.invalid/source.bin",
            expected_length=4,
            expected_sha256=_sha(b"1234"),
        )

    assert output.read_bytes() == b"known-good"


def test_truncated_candidate_fails_before_publication(tmp_path: Path):
    output = tmp_path / "source.bin"

    with pytest.raises(ValueError, match="length does not match"):
        _copy_verified_candidate(
            io.BytesIO(b"123"),
            output_path=output,
            dataset_id="fixture",
            requested_url="https://example.invalid/source.bin",
            expected_length=4,
            expected_sha256=_sha(b"1234"),
        )

    assert not output.exists()


def test_fetch_refuses_to_overwrite_governed_manifest(tmp_path: Path):
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text("not parsed because alias check runs first\n", encoding="utf-8")

    with pytest.raises(ValueError, match="must not overwrite"):
        fetch_admitted_dataset(manifest, manifest)


def test_fetch_refuses_manifest_hardlink_alias(tmp_path: Path):
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text("not parsed because alias check runs first\n", encoding="utf-8")
    output = tmp_path / "hardlink.bin"
    output.hardlink_to(manifest)

    with pytest.raises(ValueError, match="must not overwrite"):
        fetch_admitted_dataset(manifest, output)


class _FakeResponse(io.BytesIO):
    def __init__(self, payload: bytes, *, url: str):
        super().__init__(payload)
        self.status = 200
        self.headers = {"Content-Length": str(len(payload))}
        self._url = url

    def geturl(self) -> str:
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False


def _write_admitted_fixture_manifest(tmp_path: Path, payload: bytes) -> Path:
    source = Path("data/manifests/UN_WPP_2024_POPULATION_AGE5_SEX_MEDIUM_V1.yaml")
    document = yaml.safe_load(source.read_text(encoding="utf-8"))
    document["dataset_id"] = "fixture-admitted-source"
    document["source_url"] = "https://origin.example.invalid/source.bin"
    document["content_sha256"] = _sha(payload)
    document["content_length_bytes"] = len(payload)
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


def test_fetch_rejects_https_to_http_redirect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    payload = b"fixture"
    manifest = _write_admitted_fixture_manifest(tmp_path, payload)

    monkeypatch.setattr(
        acquisition_module,
        "urlopen",
        lambda request, timeout: _FakeResponse(
            payload,
            url="http://mirror.example.invalid/source.bin",
        ),
    )

    with pytest.raises(ValueError, match="redirect target must remain"):
        fetch_admitted_dataset(manifest, tmp_path / "source.bin")


def test_fetch_records_effective_https_redirect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    payload = b"fixture"
    manifest = _write_admitted_fixture_manifest(tmp_path, payload)
    resolved_url = "https://mirror.example.invalid/source.bin"

    monkeypatch.setattr(
        acquisition_module,
        "urlopen",
        lambda request, timeout: _FakeResponse(payload, url=resolved_url),
    )

    result = fetch_admitted_dataset(manifest, tmp_path / "source.bin")

    assert result.requested_url == "https://origin.example.invalid/source.bin"
    assert result.resolved_url == resolved_url
