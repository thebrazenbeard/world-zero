# WPP 2024 -> WZ_MACROREGION_V0 Cohort Population 2026 — QA V1

Source dataset: `un-wpp-2024-population-age5-sex-medium-v1`  
Source SHA-256: `a04d7d1486a5eb2832cc812d599448f0a71e8ac9e1e7e6fa4066673d6a2487cd`  
Transform subject: `6c287ec13e86842d51f91c57e9ee23fb54bea464`  
Target region set: `WZ_MACROREGION_V0` (**FROZEN**, 10 regions)  
Target cohort set: `WZ_AGE_COHORT_V0` (**FROZEN**, 4 cohorts)

## Exact source-byte verification

Generation used a public immutable mirror candidate at `kenshin-morioka/ds@bc13919b97eed8a9abe6c20a1263a84546d0c15b`, path `datasets/raw/wpp_population_age_sex/WPP2024_PopulationByAge5GroupSex_Medium.csv.gz`, Git blob `b8123f47e248690dab8ddc45d413cf821b321fdc`.

The mirror route is not a new authority source. Its bytes were independently streamed and accepted only because they matched the already admitted World Zero source subject exactly:
- bytes: **29,948,947**
- SHA-256: `a04d7d1486a5eb2832cc812d599448f0a71e8ac9e1e7e6fa4066673d6a2487cd`

## Structural extraction checks

For year 2026:
- source class: `PROJECTION`
- 237 ISO3 country/area locations
- 21 frozen WPP five-year age groups exactly once per country/area
- 4,977 selected country-age rows = 237 × 21
- one stable WPP `ParentID` per country/area
- all 22 governed parent groups covered
- all 10 frozen World Zero macroregions covered
- all 4 frozen World Zero age cohorts present in every macroregion
- output rows: **40 = 10 × 4**

Exact output:
- path: `data/derived/wpp2024/WZ_MACROREGION_V0_cohort_population_2026.csv`
- SHA-256: `a9ed5b83ca86700f42893e3929929afcded2bf4574b1e9b74807fc736a69a236`
- bytes: **2,835**
- cohort-derived global population: **8,300,678,587 persons**

## Reconciliation against admitted 2026 total-population bridge

| Region | Cohort sum | Admitted total | Difference |
| --- | ---: | ---: | ---: |
| North America | 389,628,834 | 389,628,823 | +11 |
| Latin America & Caribbean | 672,135,602 | 672,135,562 | +40 |
| Western, Northern & Southern Europe | 459,777,422 | 459,777,391 | +31 |
| Eastern Europe & Central Asia | 368,628,516 | 368,628,513 | +3 |
| Middle East & North Africa | 599,872,210 | 599,872,196 | +14 |
| Sub-Saharan Africa | 1,304,244,823 | 1,304,244,790 | +33 |
| South Asia | 2,106,270,437 | 2,106,270,433 | +4 |
| East Asia | 1,648,245,781 | 1,648,245,779 | +2 |
| Southeast Asia | 704,755,916 | 704,755,916 | 0 |
| Oceania | 47,119,046 | 47,118,992 | +54 |

Global difference: **+192 persons**. Largest regional absolute difference: **54 persons**. These match the admitted age5-source QA and are consistent with independent row-level rounding.

## Evidence classification

This artifact is `DERIVED` from a 2026 WPP `PROJECTION`. It is permanently `validation_eligible=false`.

Admission of this artifact permits an explicitly labeled 2026 initialization bridge. It does not calibrate demographic rates, validate a forecast, or by itself make the canonical 2026 World Zero scenario executable.
