# World Zero Demography 2023 Evidence Partition — reviewed successor status

Status: **PRE-FIT / V1 HOLDOUT INTERPRETATION SUPERSEDED / V2 INITIALIZATION PARTITION FROZEN**

The exact evidence catalog remains `science/evidence/WZ_DEMOGRAPHY_2023_EVIDENCE_V1.yaml`. It contains 50 admitted, validation-eligible 2023 population observations: 10 regional total-population observations and 40 regional age-cohort observations.

The original pre-fit subject `WZ_DEMOGRAPHY_2023_VARIABLE_HOLDOUT_V1` assigned the 10 regional totals to `CALIBRATION` and the 40 age-cohort observations to `VARIABLE_HOLDOUT`.

Hostile review identified a scientific contamination boundary before calibration execution: V0 uses the 2023 cohort population values as `NativeBackboneConfig.initial_population`. A value consumed as an initial condition is not an untouched holdout merely because it is absent from the calibration loss.

Therefore V1 is retained only as historical pre-execution provenance and is superseded for governed use by:

`science/partitions/WZ_DEMOGRAPHY_2023_INITIALIZATION_PARTITION_V2.yaml`

V2 assigns:
- the 10 regional total-population observations to `CALIBRATION`;
- all 40 2023 cohort observations to `INITIALIZATION`;
- no 2023 cohort observation to a final holdout.

The partition contract now types initialization separately from calibration and holdout, and exposes initialization IDs independently. Population-evidence verification fails closed if an initialization observation is also presented as a final holdout.

A future untouched cohort validation subject must use evidence not consumed to initialize the evaluated trajectory, for example an independently frozen pre-2023 initialization followed by a 2023 prediction, or a later cohort year evaluated after the independently initialized/calibrated trajectory. Any actual run must bind its initialization-use subject rather than infer cleanliness from loss-function exclusion alone.

Both WPP source families remain conservatively assigned to `UN_WPP_2024_POPULATION_FAMILY`. The observations do **not** represent independent source confirmations merely because there are many rows.

This packet still establishes only a pre-fit evidence-use firewall. It does not establish `HISTORICAL_CALIBRATION_PASS`, `VARIABLE_HOLDOUT_PASS`, temporal holdout performance, predictive validity, or forecast skill.
