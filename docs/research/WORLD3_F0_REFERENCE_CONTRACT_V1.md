# World3 F0 Reference Contract V1

Date: 2026-09-17
Status: implementation reference contract
Branch: `impl/world3-f0-core-v1`
Parent scientific spine: `fbd9fedf7fcff0a7048f11ce1add2609611e1241`

## Purpose

F0 is a hostile control, not World Zero's preferred causal model. Its job is to preserve a classical World3 subject precisely enough that later market, innovation, energy, institutional, regional, and compound-risk structures must demonstrate that their extra complexity earns inclusion.

The name `World3` is not sufficiently precise for qualification. Multiple materially different generations exist. World Zero therefore binds a reference profile before it binds an implementation or accepts an output fixture.

## Canonical F0 subject

`WORLD3_1974_STANDARD_RUN` is the canonical F0 control.

It is bound to the technical model documented in Dennis L. Meadows et al., *Dynamics of Growth in a Finite World* (1974).

Pinned reference implementations are external oracles, not imported source:

- `cvanwynsberghe/pyworld3@cdfd0a8f3675c514f27ddc0e00c8d8bd4d1fefb8`
- `worlddynamics/WorldDynamics.jl@7315afe159dc23e2af5482c215669b2572545068`

PyWorld3 describes itself as implementing the 1974 technical model and its standard example plots the Figure 7-7 observables. WorldDynamics.jl independently implements the 1974 model and reproduces the corresponding published figure.

No PyWorld3 source is copied into World Zero. Its CeCILL-2.1 implementation is used only as an external reference oracle.

## World3-03 is separate

`WORLD3_03_2004_BAU1` is a compatibility reference, not the canonical F0 control.

The 30-Year Update revised World3 into World3-03. Later technical literature describes changed equations/variables, an adaptive technology sector, ecological-footprint and human-welfare variables. The pinned PyWorld3-03 and WorldDynamics.jl subjects provide independent implementation surfaces for this later generation.

World Zero MUST NOT:

- label a World3-03 run as `WORLD3_1974_DYNAMICS`;
- mix constants, tables or equations from the two generations while retaining either reference identity;
- treat agreement with either implementation as proof of causal validity;
- treat historical aggregate fit as unique validation of World3 structure.

## Standard comparison observables

Every F0 reference profile exposes exactly:

- `POPULATION`
- `INDUSTRIAL_OUTPUT_PER_CAPITA`
- `FOOD_PER_CAPITA`
- `NONRENEWABLE_RESOURCE_FRACTION`
- `PERSISTENT_POLLUTION_INDEX`

These are comparison surfaces, not the complete internal state.

## Numerical identity

A future frozen output fixture must bind at minimum:

- reference-profile digest;
- source implementation and exact commit;
- scenario identifier;
- initial-condition/constants/table digest;
- start/end years;
- timestep;
- delay/integration semantics;
- observable-extraction map;
- output digest.

A graph image or visual resemblance is not a numerical fixture.

## Qualification ladder

1. `REFERENCE_CONTRACT_PASS`: variant/provenance/profile semantics are internally valid.
2. `REFERENCE_ORACLE_CAPTURED`: an exact output fixture is captured from at least one pinned external implementation.
3. `CROSS_IMPLEMENTATION_CHECKED`: a second independent implementation agrees within preregistered tolerances or disagreement is preserved.
4. `WORLD_ZERO_F0_REPRODUCTION_PASS`: World Zero reproduces the frozen fixture under its own executable implementation.
5. `F0_BEHAVIORAL_QUALIFIED_WITHIN_SCOPE`: topology, implementation coverage, invariants, numerical convergence and declared comparison observables pass.

No rung implies the next.

## Research basis

The 2024 Journal of Industrial Ecology recalibration paper explicitly distinguishes PyWorld3's 1974 technical-model basis from the later World3-03 update. WorldDynamics.jl documents support for the original World3 plus later updated generations and reports reproduction of published figures.

The next implementation task is reference-oracle capture followed by a typed stock-flow numerical core. Equations are not admitted merely because an external package contains them; each World Zero relation must reconcile to the declared F0 topology and implementation-coverage contract.
