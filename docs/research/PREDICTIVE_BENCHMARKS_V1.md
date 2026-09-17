# World Zero Predictive Benchmarks V1

Date: 2026-09-17
Status: research/design contract

## Why benchmarks exist

A causal systems model can look sophisticated while adding little predictive value beyond simple extrapolation. Rival causal families are necessary but insufficient because they all share a modeling worldview.

World Zero therefore keeps **predictive benchmarks** outside the causal-family namespace. Benchmarks can beat causal models on prediction without receiving causal interpretation.

## B0 — persistence/trend benchmark

Purpose: provide the cheapest honest baseline appropriate to each observable.

Allowed forms, selected before holdout evaluation:

- last-observation persistence;
- linear trend fit on calibration period;
- log-linear trend where the observable definition justifies it;
- bounded logistic trend only when preregistered and not selected after holdout inspection.

B0 must not use hidden future information, external scenario forecasts or hand-tuned turning points.

Outputs:

- same observable IDs used by causal-model comparisons;
- prediction intervals where the chosen baseline supports them;
- exact calibration/holdout partition binding.

B0 has no causal topology and cannot receive causal qualification.

## B1 — reduced-form empirical benchmark

Purpose: test whether a bounded data-driven model predicts held-out dynamics better than the causal families without claiming mechanism truth.

Candidate V0 implementation:

- regularized vector autoregression, dynamic factor/state-space model or another preregistered reduced-form method appropriate to the available sample;
- training only on admitted observations from the calibration partition;
- hyperparameter selection nested entirely inside calibration data;
- no use of sector equations or causal-family parameters.

Required safeguards:

- feature set frozen before final holdout evaluation;
- transformations provenance-bound;
- sample-size-to-parameter ratio reported;
- regularization/hyperparameter search receipt retained;
- no causal language from coefficients alone;
- failure to extrapolate under interventions is expected and must be distinguished from ordinary historical forecasting.

## Benchmark role in comparisons

Benchmarks answer different questions from causal families.

Example:

- If F1 and F3 both beat B0/B1 on temporal and regional holdouts, that is evidence the causal structure may add predictive value.
- If B1 beats every causal family on ordinary historical holdouts, World Zero must report that result rather than declaring the causal models superior because they are interpretable.
- If a causal family performs similarly to B1 but uniquely survives intervention/shock tests with physically valid invariants, that difference can still justify causal-model use for that scoped task.

## Benchmark limitations

B0/B1 are not expected to answer:

- novel policy interventions outside historical support;
- conservation-valid counterfactual physical reallocations;
- unprecedented technology substitutions;
- structural regime shifts not represented in training data.

Those limitations are not excuses to omit benchmarks. They define where causal structure is supposed to earn its value.

## Qualification language

Allowed benchmark comparison statements include:

- `OUTPERFORMS_B0_ON_DECLARED_HOLDOUT`
- `OUTPERFORMS_B1_ON_DECLARED_HOLDOUT`
- `NO_PREDICTIVE_GAIN_OVER_BENCHMARK`
- `BENCHMARK_SUPERIOR_ON_HISTORICAL_HOLDOUT`
- `INTERVENTION_COMPARISON_NOT_APPLICABLE_TO_BENCHMARK`

No benchmark result may be translated automatically into a claim that causal mechanisms are true or false.
