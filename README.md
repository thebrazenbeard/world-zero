# World Zero

World Zero is a research and modeling project to build a modern, transparent successor to the World3 system-dynamics model used in *The Limits to Growth*.

The goal is **not** to reproduce a predetermined collapse narrative or to assume that technology makes physical limits irrelevant. The goal is to construct a falsifiable world-systems model that can represent overshoot, adaptation, substitution, technological learning, demographic transition, inequality, environmental degradation, institutional response, and regional heterogeneity with explicit evidence and uncertainty.

## Current status

`RESEARCH_AND_ARCHITECTURE_V1` — no executable World Zero model is claimed yet.

Current research branch: `work/world-zero-research-architecture-v1`

The first implementation milestone will be a reproducible World3-compatible behavioral baseline plus a validation/provenance harness. New mechanisms will then be introduced incrementally and compared against that baseline.

## Core principles

- Scenarios are conditional model trajectories, not prophecies.
- Historical fit does not uniquely prove causal structure.
- Stocks, flows, delays and feedback loops remain first-class.
- Global aggregates are outputs of regional dynamics where practical, not substitutes for them.
- Physical, ecological, economic, demographic, distributional and institutional feedbacks are modeled separately before coupling.
- Technology, policy, fertility, prices and inequality must be explicitly endogenous or explicitly scenario-controlled; never silently both.
- Every empirical series carries source/provenance, definition, units, geography, time coverage, revision vintage and uncertainty.
- Dataset admission is explicit; candidate data do not become model evidence merely because they were downloaded.
- Identifiability is checked before calibration credit is granted.
- Every new sector or material feedback must have a cheap serious kill test; complexity must earn its place.
- Every simulation run is reproducible from source, data, parameter, scenario, solver and random-seed receipts.
- Validation is claim-specific. No model receives an unqualified label of "validated."
- Missing evidence remains `UNKNOWN`; required fields never justify fabricated precision.
- Superseded hypotheses and failed model structures remain reproducible historical subjects with explicit disposition.

## Research package

- `docs/research/LIMITS_TO_GROWTH_AND_WORLD3_BASELINE.md` — what the original work actually claimed, what World3 models, and what later comparisons do and do not establish.
- `docs/research/WORLD_ZERO_2026_EXTENSION_MATRIX.md` — modern systems and feedbacks to add or restructure.
- `docs/research/DATA_SOURCE_REGISTRY_V0.md` — candidate 2026 data sources and observables.
- `docs/research/VALIDATION_AND_FALSIFICATION_STRATEGY.md` — calibration, holdouts, sensitivity, shocks and hostile tests.
- `docs/research/CROSS_PROJECT_ENGINEERING_PATTERNS_2026-09-17.md` — generalized engineering patterns transferred after reviewing the owner’s repository portfolio, with private-project details deliberately excluded from this public repository.
- `docs/coordination/THIRTEEN_LANE_SYNTHESIS_2026-09-17.md` — contributions from One, Two, Three, Four, Five, Six, Seven, Eight, Nine, Thirteen, Masa, Mune and Hephaestus.
- `docs/superpowers/specs/2026-09-17-world-zero-model-design.md` — model architecture specification.
- `docs/superpowers/plans/2026-09-17-world-zero-model.md` — staged implementation plan.

## Reference implementation boundary

[`cvanwynsberghe/pyworld3`](https://github.com/cvanwynsberghe/pyworld3) is a useful behavioral/reference implementation of World3. It is licensed under CeCILL 2.1. World Zero should initially use it as a reference subject and comparison target rather than blindly copying source code.

## Governance

Research and planning on this branch do not authorize merge, publication claims, deployment, or claims of behavioral qualification. Those are separate gates.
