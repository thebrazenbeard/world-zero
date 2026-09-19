"""Fetch a dataset candidate and publish it only if it matches an admitted manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from worldzero.data.acquisition import fetch_admitted_dataset


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch exact bytes bound by a World Zero admitted dataset manifest"
    )
    parser.add_argument("manifest_path", type=Path)
    parser.add_argument("output_path", type=Path)
    parser.add_argument(
        "--candidate-url",
        help="Optional HTTPS mirror; exact admitted length and SHA-256 still govern acceptance",
    )
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    args = parser.parse_args()

    result = fetch_admitted_dataset(
        args.manifest_path,
        args.output_path,
        candidate_url=args.candidate_url,
        timeout_seconds=args.timeout_seconds,
    )
    print(
        json.dumps(
            {
                "content_length_bytes": result.content_length_bytes,
                "content_sha256": result.content_sha256,
                "dataset_id": result.dataset_id,
                "output_path": result.output_path.as_posix(),
                "requested_url": result.requested_url,
                "resolved_url": result.resolved_url,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
