> **License:** Source-visible, **not open source**. Original material is proprietary. Private noncommercial study and evaluation are permitted under [LICENSE](LICENSE); commercial use, redistribution, hosted use, and derivatives require separate written permission. See [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md). Third-party code and data retain their own rights.

# World Zero

**World-systems simulation, evidence management, and falsifiable model comparison in Python.**

World Zero is a reusable research toolkit for testing how population, resources, production, trade, environment, and institutional responses interact over time. It is motivated by the *World3* system-dynamics tradition, but its purpose is to compare competing mechanisms and observations—not to reproduce a predetermined collapse forecast or assume that technological change removes all constraints.

The repository currently provides an executable regional/scenario modeling framework, typed scientific contracts, provenance-aware input controls, a receipt-producing baseline runner, and bounded historical-demography qualification work. **It is not a validated global forecast, a production decision engine, or a complete calibrated World Zero successor to World3.**

## What works today

| Component | Reusable function | Evidence boundary |
| --- | --- | --- |
| [`worldzero.core`](src/worldzero/core/) | Stock/flow interfaces, numerical clocks, solver and invariants | Numerical consistency does not prove physical truth |
| [`worldzero.models`](src/worldzero/models/) | Native regional backbone, integrated V0 scenario, configuration binding and file-backed runner | V0 execution is not a generally calibrated global projection |
| [`worldzero.sectors`](src/worldzero/sectors/) and [`accounting`](src/worldzero/accounting/) | Sector mechanisms and physical-energy/trade reconciliation | Individual mechanisms remain subject to separate admission and ablation tests |
| [`worldzero.science`](src/worldzero/science/) | Typed claims, topology, provenance, model families, comparison protocols, partitions and implementation coverage | A structurally valid record is not an authenticated observation or causal proof |
| [`worldzero.validation`](src/worldzero/validation/) | Error metrics, temporal partitions, holdouts and targeted demographic walk-forward checks | Validation applies only to declared subjects and periods |
| [`tools`](tools/) and [`data`](data/README.md) | Offline/reconstructible scenario runs, admitted dataset manifests and derivation workflows | The included 2026 population inputs are projections, not independently observed validation targets |

Research protocols and schemas accompany the source. They are useful for extending the toolkit, but a documented future model family does not become an implemented or qualified model merely because its YAML or design exists.

## Quick start — reproduce a bounded baseline

Requires Python **3.12 or 3.13**. From a checkout of the repository, create an isolated environment:

```bash
python -m venv .venv
```

Activate `.venv` using your shell's normal activation command, then install the package and run its tests:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

You can also invoke the virtual environment's Python executable directly. Do not run project code against unreviewed or untrusted dataset files.

The built-in 2026 scenario uses checked-in scenario, parameter, region, and data-bundle files. Run it with relative output paths that work on different hosts:

```bash
python -m tools.run_world_zero_baseline --output runs/example/result.json --receipt runs/example/receipt.json
```

The runner writes a model-result JSON file and a provenance/execution receipt. The receipt records the source commit/tree, input and scenario hashes, solver configuration, dependencies, and resulting file hash. In a clean checkout, the baseline's claim class is `RUNNABLE_SOURCE_REPRODUCIBLE_ONLY`: **a successful run shows reproducible source execution, not verified prediction accuracy**. The included 2026 population bundle marks inputs as `PROJECTION` and not validation-eligible observations.

Output paths are writable locations you choose, not hard-coded paths from a developer's computer. Running a model creates local files; it does not operate physical devices or publish results.

The executable entrypoint and defaults are in [`tools/run_world_zero_baseline.py`](tools/run_world_zero_baseline.py); the baseline loader and receipt pipeline are in [`src/worldzero/models/execution.py`](src/worldzero/models/execution.py). Programmatic integration is through the installed `worldzero` Python package rather than a hosted service or authenticated API.

## Scientific method and evidence discipline

World Zero treats these as different questions:

1. **Definition:** Which causal mechanisms and higher-order interactions are declared, and which are actually bound to executable code?
2. **Evidence:** Which series were admitted, with which units, geographies, provenance, revision vintages, and uncertainty?
3. **Comparison:** Which rival families and cheap predictive baselines are being tested under a frozen protocol?
4. **Falsification:** Which holdouts, invariants, sensitivity checks, and ablations could reject a mechanism?
5. **Reproduction:** Can a run be reconstructed from exact code, topology, datasets, parameters, solver settings, and receipt hashes?

Historical fit cannot uniquely identify causation. Scenario trajectories are conditional outputs, not prophecies. Missing or disputed evidence remains `UNKNOWN`, and a claimed improvement must survive the declared metric and holdout rather than winning by adding enough parameters.

### Contracts, comparisons, and data

- [Topology schema](specs/CAUSAL_TOPOLOGY_V2.schema.json), [implementation-coverage schema](specs/IMPLEMENTATION_COVERAGE_V1.schema.json), and [comparison-protocol schema](specs/COMPARISON_PROTOCOL_V1.schema.json) define the research contracts; [schema status](specs/SCHEMA_STATUS.md) distinguishes current and superseded versions.
- [Model family definitions](model_families/) and [predictive benchmarks](benchmarks/) support explicit rivals. The proposed F0 World3-compatible control and broader modern families require separate scientific qualification.
- [Data registry](docs/research/DATA_SOURCE_REGISTRY_V0.md), [admission policy](docs/research/DATA_ADMISSION_POLICY_V1.md), and [validation strategy](docs/research/VALIDATION_AND_FALSIFICATION_STRATEGY.md) distinguish candidate sources, admitted transformations, and legitimate comparison subjects.
- [World3 baseline research](docs/research/LIMITS_TO_GROWTH_AND_WORLD3_BASELINE.md), [rival-model contract](docs/research/RIVAL_MODEL_FAMILIES_V1.md), and [mechanism admission/ablation](docs/research/MECHANISM_ADMISSION_AND_ABLATION_V1.md) explain why each additional mechanism must earn complexity.
- [Qualification records](docs/qualification/) document bounded test subjects and known limitations. An old successful result is not evidence for a later source revision or a different comparison protocol.

The external [`pyworld3` project](https://github.com/cvanwynsberghe/pyworld3) is a possible historical reference/comparison subject and uses CeCILL 2.1. Its license does not become this repository's license, and its implementation is not silently incorporated as a verified World Zero model.

## Trust, security, and operation

- The Python package does **not** authenticate data publishers, prove dataset consent, authorize protected writes, or supply a host-owned authorization service. An embedding application must enforce source admission, file permissions, caller identity, permission scopes, and output publication policies.
- Published observations, derived datasets, model projections, and simulation results must be labeled distinctly. A source hash preserves byte identity, not observation truth or a scientific endorsement.
- Review the checked-in [security policy](SECURITY.md) before opening this repository in an editor. Historical source contained a concealed automatic VS Code startup task and an executable disguised as a font; these were removed from current source, and workspace-startup safety tests cover that current configuration. Removal does not attest the security of old clones or user-level editor settings.
- Candidate branches and pull requests are unmerged research subjects until incorporated; neither a draft PR nor multiple internal model reviews prove exact-head release qualification.
- This is software/research infrastructure. It does not control real-world economic or ecological systems, and its outputs are not authority to act on people, infrastructure, or policy.

## Status and development

**Version:** `0.1.0.dev0` in [`pyproject.toml`](pyproject.toml). **Maturity:** executable research framework with narrowly scoped comparison evidence, not a released forecasting service. See [contribution guidance](CONTRIBUTING.md), [research plans](docs/superpowers/), [model-design specification](docs/superpowers/specs/2026-09-17-world-zero-model-design.md), and [qualification records](docs/qualification/) for development context and current scientific limitations.

Scientific claim promotion, source-code merge, distribution rights, and deployment are separate decisions. Do not infer one from another.
