# WPP 2024 Macroregion Cohort Population 2026 — Admission V1

Dataset ID: `wz-wpp2024-macroregion-cohort-population-2026-v1`  
Disposition: **ADMITTED bridge cut**

This 40-row artifact is derived from the exact admitted WPP 2024 age5/sex payload through the frozen `WPP2024_PARENT_TO_WZ_MACROREGION_V0` mapping and `WZ_AGE_COHORT_V0` cohort convention using transform code at commit `6c287ec13e86842d51f91c57e9ee23fb54bea464`.

The source year 2026 is a WPP projection. The derived artifact is therefore permanently `validation_eligible=false`.

Exact output:
- path: `data/derived/wpp2024/WZ_MACROREGION_V0_cohort_population_2026.csv`
- SHA-256: `a9ed5b83ca86700f42893e3929929afcded2bf4574b1e9b74807fc736a69a236`
- bytes: **2,835**
- total population: **8,300,678,587**

Reconciliation to the independently admitted 2026 total-population bridge differs by **+192 persons globally**, with a maximum absolute regional difference of **54 persons**, consistent with the separately documented WPP age-bin rounding behavior.

Admission permits use as an explicitly labeled 2026 cohort initialization bridge. It does not make the cohort convention empirical truth, does not count as validation evidence, does not calibrate demographic rates, and does not by itself promote the canonical 2026 scenario or data bundle to executable/READY.
