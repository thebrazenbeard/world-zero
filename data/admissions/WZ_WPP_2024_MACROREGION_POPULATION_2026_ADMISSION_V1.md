# WPP 2024 Macroregion Population 2026 — Admission V1

Dataset ID: `wz-wpp2024-macroregion-population-2026-v1`
Disposition: **ADMITTED bridge cut**

This 10-region artifact is derived from the admitted WPP 2024 raw source through the frozen `WPP2024_PARENT_TO_WZ_MACROREGION_V0` transform at commit `9956829a326b533670dd01eaa9cb4d1ce852fcb3`.

The source year 2026 is a WPP projection. The derived artifact is therefore permanently `validation_eligible=false` under `DATA_ADMISSION_POLICY_V1`.

Exact output:
- path: `data/derived/wpp2024/WZ_MACROREGION_V0_population_2026.csv`
- SHA-256: `59268c28420f45a1f6f1830659841cb9a236345d82b4e62968c7d3ad3e126c98`
- bytes: `677`
- total population: `8,300,678,395`

Admission permits use as an explicitly labeled 2026 initialization bridge. It does not count as validation evidence and does not make the full 2026 scenario executable.
