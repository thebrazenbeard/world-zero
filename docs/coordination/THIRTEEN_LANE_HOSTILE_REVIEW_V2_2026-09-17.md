# World Zero Thirteen-Lens Hostile Review V2 — 2026-09-17

Status: local role-lens review pending genuinely independent Bus responses

## Important boundary

This document applies the established BT2 role lenses in one execution terminal. It is **not** evidence that thirteen independent model processes reviewed the subject. A Bus request has been routed so separate role chats can later return independently authored findings against the exact subject.

The purpose here is immediate self-attack: identify design defects before implementation momentum makes them expensive.

## One — integration / scope

Finding: the project was drifting from “scientific comparison platform” toward “complete world simulator.” The revised architecture is better, but governance itself can become a second form of overbuilding.

Correction:

- keep the scientific spine minimal;
- require every registry/schema field to serve a specific falsification, reproducibility or provenance need;
- do not build rich database/control-plane infrastructure before file-based contracts become insufficient.

## Two — architecture / hidden coupling

Finding: `CAUSAL_TOPOLOGY_V1` represented relations as single `from -> to` edges. Many causal functions are genuinely higher-order and nonseparable. Converting a multi-input equation into several pairwise arrows can imply independent causal effects that the equation does not actually contain.

Correction:

- supersede the pairwise relation contract with a V2 hyperedge-compatible relation using `inputs[]` and `outputs[]`;
- preserve pairwise relations as the one-input/one-output special case;
- record functional-form class and lag separately from graph connectivity.

## Three — provenance / observation / identifiability

Finding: source references in the topology are not enough to prevent a claim from being supported by several highly correlated datasets that all derive from the same underlying measurement system.

Correction:

- dataset/observation manifests need lineage-family or upstream-source IDs;
- validation must be able to flag apparent multi-source confirmation that is actually one upstream series transformed several ways;
- observation covariance/correlation must remain representable where material.

## Four — hostile premise challenge

Finding: F0–F7 all remain variants of explicit causal stock-flow/system models. Even a “fair” contest among them could overstate the value of the entire modeling paradigm.

Correction:

Add non-causal predictive benchmarks outside the causal-family namespace:

- `B0_PERSISTENCE_TREND` — naive persistence/trend/seasonless baseline appropriate to each observable;
- `B1_REDUCED_FORM_EMPIRICAL` — regularized VAR/state-space or similarly bounded empirical benchmark using only admitted observations.

These benchmarks do not receive causal interpretation. Their role is to test whether causal complexity produces real out-of-sample gain.

## Five — earth systems / thresholds

Finding: threshold/tipping mechanisms are scientifically important but often weakly located in historical global data. If calibrated freely they can become collapse generators with enormous narrative leverage.

Correction:

- thresholds default to rival/scenario structures, not F7;
- threshold location/range must come from subsystem evidence or remain deep uncertainty;
- always compare a smooth null;
- historical fit alone cannot qualify a tipping relation.

## Six — demography / human behavior

Finding: fertility, education, income, health and security are mutually entangled. A neat directional loop can misstate reciprocal causation and cultural heterogeneity.

Correction:

- separate prediction from causal language in demographic relations;
- use regional/historical contrasts and intervention-quality evidence where available;
- retain structural alternatives for fertility response rather than one universal function.

## Seven — economy / distribution / prices

Finding: a market-adaptive family could accidentally become “markets work” encoded as a model, while the institutional family could become the opposite worldview.

Correction:

- F1 must contain failure modes: rationing, low-income demand destruction, delayed investment, concentrated suppliers and non-substitutable inputs;
- use relative/real scarcity signals in V0 rather than attempting a full nominal monetary system;
- no family is allowed to turn its ideological premise into an untestable latent coefficient.

## Eight — energy / technology / materials

Finding: explicit net-energy accounting can double-count energy burden if energy-sector own use is already embodied in capital/material/industry energy demand.

Correction:

- define an energy-accounting boundary and reconciliation identity before F3 implementation;
- test that energy invested in energy supply appears exactly once;
- separate energy carrier quality/conversion loss from EROI-style investment burden;
- infrastructure build queues and embodied energy must reconcile.

## Nine — food / water / trade / regional conservation

Finding: regional trade can double-count physical resources when production-based and consumption-based accounts are mixed. Virtual water, embodied energy/materials and food stocks can cross boundaries together.

Correction:

- every traded physical flow has one origin debit and one destination credit;
- choose production-accounting versus consumption-footprint metrics explicitly;
- global conservation tests must survive arbitrary regional routing.

## Thirteen — institutions / governance / ideology leakage

Finding: variables such as trust, state capacity or legitimacy are especially vulnerable to becoming researcher preference disguised as causal state.

Correction:

- each institutional proxy must declare observed components versus latent inference;
- avoid one-dimensional “good governance” scores as causal truth;
- test wrong-policy and high-capacity-but-wrong-model cases, not just low-capacity failure.

## Masa — root cause / runtime falsification

Finding: topology digest + implementation symbol reference does **not** prove the executable model actually implements the declared topology. Code can contain hidden couplings, omit declared relations or bind a relation ID to behavior with the wrong sign/function.

Correction:

- runtime/sector modules must register implemented relation IDs;
- compilation produces an `IMPLEMENTATION_COVERAGE` artifact mapping declared nodes/relations to code symbols;
- fail if a required active relation has no binding;
- add behavioral micro-tests for relation polarity/limiting cases;
- keep topology identity separate from implementation qualification.

## Mune — validation / reproducibility

Finding: `ROBUST_ACROSS_FAMILIES` can still be gamed if the tolerance/directional success rule is chosen after results are seen.

Correction:

- introduce frozen `ComparisonProtocol` before family execution;
- bind claim ID, family/benchmark set, data partitions, metric, tolerance/direction rule and missing-run policy;
- include protocol digest in comparison receipts;
- after-the-fact exploratory comparisons remain labeled exploratory.

## Hephaestus — implementation / exact binding

Finding 1: V1 required `source_commit` inside the topology object. A commit cannot straightforwardly contain a file that already names the commit containing itself. This was a self-referential exact-binding bug.

Correction already applied:

- remove self commit from topology content;
- Git/tree binding belongs in external family/run receipts.

Finding 2: scientific contracts risk getting ahead of executable validators.

Correction:

- implement schema validation/canonicalization before sectors;
- every normative schema gets negative tests;
- avoid a database until file contracts prove insufficient.

## Cross-lens defect register

### D1 — Pairwise topology overclaims structure

Severity: HIGH before implementation.

Disposition: create hyperedge-compatible `CAUSAL_TOPOLOGY_V2`; preserve V1 as superseded research provenance.

### D2 — Causal-family-only benchmark bias

Severity: HIGH for validation claims.

Disposition: add B0/B1 non-causal predictive benchmarks. They cannot receive causal qualification.

### D3 — Declared topology can drift from executable behavior

Severity: HIGH.

Disposition: implementation coverage artifact + relation micro-tests + exact code binding.

### D4 — Post-hoc robustness threshold

Severity: HIGH.

Disposition: frozen comparison protocol required before qualification-grade execution.

### D5 — Net-energy double counting

Severity: MEDIUM/HIGH in F3.

Disposition: explicit energy-accounting reconciliation identity and one-count rule.

### D6 — Correlated-source pseudo-confirmation

Severity: MEDIUM.

Disposition: upstream lineage IDs and correlated-observation awareness.

### D7 — Regional embodied-flow double counting

Severity: MEDIUM/HIGH in F5.

Disposition: trade conservation and production/consumption accounting boundary.

### D8 — Threshold narrative leverage exceeds evidence

Severity: MEDIUM/HIGH.

Disposition: smooth null + external evidence range + deep-uncertainty status by default.

## Revised immediate frontier

Before sector implementation:

1. supersede causal topology V1 with hyperedge-capable V2;
2. define benchmark-model contract B0/B1;
3. define frozen comparison protocol schema;
4. define topology-to-implementation coverage contract;
5. update scientific-spine implementation plan to V2;
6. only then begin executable scientific-spine code.

This review intentionally increases uncertainty in places where the earlier design looked cleaner than the evidence justified.
