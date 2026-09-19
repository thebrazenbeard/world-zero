# WPP 2024 -> WZ_MACROREGION_V0 Cohort Population 2023 — QA V1

Source dataset: `un-wpp-2024-population-age5-sex-medium-v1`
Source SHA-256: `a04d7d1486a5eb2832cc812d599448f0a71e8ac9e1e7e6fa4066673d6a2487cd`
Transform subject: `6c287ec13e86842d51f91c57e9ee23fb54bea464`
Target region set: `WZ_MACROREGION_V0` (**FROZEN**, 10 regions)
Target cohort set: `WZ_AGE_COHORT_V0` (**FROZEN**, 4 cohorts)

## Exact source-byte verification

The immutable public mirror at `kenshin-morioka/ds@bc13919b97eed8a9abe6c20a1263a84546d0c15b`, Git blob `b8123f47e248690dab8ddc45d413cf821b321fdc`, was independently streamed in memory and accepted only because it matched the already admitted World Zero source subject exactly:
- bytes: **29,948,947**
- SHA-256: `a04d7d1486a5eb2832cc812d599448f0a71e8ac9e1e7e6fa4066673d6a2487cd`

## Structural extraction checks

For year 2023:
- source class: `OFFICIAL_ESTIMATE`
- 237 ISO3 country/area locations
- 21 frozen WPP five-year age groups exactly once per country/area
- 4,977 selected country-age rows = 237 × 21
- one stable WPP `ParentID` per country/area
- all 22 governed parent groups covered
- all 10 frozen World Zero macroregions covered
- all 4 frozen World Zero age cohorts present in every macroregion
- output rows: **40 = 10 × 4**

Exact output:
- path: `data/derived/wpp2024/WZ_MACROREGION_V0_cohort_population_2023.csv`
- SHA-256: `e42aee90f156e51471c2c1704492b412626dc647fb5e6b4bde6b8b43d9a486d4`
- bytes: **3,074**
- cohort-derived global population: **8,091,735,125 persons**

## Reconciliation against admitted 2023 total-population cut

| Region | Cohort sum | Admitted total | Difference |
| --- | ---: | ---: | ---: |
| North America | 382,902,748 | 382,902,740 | +8 |
| Latin America & Caribbean | 658,891,578 | 658,891,517 | +61 |
| Western, Northern & Southern Europe | 459,555,461 | 459,555,429 | +32 |
| Eastern Europe & Central Asia | 366,857,601 | 366,857,609 | -8 |
| Middle East & North Africa | 572,506,543 | 572,506,541 | +2 |
| Sub-Saharan Africa | 1,212,229,456 | 1,212,229,418 | +38 |
| South Asia | 2,043,083,172 | 2,043,083,159 | +13 |
| East Asia | 1,660,028,547 | 1,660,028,546 | +1 |
| Southeast Asia | 690,117,184 | 690,117,186 | -2 |
| Oceania | 45,562,835 | 45,562,786 | +49 |

Global difference: **+194 persons**. Largest regional absolute difference: **61 persons**, inside the frozen 100-person reconciliation ceiling and consistent with independent WPP row-level rounding.

## Evidence classification

2023 is within the WPP official-estimate period. This artifact is therefore `DERIVED` from `OFFICIAL_ESTIMATE` and is `validation_eligible=true`.

That eligibility is not permission to leak the subject into fitting. Calibration/holdout use still requires a frozen partition protocol. The four World Zero age cohorts remain a modeling convention, not an empirically privileged taxonomy.
