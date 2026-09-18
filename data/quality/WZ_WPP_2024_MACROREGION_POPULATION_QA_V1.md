# WPP 2024 -> WZ_MACROREGION_V0 Population QA V1

Source dataset: `un-wpp-2024-demographic-indicators-medium-v1`
Source SHA-256: `286ac36bb1415e2e1ade03acfef0a29f0e4c087e2f78e38c48f50c5df89082bc`
Mapping: `WPP2024_PARENT_TO_WZ_MACROREGION_V0`
Transform subject: `9956829a326b533670dd01eaa9cb4d1ce852fcb3`
Target region set: `WZ_MACROREGION_V0` (**FROZEN**, 10 regions)

The mapping covers all 22 WPP country-parent groups exactly once. Every target macroregion receives at least one parent group.

Southern Europe (`ParentID=925`) is intentionally grouped with Western/Northern Europe under the truthful label **Western, Northern & Southern Europe**, per Patrick's 2026-09-18 decision.

## Conservation checks

For both checked years:
- 237 country/area rows collapse to exactly 22 WPP parent groups;
- 22 parent groups collapse to exactly 10 World Zero macroregions;
- country total = parent-group total = macroregion total exactly at integer-person resolution.

2023 total: **8,091,734,931 persons**
- source class: `OFFICIAL_ESTIMATE`
- derived class: `DERIVED`
- validation eligible: **true**

2026 total: **8,300,678,395 persons**
- source class: `PROJECTION`
- derived class: `DERIVED`
- validation eligible: **false**

## 2023 macroregion population

| Region | Persons |
| --- | ---: |
| North America | 382,902,740 |
| Latin America & Caribbean | 658,891,517 |
| Western, Northern & Southern Europe | 459,555,429 |
| Eastern Europe & Central Asia | 366,857,609 |
| Middle East & North Africa | 572,506,541 |
| Sub-Saharan Africa | 1,212,229,418 |
| South Asia | 2,043,083,159 |
| East Asia | 1,660,028,546 |
| Southeast Asia | 690,117,186 |
| Oceania | 45,562,786 |

## 2026 macroregion population bridge

| Region | Persons |
| --- | ---: |
| North America | 389,628,823 |
| Latin America & Caribbean | 672,135,562 |
| Western, Northern & Southern Europe | 459,777,391 |
| Eastern Europe & Central Asia | 368,628,513 |
| Middle East & North Africa | 599,872,196 |
| Sub-Saharan Africa | 1,304,244,790 |
| South Asia | 2,106,270,433 |
| East Asia | 1,648,245,779 |
| Southeast Asia | 704,755,916 |
| Oceania | 47,118,992 |

The 2026 artifact is an initialization bridge only. Its admission does not make it validation evidence and does not promote the full 2026 World Zero scenario to executable.
