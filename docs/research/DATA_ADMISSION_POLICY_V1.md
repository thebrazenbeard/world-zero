# World Zero Data Admission Policy V1

Date: 2026-09-18
Authority: Patrick

## 2026 baseline rule

Use observed historical data for calibration whenever possible.

Build the 2026 starting state from the newest **verified** real observations plus explicitly labeled estimates, nowcasts, or projections needed to bridge the gap.

A bridge value is verified only after its source identity, provenance, content digest, rights/terms state, schema mapping, transformation lineage, and applicable quality checks have been established.

Bridge values must never be counted as validation evidence merely because they are used to initialize the 2026 state.

## Raw-data storage policy

Use the smallest integrity-preserving storage approach.

Small, legally redistributable immutable cuts may be stored in Git when practical.

Large raw datasets should remain outside Git as immutable cache/artifact payloads. Git must retain enough information to reconstruct and verify the exact cut: provider/product/vintage, retrieval recipe, rights record, payload size, SHA-256, schema mapping, transform code/version, quality report, and admission record.

A missing raw cache must not silently substitute a newer provider revision.

## Source-access policy

Open-data-first.

Prefer authoritative, open, reproducible sources. If the strongest available source is restricted, proprietary, licensed beyond ordinary open-use terms, or paid, use the strongest defensible open substitute and document the resulting limitation.

Ask Patrick before paying for, subscribing to, or incorporating restricted/proprietary data.

These rules do not lower the existing dataset-admission or qualification gates.
