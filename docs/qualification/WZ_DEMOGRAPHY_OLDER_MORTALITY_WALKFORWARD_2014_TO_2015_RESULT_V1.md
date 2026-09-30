# World Zero Regional Older-Adult Mortality Walk-Forward Result V1

Status: **EXECUTED / CROSS-PLATFORM REPRODUCED / NOT_BETTER_REGIONAL_OLDER_MORTALITY / HISTORICAL_WALKFORWARD_COMPARISON_ONLY**

Date: 2026-09-19

## Frozen experiment

The contract was frozen before this lane extracted or inspected the 2015 target:

`science/scoring/WZ_DEMOGRAPHY_OLDER_MORTALITY_WALKFORWARD_2014_TO_2015_V1.yaml`

Freeze commit:

`147f609e40923773e318c49c0473b8232534c033`

Fitting history is 2012–2014. Base birth, ageing, global mortality-shape, and migration dynamics use 2013–2014. The candidate changes only older-adult mortality, replacing the globally shaped regional value with a region-specific rate inferred from 2012→2013 and 2013→2014 older-stock continuity after accounting for mature→older ageing and modeled older-adult migration.

The 2015 target is extracted only after both baseline and candidate trajectories execute.

## First clean result

Execution source:

`901bd132e76ffe7711a584bf4ef6dc1f6596bc35`

Source tree:

`688cec7e477a9e61e46bf6dfa91ffca344bdfed3`

Baseline parameter SHA-256:

`0395be7f1e61cbd859d05fe494347e54d3ec1df8408e6c3d4cd868492b829443`

Candidate parameter SHA-256:

`c92b113e894d63ed6ff6597e293935f67d86f1c9ce1e899f74307ac0b69b809b`

The regional estimator strongly improved the target residual:

- older-adult MAE: **869902.3542103792 → 265671.80465012696** (69.46% lower)
- older-adult MAPE: **1.5309549149773176% → 0.3201636429905593%** (79.09% lower)
- overall MAE: **675885.909801408 → 524828.2724113448** (22.35% lower)
- overall RMSE: **985755.9948167036 → 816958.5631199381** (17.12% lower)
- overall MAPE: **0.619400242166686% → 0.3167024241699964%** (48.87% lower)

But the predeclared global-population gate failed:

- absolute global error: **314336.274353981 → 932618.5906333923 persons**

Therefore the frozen verdict is:

**NOT_BETTER_REGIONAL_OLDER_MORTALITY**

That failure is preserved. The model is not retuned on 2015.

## Cross-platform verification

Scientific workflow run: `35467696497`

- Linux job `105962944996`: PASS
- Windows job `105962945015`: PASS
- Linux artifact `10591733221`
- Windows artifact `10592070665`

All five scientific payload files are byte-identical between Linux and Windows. The ZIP container digests differ only because of archive metadata.

Standard CI on the execution head:
- pytest: **344 passed**
- Ruff: **PASS**
- mypy: **PASS** (87 source files)

Offline Linux qualification: **PASS**. Offline Windows qualification was still completing when the first evidence package was written; final-head qualification must be checked again before any exact-head PASS claim.

## What we learned

The regional older-adult mortality signal is real enough to reduce older-adult MAPE by about **79.09%** and overall MAPE by about **48.87%** on a frozen 2015 target. The failure is not local accuracy; it is aggregate population conservation. The candidate implies too few total deaths relative to the baseline and shifts the global population error from roughly 0.31 million to 0.93 million persons.

That suggests the next hypothesis: preserve the successful regional *shape* of older-adult mortality while normalizing its aggregate death mass before execution. That hypothesis must be tested on a new target year, not on 2015.

## Claim ceiling

This is a bounded historical walk-forward comparison only. It does not establish structural mortality identification, calibration, predictive validity, forecast skill, general scientific validation, deployment, or production effect.
