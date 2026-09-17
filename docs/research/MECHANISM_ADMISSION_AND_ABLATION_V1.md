# World Zero Mechanism Admission and Ablation V1

Date: 2026-09-17
Status: normative research/design gate for future implementation

## Why this exists

World Zero can fail by being too simple, but it can also fail by becoming a giant explain-everything machine with enough parameters to reproduce any history after the fact.

A plausible mechanism is not automatically an admissible mechanism.

This gate controls promotion from:

`IDEA -> RIVAL_FAMILY_EXPERIMENT -> ADMITTED_COMPONENT -> F7_MINIMAL_SYNTHESIS`

The rival families are intentionally allowed to contain mechanisms that have not earned universal inclusion. F7 is not.

## Admission packet

Every proposed mechanism must have a compact packet containing:

- `mechanism_id`;
- plain-language causal proposition;
- affected nodes/relations;
- physical/social/economic interpretation;
- units and conservation implications;
- evidence class;
- source pointers;
- rival/null mechanism;
- parameter or structural uncertainty;
- identifiability assessment;
- motivating residual or failure case;
- preregistered kill test;
- holdout target;
- ablation expectation;
- computational cost class;
- current disposition.

Allowed dispositions:

- `RESEARCH_ONLY`
- `RIVAL_FAMILY_ONLY`
- `ADMITTED_COMPONENT`
- `F7_CANDIDATE`
- `F7_ADMITTED`
- `REJECTED`
- `SUPERSEDED`
- `UNIDENTIFIABLE_WITH_CURRENT_EVIDENCE`

## Gate A — semantic and boundary clarity

Before fitting anything:

1. Is the mechanism defined precisely enough that two implementers would build the same causal claim?
2. Are system boundaries explicit?
3. Are units and sign conventions explicit?
4. Does the mechanism conserve matter/energy/population where conservation applies?
5. Is the claimed variable directly observable, derived, inferred or latent?

Failure at Gate A blocks implementation beyond a disposable research spike.

## Gate B — observational identifiability preflight

Ask whether the available observation surface can distinguish the mechanism from plausible rivals.

Required checks:

- Which observables respond uniquely or differentially to this mechanism?
- Could another parameter or mechanism produce the same observed trajectory?
- Are the proposed parameters separately identifiable or only a combination of them?
- Does aggregation destroy the distinction?
- Does the calibration data include an intervention, shock, regional contrast or temporal regime that excites the mechanism?

Possible outcomes:

- `IDENTIFIABLE_ENOUGH_FOR_TEST`
- `WEAKLY_IDENTIFIABLE`
- `UNIDENTIFIABLE_WITH_CURRENT_EVIDENCE`
- `OBSERVATION_MODEL_INADEQUATE`

Weak or failed identifiability does not mean the mechanism is false. It means World Zero must not pretend the data selected it.

## Gate C — cheapest discriminating kill test

Before full integration, design the cheapest valid test capable of making the mechanism unnecessary, wrong or materially weaker.

Examples:

- **Rebound:** compare null, low and high rebound against held-out energy-demand responses after identifiable efficiency changes.
- **Net energy:** test whether gross-energy accounting leaves systematic residuals in energy-sector own-use, investment burden or useful-energy availability that net-energy accounting improves.
- **Network topology:** compare aggregate-capacity and concentration-aware variants on known hub disruptions or regional trade shocks.
- **Innovation:** compare monotonic learning, saturating learning and competing-technology diffusion on held-out adoption/cost trajectories.
- **Policy perception:** compare omniscient state feedback with lagged/noisy observation rules on policy-response timing.

If no plausible observation can discriminate the mechanism, it remains structural uncertainty rather than an established component.

## Gate D — holdout value

The mechanism must improve or materially alter at least one preregistered out-of-sample target without unacceptable regressions elsewhere.

Valid targets include:

- temporal holdout;
- regional holdout;
- variable holdout;
- shock/recovery holdout;
- structural negative control;
- turning-point timing;
- uncertainty calibration;
- conservation/invariant behavior.

Historical in-sample fit by itself does not pass Gate D.

## Gate E — ablation necessity

After integration, remove or neutralize the mechanism while holding the rest of the exact subject constant.

Ask:

- Does the target claim change?
- Does a holdout materially worsen?
- Does an invariant fail?
- Does uncertainty widen in a meaningful way?
- Can a simpler relation reproduce the same gain?

A mechanism that cannot survive ablation review may remain in a specialized rival family, but it does not enter F7 merely because it is realistic.

## Gate F — rival-family robustness

A component is not considered robust simply because it improves one family.

For a target claim, test whether the conclusion persists under plausible structural rivals.

Example:

`Rapid electrification remains feasible under F1 market adaptation but fails under F3 net-energy/material bottleneck.`

That result is `FAMILY_SENSITIVE`, not a disagreement to be averaged away.

## Gate G — complexity and overfitting budget

Every admitted mechanism spends complexity budget.

Track at least:

- number of new dynamic states;
- number of calibrated parameters;
- number of lookup functions;
- number of latent variables;
- number of external scenario inputs;
- additional runtime/ensemble cost;
- identifiability class.

Adding ten weakly identified parameters for a tiny in-sample gain is presumptively a rejection.

## Gate H — numerical integrity

A scientifically useful mechanism that only works at one arbitrary timestep or solver setting has not passed.

Required checks where applicable:

- timestep convergence;
- alternate solver comparison;
- conservation drift;
- delay discretization sensitivity;
- threshold hysteresis behavior;
- stochastic seed/ensemble stability;
- extreme-parameter boundedness.

Numerical artifacts are not world dynamics.

## Gate I — negative-transfer / unintended coupling

A mechanism added for one domain must not silently alter unrelated outputs through accidental implementation coupling.

Examples:

- enabling institutional perception noise must not change carbon conservation;
- changing income distribution must not create or destroy population;
- switching a solver must not change scenario semantics;
- adding a trade network must not duplicate global resource stocks.

Unexpected cross-domain effects trigger root-cause analysis before qualification.

## F7 promotion rule

A mechanism may enter `F7_MINIMAL_ADAPTIVE_SYNTHESIS` only when:

1. Gate A passes;
2. Gate B is at least `WEAKLY_IDENTIFIABLE`, unless the mechanism is required for a hard physical/accounting invariant;
3. a preregistered Gate C kill test exists;
4. Gate D shows claim-relevant holdout value or invariant necessity;
5. Gate E shows nontrivial ablation value;
6. Gate F documents structural sensitivity;
7. complexity cost is proportionate to gain;
8. numerical integrity passes;
9. no unresolved negative-transfer defect remains.

Exceptions for conservation/accounting structure must be explicit and do not grant causal-validation credit.

## Removal rule

F7 membership is revocable.

Later evidence can demote an admitted mechanism when:

- better data contradict it;
- a simpler mechanism reproduces its useful behavior;
- a prior gain was discovered to be leakage or overfit;
- its parameters become non-identifiable after data revisions;
- its effect disappears under corrected numerical methods;
- its original target claim is no longer scientifically relevant.

Demotion preserves the old exact subject as `SUPERSEDED`; it does not rewrite history.

## Research priority heuristic

When choosing what to test next, prioritize mechanisms with high product of:

`claim importance × plausible effect size × current uncertainty × discriminating-data availability`

and penalize:

`implementation complexity × identifiability weakness × computational cost`.

This is a prioritization heuristic, not a score for scientific truth.
