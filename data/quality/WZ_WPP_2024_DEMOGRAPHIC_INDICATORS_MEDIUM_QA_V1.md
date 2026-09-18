# WPP 2024 Demographic Indicators Medium — QA V1

Dataset ID: `un-wpp-2024-demographic-indicators-medium-v1`
Payload SHA-256: `286ac36bb1415e2e1ade03acfef0a29f0e4c087e2f78e38c48f50c5df89082bc`
Payload bytes: `16,557,272`
Ingest/verification code: `644cd4f70b39176a987de196affa9b7c2763e780`

## Source identity

HTTP HEAD against the frozen source URL returned:
- status: 200
- content type: `application/x-gzip`
- content length: `16,557,272`
- last modified: `2024-12-13T19:11:17Z`
- ETag: `"0x8DD1BA9EBFD1565"`

The downloaded byte length and SHA-256 match the manifest exactly.

## Structural inspection

Exact CSV header matches `worldzero.data.wpp2024.WPP2024_FIELDS`.

Observed payload shape:
- total rows: **84,360**
- unique provider locations/aggregates: **555**
- ISO3 country/area locations: **237**
- variant set: **Medium only**
- minimum Time: **1950**
- maximum Time: **2101**
- country rows in 2023: **237**
- country rows in 2024: **237**
- country rows in 2101: **237**

For every substantive year 1950–2100:
- country/area mid-year population row count is exactly **237**
- missing `TPopulation1July` values: **0**
- negative `TPopulation1July` values: **0**

## Estimate / projection boundary

UN WPP 2024 methodology/release material identifies **1950–2023 as the estimation period** and **2024 onward as projections**.

World Zero therefore classifies:
- 1950–2023 WPP values: `OFFICIAL_ESTIMATE`
- 2024–2100 WPP values: `PROJECTION`, `validation_eligible=false`

The provider's 2101 country rows contain only identifying columns plus `TPopulation1Jan`; mid-year population and demographic indicator fields are blank. World Zero treats 2101 as a technical boundary value, not substantive annual projection coverage.

Official source references:
- `https://population.un.org/wpp`
- `https://population.un.org/wpp/assets/Files/WPP2024_Release-Note.pdf`
- `https://population.un.org/dataportalapi/index.html`

## Population extraction checks

`TPopulation1July` is interpreted as thousands of persons and converted to persons by multiplying by 1000.

Country/area sums versus provider World aggregate:

| Year | Classification | 237-country sum | Provider World | Difference |
| --- | --- | ---: | ---: | ---: |
| 2023 | OFFICIAL_ESTIMATE | 8,091,734,931 | 8,091,734,930 | +1 |
| 2024 | PROJECTION | 8,161,972,586 | 8,161,972,572 | +14 |
| 2026 | PROJECTION | 8,300,678,395 | 8,300,678,396 | -1 |
| 2100 | PROJECTION | 10,180,160,752 | 10,180,160,751 | +1 |

These differences are consistent with row-level rounding and are negligible relative to the aggregate scale.

## Known source-hierarchy note

The 237 countries/areas reduce to 22 WPP parent groups. `ParentID=918` is used for Bermuda, Canada, Greenland, Saint Pierre and Miquelon, and the United States, while the visible aggregate named Northern America uses a different provider location ID. World Zero records this explicitly rather than silently rewriting the source hierarchy.

Macroregion aggregation is **not part of this raw-source admission**.
