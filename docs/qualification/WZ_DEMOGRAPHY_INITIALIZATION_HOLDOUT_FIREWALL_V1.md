# World Zero Initialization / Holdout Firewall V1

Status: **SOURCE CANDIDATE / PRE-FIT FIREWALL / NO HOLDOUT RESULT CLAIM**

Date: 2026-09-19

## Exact integration basis

This subject is built from canonical World Zero main after the runtime path landed:

- main: `704e856fc9e215f6da31823acb645575cfc61374`
- PR #18 baseline bindings: merged
- PR #19 canonical V0 runner/runtime receipt: merged
- PR #24 evidence firewall: imported as source evidence, not treated as merged history

The imported 2023 evidence packet retains its governed catalog and frozen
10-total CALIBRATION / 40-cohort VARIABLE_HOLDOUT partition.

## S1 leakage rule

A holdout selector must receive the exact governed observation IDs consumed while
constructing the initial state. Selection fails closed when any selected holdout
observation ID is also present in `initialization_observation_ids`.

The initialization-ID subject is runtime-typed as an exact tuple of unique,
non-empty built-in strings. An empty tuple means no governed observation IDs were
consumed for initialization; it must not mean unknown provenance.

## Scientific consequence

This closes the mechanical selector bypass that previously allowed a caller to
label evidence as holdout while also declaring that exact evidence as an
initialization input.

It does **not** make the 2023 cohort holdout usable by itself. A run initialized
from the same 2023 cohort observations must be rejected. A real VARIABLE_HOLDOUT
experiment still needs an independently governed, disjoint initialization subject
(for example a pre-2023 initialization cut), or must reclassify consumed evidence
and freeze a new partition before execution.

The canonical 2026 runtime remains a provisional runnable source subject using
2026 WPP projection inputs. That fact does not establish a 2023 holdout result.

## Claim ceiling

This subject may establish only governed evidence loading, validation eligibility,
exact holdout identity binding, explicit initialization-evidence declaration, and
mechanical initialization/holdout overlap rejection.

It does not establish HISTORICAL_CALIBRATION_PASS, VARIABLE_HOLDOUT_PASS,
predictive validity, forecast skill, calibrated parameter quality, scientific
validation, canonical promotion, merge, or deployment/runtime effect.
