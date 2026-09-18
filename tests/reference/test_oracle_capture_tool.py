import hashlib

import pytest

from tools.capture_world3_oracle import (
    exact_commit_from_ref,
    format_number,
    serialize_fixture_csv,
)


def test_fixture_csv_is_deterministic_and_column_ordered():
    data = serialize_fixture_csv(
        [1900.0, 1900.5],
        {"POPULATION": [1.0, 2.0], "FOOD_PER_CAPITA": [3.0, 4.0]},
        ["POPULATION", "FOOD_PER_CAPITA"],
    )
    assert data == (
        b"YEAR,POPULATION,FOOD_PER_CAPITA\n"
        b"1900,1,3\n"
        b"1900.5,2,4\n"
    )
    assert hashlib.sha256(data).hexdigest() == (
        "148cc90baa3f482f06ce82b88d13856cbdfcdfa7f70beeefa735947dc7c11fc3"
    )


def test_fixture_csv_rejects_mismatched_lengths():
    with pytest.raises(ValueError, match="series lengths"):
        serialize_fixture_csv(
            [1900.0, 1900.5],
            {"POPULATION": [1.0]},
            ["POPULATION"],
        )


def test_nonfinite_output_is_rejected():
    with pytest.raises(ValueError, match="non-finite"):
        format_number(float("nan"))


def test_exact_commit_is_extracted_from_oracle_ref():
    ref = (
        "cvanwynsberghe/pyworld3@"
        "cdfd0a8f3675c514f27ddc0e00c8d8bd4d1fefb8"
    )
    assert exact_commit_from_ref(ref) == (
        "cdfd0a8f3675c514f27ddc0e00c8d8bd4d1fefb8"
    )
