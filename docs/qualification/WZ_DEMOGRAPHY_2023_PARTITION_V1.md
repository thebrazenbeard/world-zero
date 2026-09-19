# World Zero Demography 2023 Evidence Partition V1

Status: **FROZEN BEFORE EXECUTION**

This packet freezes the first empirical demography partition without claiming any calibration or validation result.

The exact evidence catalog is `science/evidence/WZ_DEMOGRAPHY_2023_EVIDENCE_V1.yaml`. It contains 50 admitted, validation-eligible 2023 population observations: 10 regional total-population observations and 40 regional age-cohort observations.

The frozen partition `WZ_DEMOGRAPHY_2023_VARIABLE_HOLDOUT_V1` assigns the 10 regional totals to `CALIBRATION` and all 40 cohort-composition observations to `VARIABLE_HOLDOUT`.

No cohort observation may be moved into calibration after seeing holdout performance without creating a new partition subject and downgrading the affected comparison to exploratory.

Both WPP source families are conservatively assigned to `UN_WPP_2024_POPULATION_FAMILY`. The 50 rows therefore do **not** represent 50 independent source confirmations.

This packet establishes a pre-fit evidence firewall only. It does not establish `HISTORICAL_CALIBRATION_PASS`, `VARIABLE_HOLDOUT_PASS`, temporal holdout performance, predictive validity, or forecast skill.
