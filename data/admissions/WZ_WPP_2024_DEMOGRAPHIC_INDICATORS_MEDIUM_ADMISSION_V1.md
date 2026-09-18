# WPP 2024 Demographic Indicators Medium — Admission V1

Dataset ID: `un-wpp-2024-demographic-indicators-medium-v1`
Disposition: **ADMITTED raw source cut**

## Admission evidence

- exact payload SHA-256 verified
- exact payload byte length verified
- source HTTP identity recorded
- release/vintage recorded as World Population Prospects 2024, released 11 July 2024
- official UN estimate/projection boundary recorded
- rights/terms reviewed from official UN Population Division material
- exact CSV schema mapped
- required mid-year population completeness checked across 1950–2100
- country/area coverage checked at 237 locations per substantive year
- world-total reconciliation checked on representative historical/projection years
- ingest/verification code frozen at `644cd4f70b39176a987de196affa9b7c2763e780`

Rights basis recorded as CC BY 3.0 IGO from official UN Population Division Data Portal/API and WPP publication metadata. This record is provenance documentation, not legal advice.

## Scope of admission

Admission means this exact raw byte cut may be used as a governed input to downstream World Zero transformations.

Admission does **not** mean:
- WPP projections are observed data;
- 2024+ values are validation evidence;
- the World Zero 2026 baseline is data-bound;
- the current 10-region macroregion mapping is complete;
- any World Zero demographic parameter has been calibrated.

Per `DATA_ADMISSION_POLICY_V1`, 2024+ WPP projection values may be used only as explicitly labeled bridge/scenario inputs and remain ineligible as validation evidence.

## External raw storage

The 16.6 MB raw gzip is intentionally excluded from Git.

Reconstruction requires the retrieval recipe plus exact SHA-256. If the provider later serves different bytes at the same URL, the new payload is a different candidate cut and must not silently replace this admitted source.

## Open frontier

Country/area to `WZ_MACROREGION_V0` aggregation remains a separate transformation and is not admitted by this record. Southern Europe currently requires an explicit World Zero region-semantics decision before that mapping can be frozen.
