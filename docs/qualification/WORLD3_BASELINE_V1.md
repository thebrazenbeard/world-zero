# World3 Baseline V1 Qualification

Date: 2026-09-17
Status: external control subject frozen; clean-room F0 implementation not yet qualified

## Purpose

This artifact freezes the external World3-compatible control used to test World Zero F0.
It is a behavioral reference, not evidence that World3 is causally correct and not a
prediction of a dated future outcome.

World Zero does not copy the PyWorld3 implementation into its package. The control is
executed out-of-process through the public PyWorld3 API and is bound to an exact Git
commit before execution.

## Reference identity

- Repository: https://github.com/cvanwynsberghe/pyworld3
- Git commit: cdfd0a8f3675c514f27ddc0e00c8d8bd4d1fefb8
- PyWorld3 reported version: 1.1
- License: CeCILL-2.1

## Reference runtime used for the frozen fixture

- Python: CPython 3.12.10
- NumPy: 2.5.3
- SciPy: 1.18.1
- Reference source lived outside the World Zero repository.
- World Zero package dependencies were unchanged.

## Standard-run configuration

- year_min = 1900
- year_max = 2100
- dt = 0.5 year
- pyear = 1975
- iphst = 1940
- default World3 constants
- default World3 nonlinear lookup tables
- delay method: euler
- run_world3(fast=False)

## Frozen trajectory artifact

Path: tests/baseline/fixtures/world3_standard_run.csv

Columns:

- year
- population (pop)
- nonrenewable-resource fraction remaining (nrfr)
- food per capita (fpc)
- industrial output per capita (iopc)
- persistent-pollution index (ppolx)

Rows: 401 data rows.

SHA-256: 31d3f493e942e3f0eadf8828bf51ec968745e19b12399dc382138e89a67a2d68

## Reproduction check

The World Zero exact-commit-bound subprocess adapter re-ran the pinned reference and
compared it with the frozen CSV. The normalized maximum trajectory error was:

4.528806913393279e-12

The small non-zero value is from decimal serialization of the CSV, not a different
reference trajectory.

Selected standard-run checks from the pinned reference:

- population peak: 2027.0, approximately 7.062043157 billion
- industrial output per capita peak: 2012.5, approximately 395.296
- food per capita peak: 2009.0, approximately 505.431
- persistent-pollution index peak: 2034.5, approximately 11.0018

## Qualification boundary

This establishes that World Zero can invoke and provenance-bind the external World3
control and reproduce the frozen control artifact.

It does **not** establish that:

- World Zero has independently implemented the World3 equations;
- World3 is empirically validated as a unique causal model;
- the standard-run dates are predictions;
- any later World Zero modernization is superior.

The next F0 gate is an independent World Zero implementation whose trajectories are
compared against this frozen control before modernization mechanisms are admitted.
