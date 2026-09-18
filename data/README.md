# World Zero data directory

World Zero does not treat a URL as a dataset binding.

Raw or derived data used by a scientific run must be bound through an immutable dataset manifest that records provider, product, release/vintage, retrieval timestamp, source locator, license/terms state, geography, time coverage, frequency, units, transformations, missing-data policy, uncertainty, payload SHA-256, transform-code commit, and admission evidence.

Dataset lifecycle:

`CANDIDATE -> SOURCE_VERIFIED -> RIGHTS_TERMS_CHECKED -> SCHEMA_MAPPED -> QUALITY_CHECKED -> ADMITTED`

Only an `ADMITTED` immutable cut may be consumed by qualification-grade model runs. Sector code must not fetch network data directly.

Observation transforms preserve the raw dataset IDs and digests that contributed to each derived series. Derived or composite observations must also record the transform identity, version, source observable IDs, and code commit.
