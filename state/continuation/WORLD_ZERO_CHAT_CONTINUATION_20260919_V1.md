# WORLD ZERO CHAT CONTINUATION — 2026-09-19 V1

Status: DURABLE CONTINUATION CHECKPOINT
Repository: `thebrazenbeard/world-zero`
Purpose: restore the exact World Zero parallel-execution frontier after chat rollover.

## 0. Authority and execution posture

Patrick authorized continued ordinary World Zero repository work and conditional merging under the already-established gate:

- exact current-head independent/hostile review PASS;
- exact current-head CI green;
- head/base unchanged from the reviewed subject;
- merge using expected-head protection;
- dependent stacked PRs must then be retargeted/reconciled/requalified;
- never treat CI alone as merge authority.

No merge occurred during the saved chat segment.

Keep source/build/install/runtime/scientific-effect claims distinct.
Do not promote runnable/reproducible into calibrated, validated, predictive, forecast-valid, or scientifically accepted.

Chat Communication Bus writes remain withheld while the R10-bound topology is in conflict with later topology state. Bound R10 topology anchor remains:
- commit `712992d96dc813d0fa38094ef1f1fec0dfdc0d3e`
- file `architecture/contracts/RADAR_TOPOLOGY_V1.json`
- blob `8b7cb3deff0ee7f15151f5be0ede19c8c1194adc`
- route `bus/vera-v2`

Do not silently accept topology drift.

## 1. Canonical main

`main` exact head:
`c36b86421d95b93a93aacceebb96bef42090a69a`

No main mutation occurred in the saved segment.

## 2. Scientific/evidence posture

Preserve these semantics exactly:

- WPP 2024 estimate years through 2023: `OFFICIAL_ESTIMATE`.
- WPP 2024 year 2024 onward: `PROJECTION`.
- 2026 baseline population subjects are projection evidence and `validation_eligible=false`.
- 2023 admitted population subjects are official-estimate-derived and `validation_eligible=true`.
- `validation_eligible=true` means eligible for governed partition assignment only; it is not a calibration/holdout PASS.
- `WZ_MACROREGION_V0` remains the frozen 10-region set.
- `WZ_AGE_COHORT_V0` remains the frozen modeling convention:
  - child 0–14
  - young adult 15–39
  - mature adult 40–64
  - older adult 65+
- The age cohorts are modeling conventions, not empirically privileged taxonomy.

Raw WPP age5 source subject:
- dataset id: `un-wpp-2024-population-age5-sex-medium-v1`
- expected bytes: `29948947`
- SHA-256: `a04d7d1486a5eb2832cc812d599448f0a71e8ac9e1e7e6fa4066673d6a2487cd`
- admitted manifest: `data/manifests/UN_WPP_2024_POPULATION_AGE5_SEX_MEDIUM_V1.yaml`
- exact immutable public mirror used for independent byte verification:
  `kenshin-morioka/ds@bc13919b97eed8a9abe6c20a1263a84546d0c15b`
- mirror path:
  `datasets/raw/wpp_population_age_sex/WPP2024_PopulationByAge5GroupSex_Medium.csv.gz`
- Git blob:
  `b8123f47e248690dab8ddc45d413cf821b321fdc`
- mirror bytes were independently streamed and accepted only after exact length + SHA-256 matched the already admitted subject.
- raw gzip remains outside World Zero Git.

2026 cohort artifact:
- dataset: `wz-wpp2024-macroregion-cohort-population-2026-v1`
- artifact SHA-256: `a9ed5b83ca86700f42893e3929929afcded2bf4574b1e9b74807fc736a69a236`
- global population: `8,300,678,587`
- source class: `PROJECTION`
- validation eligible: false.

2023 cohort artifact:
- dataset: `wz-wpp2024-macroregion-cohort-population-2023-v1`
- artifact path: `data/derived/wpp2024/WZ_MACROREGION_V0_cohort_population_2023.csv`
- SHA-256: `e42aee90f156e51471c2c1704492b412626dc647fb5e6b4bde6b8b43d9a486d4`
- bytes: `3074`
- global population: `8,091,735,125`
- reconciliation vs admitted 2023 regional total cut: +194 persons globally;
- maximum absolute regional difference: 61 persons;
- source class: `OFFICIAL_ESTIMATE`;
- validation eligible: true.

2023 regional-total artifact:
- dataset: `wz-wpp2024-macroregion-population-2023-v1`
- output SHA-256: `e12423a8c8edb5f68548605bb837d7689c18caa10b122261e4f96f2aeb7a8578`
- source class: `OFFICIAL_ESTIMATE`
- validation eligible: true.

## 3. Active PR stack and exact heads

### PR #16 — Bind cohort-derived artifacts to frozen semantics

Branch:
`data/v0-wpp-cohort-derived-v1`

Exact head:
`fa3ecfc63009a2a16af0bff4b4142c73014fecaf`

Base:
`main` @ `c36b86421d95b93a93aacceebb96bef42090a69a`

State:
- OPEN / DRAFT / mergeable
- reviews: NONE
- test workflow `35409612612`: SUCCESS
- offline workflow `35409612621`: SUCCESS

Merge gate:
WAITING for exact-head hostile PASS.

Important source hardening already present:
- admitted age5 manifest exact length/SHA verification;
- exact age-group completeness: 237 ISO3 × 21 age groups;
- duplicate/missing age protection;
- stable WPP ParentID per country;
- governed ParentID mapping compatibility;
- deterministic cohort serialization/reconciliation.

### PR #18 — Bind provisional 2026 baseline runtime configuration

Branch:
`runtime/v0-baseline-bindings-v1`

Exact head:
`7ece1e1fa9f0a6a89df57f6785cb9cc84fe5e89a`

Base:
`data/v0-wpp-cohort-derived-v1` @ `fa3ecfc63009a2a16af0bff4b4142c73014fecaf`

State:
- OPEN / DRAFT / mergeable
- reviews: NONE
- test workflow `35409923187`: SUCCESS
- offline workflow `35409923092`: SUCCESS

Merge gate:
WAITING for #16 dependency resolution and then exact-subject hostile PASS after any retarget/reconciliation.

Canonical 2026 baseline:
- bundle READY under provisional bindings;
- exact population total + cohort inputs admitted;
- parameters remain `PROVISIONAL_EXECUTION` / `MODELING_ASSUMPTION`;
- all 2026 population evidence remains `PROJECTION`, validation-ineligible.

### PR #19 — Add canonical V0 runner and runtime receipt

Branch:
`runtime/v0-baseline-runner-v1`

Exact head:
`cef7cc342150d25a16f27b55e0055e2ab97d5cd2`

Base:
`runtime/v0-baseline-bindings-v1` @ `7ece1e1fa9f0a6a89df57f6785cb9cc84fe5e89a`

State:
- OPEN / DRAFT / mergeable
- only recorded review is OLD COMMENTED review on ancient head `512ec6c216b4c2d6a8126b9a968112f4c8f886f7`; obsolete
- fresh exact-head rereview request comment: `5743232911`
- test workflow `35452937561`: SUCCESS
- offline workflow `35452937576`: SUCCESS (Linux + Windows)

Current receipt claim ceiling:
`RUNNABLE_SOURCE_REPRODUCIBLE_ONLY`

Do not overread this as calibration, validation, prediction, forecast quality, or scientific acceptance.

Current protections:
- source commit/tree resolved from actual clean checkout;
- caller expected commit/tree only reject mismatch;
- exact scenario/bundle/parameter/region/cohort bindings;
- transitive dataset manifest/output SHA/length/lineage bindings;
- immutable snapshots before model construction;
- live originals re-resolved after run;
- ABA mutation protection;
- input/output path, symlink and hardlink alias protection;
- in-checkout outputs restricted to Git-ignored `runs/`;
- same-directory atomic result/receipt publication;
- external runtime dependency versions recorded for PyYAML + pydantic;
- Python implementation/version, OS and machine architecture recorded;
- World Zero code identity bound through exact Git commit/tree.

Merge gate:
WAITING for exact current-head hostile PASS and upstream stack.

### PR #20 — Fetch exact bytes bound by admitted dataset manifests

Branch:
`data/v0-admitted-source-fetch-v1`

Exact head:
`f4708ccac3f597753ddd47ec9dea2976ae630bdd`

Base:
`main` @ `c36b86421d95b93a93aacceebb96bef42090a69a`

State:
- OPEN / DRAFT / mergeable
- reviews: NONE
- fresh exact-head rereview request comment: `5743313923`
- test workflow `35453120554`: SUCCESS
- offline workflow `35453120537`: SUCCESS (Linux + Windows)

Current protections:
- source manifest must be ADMITTED and exact-length-bound;
- absolute HTTPS candidate;
- all redirect hops HTTPS-only;
- URL credentials rejected;
- finite positive timeout;
- exact streamed length + SHA-256 govern acceptance;
- same-directory candidate + fsync;
- default refuses pre-existing destination;
- no-replace publication is filesystem-race-safe;
- competing destination creation during transfer fails closed;
- explicit replacement requires `replace_existing=True` / `--replace-existing`;
- manifest path/hardlink alias rejection;
- requested/resolved URLs retained separately;
- failed verification preserves existing destination and removes candidate.

This helper never admits data by retrieval alone.

Merge gate:
WAITING for exact-head hostile PASS.
Because #20 is based directly on main, avoid moving main under an exact #16 review unless the resulting review/base consequences are intentionally reconciled.

### PR #21 — Admit 2023 macroregion cohort historical evidence

Branch:
`data/v0-wpp-cohort-history-v1`

Exact head:
`4f6f8a8ea4e26c5174e2172e85a37866700cb2c5`

Base:
PR #16 branch @ `fa3ecfc63009a2a16af0bff4b4142c73014fecaf`

State:
- OPEN / DRAFT / mergeable
- test workflow `35452404477`: SUCCESS
- offline workflow `35452404479`: SUCCESS
- exact-head review is COMMENTED / scientific-provenance ACCEPT for dataset admission scope only
- review explicitly says validation-use scope was not yet mechanically assigned
- review is NOT the hostile PASS required by the standing merge gate
- follow-up comment linking the validation-use repair work: `5743314560`

Merge gate:
WAITING for #16 dependency + required exact-head merge review after any base change.

### PR #22 — Bind World Zero holdouts to validation-eligible observations

Branch:
`one/wz-holdout-eligibility-binding-v1-20260919`

Exact head:
`ed02f1c0c7f978611c73a7a4aa496f5f5bba6a7d`

Base:
PR #21 branch @ `4f6f8a8ea4e26c5174e2172e85a37866700cb2c5`

State:
- OPEN / DRAFT / mergeable
- test workflow `35452884368`: SUCCESS
- offline workflow `35452884354`: SUCCESS
- COMMENTED BT2 exact merge-subject qualification says SOURCE / BUILD / TEST = PASS for GitHub synthetic merge subject `9e8543ad4f6bd907b66a10930ccb08f69d420358`
- this is not automatically equivalent to the standing exact-head hostile PASS merge gate

Scope:
- generic `select_holdout()` now requires governed `ObservationSeries` bindings;
- missing binding fails closed;
- `validation_eligible=false` fails closed;
- calibration partitions still forbidden as holdouts.

Important:
PR #22 overlaps with but is not identical to PR #23. Treat them as parallel implementations to reconcile, not as mutually superseding by assumption.

### PR #23 — Freeze 2023 demography calibration/variable-holdout partition

Branch:
`science/v0-demography-2023-partition-v1`

Exact head:
`6d0b02e1d87b816dab8ffd3b7b66e74798bae018`

Base:
PR #21 branch @ `4f6f8a8ea4e26c5174e2172e85a37866700cb2c5`

State:
- OPEN / DRAFT / mergeable
- reviews: NONE at checkpoint
- fresh exact-head hostile/scientific review request comment: `5743314366`
- test workflow `35453168654`: SUCCESS
- offline workflow `35453168599`: SUCCESS (Linux + Windows)

Science firewall:
- catalog: `science/evidence/WZ_DEMOGRAPHY_2023_EVIDENCE_V1.yaml`
- partition: `science/partitions/WZ_DEMOGRAPHY_2023_VARIABLE_HOLDOUT_V1.yaml`
- 50 exact 2023 governed observations;
- 10 regional total-population IDs assigned to CALIBRATION;
- 40 regional cohort-composition IDs assigned to VARIABLE_HOLDOUT;
- exact manifest/output SHA bindings;
- every observation re-resolved to exactly one governed CSV row;
- catalog/partition cross-binding fails closed on unknown assigned IDs;
- fails closed on governed-but-unassigned IDs;
- holdouts must remain validation-eligible;
- zero calibration/holdout overlap retained;
- all 50 observations assigned conservatively to one covariance family:
  `UN_WPP_2024_POPULATION_FAMILY`
  so they cannot be presented as 50 independent confirmations.

Important:
This is only a pre-fit evidence firewall. It does NOT establish:
- `HISTORICAL_CALIBRATION_PASS`
- `VARIABLE_HOLDOUT_PASS`
- temporal holdout performance
- predictive validity
- forecast skill
- scientific validation.

## 4. PR #22 vs #23 reconciliation frontier

This is the highest-value integration issue created by parallel work.

PR #22 and PR #23 share the same #21 base but cover different layers:

- #22 hardens the generic holdout selector by requiring typed governed `ObservationSeries` and checking validation eligibility at selection time.
- #23 creates an exact-digest population evidence catalog, freezes the 10-total/40-cohort partition, and mechanically cross-binds partition membership to governed exact population evidence before any calibration.

Likely relationship: complementary, not redundant.

Do NOT merge either merely because both are green.
Next chat should compare their exact diffs/contracts and decide an integration order or combined subject. Any stacking/rebase/retarget creates a new review subject and requires fresh qualification/review.

## 5. Other open repository state

PR #17:
- title: Freeze cohort artifact serialization and reconciliation
- branch: `data/v0-wpp-cohort-serialization-v1`
- head: `1acfc607fe71ea2abd74b43228a19846c6713683`
- base: main
- OPEN / DRAFT
- not an active parallel lane in this checkpoint; fresh-check overlap/supersession before any use.

PR #5:
- Dependabot pytest update;
- not part of the current scientific/runtime frontier.

## 6. Merge-order discipline

No PR in the active stack has been merged.

Do not infer merge permission from green CI or COMMENTED review text.

Primary dependency order remains:
1. #16
2. #18 after #16 is merged/retargeted/requalified
3. #19 after #18
4. #21 after #16 and any resulting retarget/requalification
5. reconcile #22/#23 after #21 and establish one exact integration subject/order
6. #20 is independent but moving main can invalidate/reframe pending base/review subjects; coordinate deliberately.

Every head/base movement invalidates prior exact-subject review evidence unless the review explicitly binds the new subject.

## 7. Immediate next executable work

On restore:

1. Fresh-check main, all active branch heads, PR #16/#18/#19/#20/#21/#22/#23 states, reviews and exact-head workflows.
2. If any exact-head hostile PASS satisfying the standing merge gate has arrived, verify unchanged subject + green CI and execute the dependency-safe merge/retarget/requalification sequence with expected-head protection.
3. Otherwise compare PR #22 vs #23 semantically and structurally; identify complementary vs conflicting changes and build a single reviewable integration path without erasing either provenance.
4. Continue hostile review of #19 and #20 only for substantive integrity defects; avoid churn.
5. After #22/#23 integration is frozen, advance the first actual calibration experiment only under the frozen evidence firewall:
   - calibration may consume only the 10 regional total-population observations;
   - the 40 cohort-composition observations remain unopened VARIABLE_HOLDOUT evidence;
   - no holdout result may be used to tune the calibration subject and still be called holdout.
6. Preserve covariance accounting: all current 2023 population observations share a conservative WPP family and are not independent confirmations.
7. No Bus writes until the R10 topology conflict is actually resolved.

## 8. Restore semantics

This checkpoint is a starting snapshot, not current truth.
Fresh-check mutable state before writes.
Do not carry PASS/FAIL/review status across head movement.
Do not claim hidden/background work.
Do not merge/deploy/change protected state outside the exact authority already established.

Restore phrase:
`WORLD_ZERO::RESTORE::WORLD_ZERO_CHAT_CONTINUATION_20260919_V1`

Run phrase after restore:
`WORLD_ZERO::PARALLEL_EXECUTE::FULL_FRONTIER`
