# World3 F0 Reference Contract V1

Date: 2026-09-17
Status: implementation reference contract
Branch: `impl/world3-f0-core-v1`
Parent scientific spine: `fbd9fedf7fcff0a7048f11ce1add2609611e1241`

## Purpose

F0 is a hostile control, not World Zero's preferred causal model. Its job is to preserve a classical World3 subject precisely enough that later market, innovation, energy, institutional, regional, and compound-risk structures must demonstrate that their extra complexity earns inclusion.

The name `World3` is not sufficiently precise for qualification. Multiple materially different generations exist. World Zero therefore binds scientific reference identity separately from numerical-oracle execution identity.

## Canonical F0 scientific subject

`WORLD3_1974_STANDARD_RUN` is the canonical F0 control.

It binds:

- variant: `WORLD3_1974_DYNAMICS`;
- scenario: `STANDARD_RUN`;
- primary technical source: Dennis L. Meadows et al., *Dynamics of Growth in a Finite World* (1974);
- the five declared comparison observables.

It deliberately does **not** contain solver, timestep, implementation commit, delay algorithm, or package-specific variable names. Those are execution identity.

## World3-03 is separate

`WORLD3_03_2004_BAU1` is a compatibility reference, not the canonical F0 control.

The 30-Year Update revised World3 into World3-03. Later technical literature describes changed equations/variables and an adaptive technology sector. World Zero MUST NOT:

- label a World3-03 run as `WORLD3_1974_DYNAMICS`;
- mix constants, tables or equations from the two generations while retaining either reference identity;
- treat agreement with an implementation as proof of causal validity;
- treat historical aggregate fit as unique validation of World3 structure.

## Standard comparison observables

Every World3 reference profile exposes exactly:

- `POPULATION`
- `INDUSTRIAL_OUTPUT_PER_CAPITA`
- `FOOD_PER_CAPITA`
- `NONRENEWABLE_RESOURCE_FRACTION`
- `PERSISTENT_POLLUTION_INDEX`

These are comparison surfaces, not the complete internal state.

## Oracle execution identity

External implementations are transient numerical oracles. They are not imported into World Zero source.

The first oracle spec is `WORLD3_1974_PYWORLD3_STANDARD`, bound to:

`cvanwynsberghe/pyworld3@cdfd0a8f3675c514f27ddc0e00c8d8bd4d1fefb8`

Inspection of that exact source exposed an important documentation/code discrepancy: the class docstring says the default timestep is 1 year, but `World3.__init__` actually defaults to `dt=0.5`. The standard example calls `World3()`, so the executable standard run uses:

- start year: 1900;
- end year: 2100;
- timestep: 0.5 years;
- endpoint included;
- sample count: 401;
- delay method: default Euler;
- run mode: checked/rescheduling path (`fast=False`);
- default constants and tables;
- initialization order: constants -> variables -> tables -> delays -> run.

This mismatch is exactly why execution evidence is source-bound rather than inferred from prose.

The PyWorld3 observable bindings are:

- `POPULATION -> pop`
- `INDUSTRIAL_OUTPUT_PER_CAPITA -> iopc`
- `FOOD_PER_CAPITA -> fpc`
- `NONRENEWABLE_RESOURCE_FRACTION -> nrfr`
- `PERSISTENT_POLLUTION_INDEX -> ppolx`

PyWorld3 is CeCILL-licensed. World Zero does not copy its implementation source. It uses the pinned repository only as an external oracle and stores independently generated output fixtures/provenance.

WorldDynamics.jl at `7315afe159dc23e2af5482c215669b2572545068` remains the intended independent cross-implementation surface. Its numerical execution identity will be frozen separately after its exact standard-run invocation and solver semantics are inspected; it is not forced into PyWorld3's execution profile.

## Future frozen output fixture

A captured oracle fixture must bind at minimum:

- scientific reference-profile digest;
- oracle-execution-spec digest;
- exact implementation commit;
- constants/table/initial-condition evidence;
- time grid and sample count;
- observable-extraction map;
- serialized output digest.

A graph image or visual resemblance is not a numerical fixture.

## Qualification ladder

1. `REFERENCE_CONTRACT_PASS`: scientific reference and oracle-execution contracts are internally valid.
2. `REFERENCE_ORACLE_CAPTURED`: exact numeric output is captured from a pinned oracle.
3. `CROSS_IMPLEMENTATION_CHECKED`: a second independent implementation agrees within preregistered tolerances or disagreement is preserved.
4. `WORLD_ZERO_F0_REPRODUCTION_PASS`: World Zero reproduces the frozen fixture under its own implementation.
5. `F0_BEHAVIORAL_QUALIFIED_WITHIN_SCOPE`: topology, implementation coverage, invariants, numerical convergence and declared observables pass.

No rung implies the next.

## Research basis

The 2024 Journal of Industrial Ecology recalibration paper explicitly distinguishes PyWorld3's 1974 technical-model basis from the later World3-03 update. WorldDynamics.jl documents support for the original World3 plus later updated generations and reports reproduction of published figures.

The next task is exact PyWorld3 oracle capture, followed by an independently implemented typed stock-flow numerical core. Equations are not admitted merely because an external package contains them; every World Zero relation must reconcile to the declared F0 topology and implementation-coverage contract.
