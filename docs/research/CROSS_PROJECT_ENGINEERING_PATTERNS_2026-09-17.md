# Cross-Project Engineering Patterns Applied to World Zero

Date: 2026-09-17
Status: research/design input

## Scope and privacy boundary

Before extending the World Zero design further, the owner’s accessible GitHub repository portfolio was reviewed at breadth-first level for reusable engineering patterns. The review covered 49 repositories. Three were empty at the time of inspection; several others were intentionally thin or domain-specific and did not contribute useful mechanisms.

Most of those repositories are private. This public document therefore records only generalized engineering patterns that are useful to World Zero. It deliberately does not enumerate private repositories, quote private material, or expose private project-specific facts.

Repository review is an idea source, not authority over World Zero. A pattern is adopted only when it improves the model’s scientific or engineering discipline.

## Adopted patterns

### 1. Separate source, calibration, execution, and qualification

World Zero must not collapse these states:

- model source exists;
- data are admitted;
- parameters are calibrated;
- a simulation ran successfully;
- a scenario reproduced a historical pattern;
- a holdout validation passed;
- a policy experiment produced a result;
- a causal interpretation is supported.

Each is a separate claim with separate evidence.

### 2. Exact-subject binding

Every material run, calibration, comparison, and qualification result must bind the exact subject that produced it:

- source commit;
- model configuration;
- dataset manifest/version;
- parameter set;
- initial conditions;
- scenario/intervention definition;
- numerical solver and step configuration;
- random seed or ensemble identity where applicable.

A PASS on one subject does not silently transfer after any of those inputs move.

### 3. Evidence classes are first-class model metadata

World Zero should distinguish at minimum:

- `OBSERVED` — directly measured or retrieved empirical quantity;
- `DERIVED` — mechanically transformed from observed inputs;
- `INFERRED` — estimated latent quantity or fitted relationship;
- `HYPOTHESIS` — proposed causal structure not yet established;
- `DISPUTED` — materially contested interpretation or estimate;
- `UNKNOWN` — required value or relationship not honestly established;
- `SUPERSEDED` — historical model/data subject retained for provenance.

A required field does not authorize fabricated precision. `UNKNOWN` is preferable to an invented number.

### 4. Dataset admission instead of casual downloading

A dataset moves through an explicit lifecycle:

`CANDIDATE -> SOURCE_VERIFIED -> RIGHTS/TERMS_CHECKED -> SCHEMA_MAPPED -> QUALITY_CHECKED -> ADMITTED`

Admission records should preserve source identity, retrieval date, release/version, units, transformations, geographic and temporal coverage, known revisions, uncertainty, and licensing/terms.

Historical releases should remain reproducible after newer revisions arrive.

### 5. Append-only evidence and contradiction history

New evidence should not silently rewrite earlier assumptions, calibrations, or scenario conclusions.

Maintain append-oriented records for:

- dataset revisions;
- parameter revisions;
- structural-model revisions;
- failed calibrations;
- rejected causal links;
- contradiction findings;
- supersession decisions.

A conflict ledger should record why an older relationship, parameterization, or interpretation was replaced.

### 6. Identifiability before calibration

Before fitting a parameter or crediting a feedback mechanism, ask whether the available observations can distinguish the proposed relationship from plausible rivals.

Possible dispositions include:

- `IDENTIFIABLE_WITHIN_TESTED_SCOPE`;
- `WEAKLY_IDENTIFIABLE`;
- `UNIDENTIFIABLE_WITHIN_OBSERVATION_SURFACE`;
- `PREPROCESSING_PRESERVATION_UNKNOWN`;
- `RIVAL_FAMILY_INADEQUATE`.

A low calibration error does not prove the fitted mechanism is identifiable or causal.

### 7. Cheap kill tests before expensive implementation

Every proposed World Zero extension should have the cheapest serious falsification test that could justify rejecting, simplifying, or postponing it.

Examples:

- If regionalization does not improve out-of-sample demographic/resource behavior over a global aggregate, do not assume the extra state is automatically valuable.
- If endogenous learning curves cannot outperform a simple exogenous technology trend on holdout periods, the additional feedback needs stronger justification.
- If a proposed biodiversity-to-productivity coupling is non-identifiable under available data, keep it as a scenario uncertainty rather than a calibrated causal constant.

Complexity must earn its place.

### 8. Claims ledger separate from source ledger

Sources and claims are not interchangeable.

Maintain separate ledgers for:

- source identity and what was actually inspected;
- empirical claims directly supported by sources;
- model interpretations;
- proposed causal mechanisms;
- calibration results;
- scenario conclusions;
- unresolved or untraceable claims.

A source being present does not mean every claim attributed to it is supported.

### 9. Frozen rival models and negative controls

World Zero should compete against simpler and deliberately wrong alternatives.

Before evaluating a new mechanism, freeze the rival set where practical. Useful controls include:

- persistence/no-change baseline;
- exogenous-trend baseline;
- shuffled or lag-destroyed relationship;
- mechanism-disabled ablation;
- parameter-equivalent but causally different rival;
- oracle/upper-bound control when appropriate.

The evaluation framework must be able to fail World Zero and to recognize known-bad controls.

### 10. Historical fit is not enough

Qualification should separate:

- in-sample calibration;
- temporal holdout;
- geographic holdout;
- shock/regime holdout;
- cross-dataset replication;
- structural-ablation tests;
- counterfactual/intervention plausibility;
- numerical convergence.

A visually convincing global trajectory is weak evidence by itself.

### 11. Operation journal for long simulations and calibration jobs

Long or consequential computational jobs should use durable state transitions such as:

`PREPARED -> ATTEMPTED -> VERIFIED | FAILED | AMBIGUOUS`

If a worker or runtime dies after attempting an expensive or stateful operation, recovery inspects the target/result before retrying.

The run receipt should make duplicate execution detectable.

### 12. Chronology is data, not interpretation

Events, interventions, policy adoptions, shocks, wars, technological deployments, demographic transitions, and dataset releases should have explicit timestamps and stable event identifiers.

The chronology layer records when something happened. Other model components decide what it means.

### 13. Structural topology should be inspectable

World Zero’s causal architecture should be representable as an attributed graph/hypergraph-like structure separate from solver code.

Nodes represent stocks, state families, or bounded modules. Edges represent typed pairwise relationships. Higher-order dependencies may be represented explicitly where a relationship genuinely depends on a joint configuration rather than decomposable pairwise effects.

This representation is for inspectability, dependency analysis, ablation generation, and provenance. It must not become decorative graph complexity with no executable meaning.

### 14. Model state should survive solver replacement

Scenario definitions, admitted datasets, parameter records, causal-structure manifests, run receipts, and validation evidence should live outside any one numerical engine.

A future solver replacement must not require reconstructing scientific state from solver-specific code.

### 15. Automate execution; escalate judgment

Automate:

- data integrity checks;
- unit checks;
- calibration sweeps;
- ensemble execution;
- sensitivity analysis;
- regression tests;
- numerical convergence checks;
- reproducibility receipts.

Escalate:

- adding/removing causal links;
- changing claim strength;
- selecting among materially different causal structures;
- changing policy semantics;
- accepting a controversial tipping threshold;
- promoting an inferred relationship into a structural invariant.

Optimization must not silently become architecture authority.

### 16. Preserve negative transfer boundaries

A mechanism that improves one module must not silently contaminate unrelated outputs.

Examples:

- policy assumptions must not leak into historical baseline calibration;
- future scenario priors must not enter holdout validation;
- regional calibration data must not leak into a geographic holdout;
- observed post-event data must not influence a supposedly pre-event forecast;
- a climate-damage prior must not be double-counted through both agriculture and capital channels unless that composition is explicit.

### 17. Model defects close only with regression evidence

A defect is not closed because its explanation is understood.

Closure requires:

1. the failure is reproducible or otherwise evidenced;
2. the responsible mechanism is identified to the justified extent;
3. corrective behavior is implemented;
4. a regression test distinguishes repaired behavior from the prior failure;
5. the exact repaired subject is recorded.

### 18. Preserve superseded hypotheses

Rejected or superseded model structures remain historical evidence. They should be retained with disposition and reason rather than deleted.

This allows later reviewers to distinguish genuine scientific improvement from repeated rediscovery or silent goalpost movement.

## Consequences for the World Zero V0 architecture

These patterns tighten the existing V0 plan in six specific ways:

1. Add an **identifiability preflight** before parameter calibration.
2. Add **dataset admission manifests** rather than direct source-to-model loading.
3. Add a **claim ledger and structural conflict ledger** alongside the source registry.
4. Add **experiment/run journaling** for long calibration and ensemble jobs.
5. Require a **cheap kill test** for every new sector or material feedback mechanism.
6. Store the causal/dependency topology in an inspectable machine-readable form independent of the solver.

These are engineering/scientific-governance constraints, not additional socioeconomic sectors. Their purpose is to make World Zero harder to fool, easier to reproduce, and easier to revise without laundering old assumptions into new truth.
