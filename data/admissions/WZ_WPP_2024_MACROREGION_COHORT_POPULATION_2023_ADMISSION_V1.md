# WPP 2024 Macroregion Cohort Population 2023 — Admission V1

Dataset ID: `wz-wpp2024-macroregion-cohort-population-2023-v1`
Disposition: **ADMITTED historical evidence cut**

This 40-row artifact is derived from the exact admitted WPP 2024 age5/sex payload through the frozen `WPP2024_PARENT_TO_WZ_MACROREGION_V0` mapping and `WZ_AGE_COHORT_V0` cohort convention using transform code at commit `6c287ec13e86842d51f91c57e9ee23fb54bea464`.

Exact output:
- path: `data/derived/wpp2024/WZ_MACROREGION_V0_cohort_population_2023.csv`
- SHA-256: `e42aee90f156e51471c2c1704492b412626dc647fb5e6b4bde6b8b43d9a486d4`
- bytes: **3,074**
- total population: **8,091,735,125**

Reconciliation to the independently admitted 2023 total-population cut differs by **+194 persons globally**, with a maximum absolute regional difference of **61 persons**.

Because 2023 is an official-estimate year, the artifact is `validation_eligible=true`. That flag means it may be assigned to a governed historical comparison partition. It does not assign the artifact to calibration or holdout by itself, does not validate a model, and does not make the four World Zero cohort boundaries empirical truth.
