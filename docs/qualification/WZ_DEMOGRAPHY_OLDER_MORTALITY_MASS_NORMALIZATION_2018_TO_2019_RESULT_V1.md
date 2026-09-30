# World Zero Older-Mortality Mass-Normalization Walk-Forward V1

Status: **EXECUTED / CROSS-PLATFORM REPRODUCED / NOT_BETTER_MASS_NORMALIZED / HISTORICAL_WALKFORWARD_COMPARISON_ONLY**

The 2018→2019 contract was frozen before this lane inspected 2019 at commit `848ddbdc35eb285a2d74e861b8c752603abaaa47`. The candidate preserved the pre-target regional older-adult mortality shape and multiplied every regional rate by one common factor (`1.025210372140686`) so aggregate older-adult death mass at the 2018 initial state matched the global-shape reference before either arm saw the target.

Exact executed/final scientific head: `9acf067d6c445d1dbd402f7e86d65d1acbd31b01`.

## Result

The candidate improved absolute global error:

- baseline: **2,321,645.674 persons**
- mass-normalized: **1,344,365.307 persons**

But it damaged the predeclared distributional/error gates:

- MAE: **461,357.015 → 485,789.024**
- RMSE: **723,828.921 → 736,979.310**
- MAPE: **0.259995% → 0.296047%**
- older-adult MAE: **202,216.427 → 299,944.464**
- older-adult MAPE: **0.305986% → 0.450193%**

Therefore the frozen verdict is **NOT_BETTER_MASS_NORMALIZED**.

No tuning was performed against 2019 after this result.

## Verification

Exact-head standard CI `35470778449`:
- **347/347 tests PASS**
- Ruff PASS
- mypy PASS (89 source files)

Exact-head offline qualification `35470778463`:
- Linux PASS
- Windows PASS

Exact-head scientific workflow `35470778478`:
- Linux job `105971236958`: PASS
- Windows job `105971236888`: PASS
- all five scientific payloads are byte-identical across platforms

Scientific artifact ZIPs:
- Linux `10592648131`: SHA-256 `c6b7035352733ec7beb85d8f3bf33cb5d22454f535491141bc9182e4b57f91bd`
- Windows `10592463468`: SHA-256 `adc41aab564bab1cac06f5f45f4059382515b746b390a8fa15d4d84d5a914a50`

The container ZIP digests differ, but the scientific files are identical; the durable cross-platform receipt records each payload digest.

## Scientific lesson

The previous failure was not repaired by a single global rescaling. The regional mortality shape and aggregate mass constraint pull in different directions under this estimator. The next candidate must derive a regional/global shrinkage rule from earlier historical folds only and test that frozen rule on a different target year. Neither 2015 nor 2019 may be retuned and then represented as fresh validation.

## Claim ceiling

This establishes only a bounded historical walk-forward comparison. It does not establish structural mortality identification, calibration, general predictive validity, forecast skill, scientific validation, deployment, production effect, or merge authority.
