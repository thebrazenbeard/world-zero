# WPP 2024 Population by 5-Year Age Groups and Sex — QA V1

Dataset ID: `un-wpp-2024-population-age5-sex-medium-v1`
Payload SHA-256: `a04d7d1486a5eb2832cc812d599448f0a71e8ac9e1e7e6fa4066673d6a2487cd`
Payload bytes: `29,948,947`
Ingest/verification code: `c4fb3c183cb3ea77220c41a91b9640ca4e6664a7`

## Source identity

Official WPP bulk URL returned HTTP 200, `application/x-gzip`, content length `29,948,947`, Last-Modified `2024-12-13T19:11:50Z`, and ETag `"0x8DD1BA9FF59EA82"`.

Downloaded bytes match the manifest size and SHA-256 exactly.

## Structural inspection

- total rows: **1,759,905**
- ISO3 country/area locations: **237**
- years: **1950–2100**
- variant set: **Medium only**
- age groups: **21**, from `0-4` through `100+`
- country rows in 2023: **4,977 = 237 × 21**
- country rows in 2026: **4,977 = 237 × 21**
- country-year pairs over 1950–2100: **35,787 = 237 × 151**
- age-group rows per country-year: **exactly 21**
- missing PopTotal/PopMale/PopFemale values: **0**
- negative population values: **0**
- inconsistent age starts/spans: **0**
- maximum `PopMale + PopFemale - PopTotal`: **0.001 thousand = 1 person**, consistent with row-level rounding

## Cross-source reconciliation

Age-bin totals were independently aggregated through the frozen 22→10 macroregion mapping and compared with the already admitted WPP demographic-indicators macroregion population cuts.

2023:
- age-bin global total: **8,091,735,125**
- admitted total-population cut: **8,091,734,931**
- difference: **+194 persons**
- largest regional absolute difference: **61 persons**

2026:
- age-bin global total: **8,300,678,587**
- admitted total-population cut: **8,300,678,395**
- difference: **+192 persons**
- largest regional absolute difference: **54 persons**

Those differences are negligible and consistent with independent rounding of five-year age-group rows versus total-population rows.

## Evidence classification

Per the canonical WPP policy:
- 1950–2023: `OFFICIAL_ESTIMATE`
- 2024–2100: `PROJECTION`, never validation evidence

This QA admits the raw age/sex source. The four World Zero cohort transformation is a separate governed transformation subject.
