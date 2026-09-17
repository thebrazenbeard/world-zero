# World Zero Scientific Spine V2 — Task 6 Boundary Correction

Date: 2026-09-17
Status: current implementation correction

This note supersedes only Task 6 Step 3 of `2026-09-17-world-zero-scientific-control-plane-v2.md`.

The original Step 3 proposed proving that B1 hyperparameter search uses only calibration observation IDs. That proof depends on `PartitionSet`, which is not implemented until Task 7. Implementing a fake partition surface in Task 6 would invert the dependency order and create duplicate leakage logic.

Task 6 therefore enforces the manifest-level policy instead:

- benchmarks cannot carry causal topology fields or causal interpretation;
- B1 declares `calibration_only_selection = true`;
- B1 declares final-holdout access `FORBIDDEN_UNTIL_FINAL_EVALUATION`;
- B1 freezes its feature set before final-holdout evaluation;
- B1 declares its hyperparameter and regularization policies.

Task 7 remains responsible for the executable observation-ID proof: calibration/search IDs must be disjoint from final holdout IDs, including upstream-lineage-aware leakage checks.

This is a sequencing correction, not a weakening of the holdout-isolation requirement.
