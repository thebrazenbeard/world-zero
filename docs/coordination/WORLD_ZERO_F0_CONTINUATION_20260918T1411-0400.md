# WORLD ZERO F0 CONTINUATION — 2026-09-18 14:11 ET

Status: durable continuation checkpoint only. This file does not promote provisional oracle evidence or alter scientific qualification.

## Branch / subject

Active branch: `impl/world3-f0-core-v1`

Scientific/source head before this continuation note:
`8461b8c68119a61d97092aa165f57af4090128ec`

Parent qualified scientific spine:
`fbd9fedf7fcff0a7048f11ce1add2609611e1241`

The F0 branch is isolated from the qualified V2 scientific spine.

## F0 reference decision

Canonical F0 control:
- profile: `WORLD3_1974_STANDARD_RUN`
- variant: `WORLD3_1974_DYNAMICS`
- scenario: `STANDARD_RUN`
- primary technical lineage: Meadows et al., *Dynamics of Growth in a Finite World* (1974)

World3-03 is separate:
- profile: `WORLD3_03_2004_BAU1`
- role: compatibility reference
- MUST NOT impersonate the 1974 canonical F0 control.

Scientific reference identity and numerical oracle execution identity are deliberately separate.

Pinned external reference implementations:
- `cvanwynsberghe/pyworld3@cdfd0a8f3675c514f27ddc0e00c8d8bd4d1fefb8`
- `worlddynamics/WorldDynamics.jl@7315afe159dc23e2af5482c215669b2572545068`
- World3-03 compatibility: `TimSchell98/PyWorld3-03@1f1b2f40637e2c77202df8ed12d7f9fb225340d7`

No PyWorld3 implementation source is copied into World Zero. External implementations are oracle/reference surfaces only.

## Corrected PyWorld3 standard-run semantics

Pinned source inspection found a documentation/code discrepancy: the prose/docstring suggests a one-year default timestep, but the executable `World3.__init__` standard run defaults to `dt=0.5`.

Bound provisional execution semantics:
- year_min: 1900
- year_max: 2100
- dt: 0.5 years
- inclusive endpoint
- sample_count: 401
- delay method: Euler
- run mode: checked/rescheduling path (`fast=False`)
- default constants/tables
- initialization:
  1. `init_world3_constants`
  2. `init_world3_variables`
  3. `set_world3_table_functions`
  4. `set_world3_delay_functions`
  5. `run_world3`

Five comparison observables:
- POPULATION -> `pop`
- INDUSTRIAL_OUTPUT_PER_CAPITA -> `iopc`
- FOOD_PER_CAPITA -> `fpc`
- NONRENEWABLE_RESOURCE_FRACTION -> `nrfr`
- PERSISTENT_POLLUTION_INDEX -> `ppolx`

## Provisional oracle discovery evidence

Workflow:
- run: `35292233360`
- workflow: `Discover World3 oracle environment`
- exact head: `8461b8c68119a61d97092aa165f57af4090128ec`
- conclusion: SUCCESS

Artifact:
- artifact id: `10526652366`
- name: `world3-pyworld3-provisional-8461b8c68119a61d97092aa165f57af4090128ec`
- artifact digest: `sha256:b6f1567927863a1c8e6b06b106a42d6829fd70fb16bb8a6294be512d8b3a3045`
- expiry at observation: 2026-10-02T00:41:50Z

Captured metadata:
- capture_status: `PROVISIONAL_ENV_DISCOVERY`
- fixture SHA-256: `6ef0f965ea088534cee95f81ad81bcc58e224b61f8c101838526510055d2b450`
- oracle spec file SHA-256: `42b65fbb772021823251992735671070439a608cc065ed631fd2c23cc732e149`
- profile file SHA-256: `133f9e22afb585e8ab879dbb8b4871a35b396ab69657bc1204fda93585197cdf`
- World3 table file SHA-256: `3204ec9a7183c78d22b1600b924d27806ea8e9d9041159f332b09fd09c8b2dd4`
- observed checkout: `cdfd0a8f3675c514f27ddc0e00c8d8bd4d1fefb8`
- sample_count: 401

Resolved environment:
- Python 3.12.14
- PyWorld3 1.1
- NumPy 2.5.3
- SciPy 1.18.1
- Matplotlib 3.11.2

Full provisional environment.freeze SHA-256:
`4a30d04fe996b04966b41beca5ce5b0b1c4d67b405db22ca438bd4c7b1748a22`

The provisional environment freeze contained:
`annotated-types==0.8.0, ast_serialize==0.11.2, colorama==0.4.6, contourpy==1.4.0, cycler==0.12.1, fonttools==4.65.0, iniconfig==2.3.0, kiwisolver==1.5.1, librt==0.15.0, matplotlib==3.11.2, mypy==2.3.1, mypy_extensions==1.1.0, numpy==2.5.3, packaging==26.3, pathspec==1.1.1, pillow==12.3.0, pluggy==1.6.0, pydantic==2.13.4, pydantic_core==2.46.4, Pygments==2.21.0, pyparsing==3.3.2, pytest==9.0.2, python-dateutil==2.9.0.post0, PyYAML==6.0.3, ruff==0.16.8, scipy==1.18.1, six==1.17.0, types-PyYAML==6.0.12.20260906, typing-inspection==0.4.4, typing_extensions==4.16.0`.

This evidence remains PROVISIONAL. It is not a canonical reference fixture.

## Current F0 qualification state

Older exact head `56c5e08641baeb1ab8d0d3f2ff8a06d2e8d8b3ca` had a successful native F0 qualification, but later contract/tool changes superseded that subject.

Latest offline qualification run before the provisional capture:
- run: `35292232610`
- head: `a665199c1827f6dc9b334ba5c5afcea193b0c9b5`
- Linux and Windows both reconstructed offline and passed pytest.
- both stopped at Ruff; mypy did not run.

Exact Ruff findings:
1. import ordering in `tests/reference/test_world3_reference.py`;
2. B009 in `tools/capture_world3_oracle.py`: constant `getattr(world3_module, "World3")` should use direct attribute access.

Therefore the current F0 branch has NO current exact-head native qualification claim.

## Next actions

1. Freeze the discovered scientific dependency environment into source-controlled oracle execution identity.
2. Bind the environment/lock digest into `WORLD3_ORACLE_EXECUTION_V1`.
3. Fix the two exact Ruff findings without weakening gates.
4. Rerun the full offline Linux/Windows F0 qualifier on the new exact head.
5. Rerun the external oracle capture from exact frozen dependency versions with status `FROZEN_ORACLE_CAPTURE`.
6. Compare the frozen capture digest/values against the provisional discovery; preserve any divergence.
7. Only after that admit a reference fixture.
8. Inspect/freeze an independent WorldDynamics.jl execution identity and cross-check.
9. Then implement the typed World Zero stock-flow numerical core and reproduce the frozen F0 fixture.

Do not promote historical fit or agreement with one implementation into causal validation.

## Boundaries

No merge, deployment, provider mutation, paid compute, or runtime installation is authorized by this checkpoint.
