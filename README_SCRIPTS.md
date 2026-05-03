# EDCL Tier-A1 Validation Script Index

This file summarizes the main scripts for running and analyzing the Tier-A1 late-only EDCL cosmology validation.

The repo now uses one canonical Tier-A1 execution path:

```text
cosmology/scripts/run_tiera1_lateonly_suite.py
```

Legacy entry points are kept only as compatibility wrappers. They should delegate to the canonical runner instead of maintaining separate YAML-generation or MCMC logic.

## Quick start

### 1. Setup-only check before MCMC

Use a Linux/Colab/WSL-style environment:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py \
  --profile iterate \
  --skip-mcmc \
  --no-validate
```

This verifies:

```text
CLASS clone/tag selection
EDCL patch application
CLASS/classy build
EDCL smoke/preflight checks
YAML rendering into <workdir>/yamls/
H0-likelihood invariant checks
Cobaya install/test initialization
manifest and bundle creation
```

### 2. Full iterate run

After setup-only succeeds:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile iterate
```

### 3. Referee run

After the iterate run is clean and interpretable:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile referee
```

## Compatibility wrappers

These wrappers are allowed, but they should not contain separate MCMC/YAML workflows:

```bash
bash RUN_TIER_A_VALIDATION.sh
bash scripts/RUN_TIER_A_VALIDATION.sh
python COLAB_TIER_A_VALIDATION.py --full-run
python colab/COLAB_TIER_A_VALIDATION.py --full-run
```

To use an existing EDCL-patched CLASS build:

```bash
bash RUN_TIER_A_VALIDATION.sh /path/to/class_public
```

or:

```bash
bash scripts/RUN_TIER_A_VALIDATION.sh /path/to/class_public
```

Useful wrapper environment variables:

```text
PROFILE=iterate|smoke|referee
WORK_DIR=/path/to/workdir
OUTPUT_DIR=/path/to/workdir   # legacy alias if WORK_DIR is unset
CLASS_PATH=/path/to/class_public
SKIP_APT=1
SKIP_PIP=1
SKIP_COBAYA_INSTALL=1
SKIP_MCMC=1
NO_VALIDATE=1
MCMC_MAX_SAMPLES=N
```

`COBAYA_PACKAGES_PATH` is no longer required by the corrected wrappers. The canonical Python runner uses a workdir-local Cobaya packages directory.

## Analyze existing chain files

For standalone chain-file analysis:

```bash
python3 cosmology/scripts/analyze_chains.py \
  --chains-dir ./chains \
  --output tierA1_chain_verification.json \
  --plot
```

This analyzes chain files only. It does not validate rendered YAMLs, logs, workdir structure, or H0-likelihood invariants. The standalone analyzer uses the configured no-H0 collapse threshold `q95(alpha_R) <= 0.03`; if the no-H0 q95 exceeds that value, report the result as a collapse tendency rather than a configured-threshold collapse pass.

For full workdir validation, use:

```bash
python3 cosmology/scripts/validate_tiera1_lateonly_results.py \
  --workdir <WORKDIR> \
  --profile iterate
```

## Key files

| File | Role |
|---|---|
| `cosmology/scripts/run_tiera1_lateonly_suite.py` | Canonical Tier-A1 setup/run/validate/bundle entry point |
| `RUN_TIER_A_VALIDATION.sh` | Root shell compatibility wrapper |
| `scripts/RUN_TIER_A_VALIDATION.sh` | Legacy shell compatibility wrapper from `scripts/` |
| `COLAB_TIER_A_VALIDATION.py` | Root Colab compatibility wrapper |
| `colab/COLAB_TIER_A_VALIDATION.py` | Legacy Colab compatibility wrapper from `colab/` |
| `cosmology/scripts/render_yamls.py` | Template renderer; supports workdir YAML output |
| `cosmology/scripts/check_no_doublecount_sh0es.py` | Local-H0 / SH0ES guard |
| `cosmology/scripts/validate_tiera1_lateonly_results.py` | Workdir-level validator |
| `cosmology/scripts/analyze_chains.py` | Standalone chain-file analyzer |
| `cosmology/likelihoods/H0_edcl_func.py` | Canonical observed-frame `H0_edcl` helper |
| `tests/test_h0_obs_likelihood.py` | Regression test for the `H0_obs` likelihood convention |

## H0-likelihood convention

Correct EDCL+local-H0 runs must use the observed-frame local-Hubble likelihood:

```text
H0_obs = H0 * (1 + alpha_R * 0.7542)
```

The configuration rules are:

```text
LCDM + local H0:
  direct H0.riess2020 is allowed.

EDCL + local H0:
  H0_edcl is required.
  direct H0.riess2020 is forbidden.
  derived H0_obs is required.
  derived delta0 is required.

EDCL no-H0:
  H0_edcl is forbidden.
  direct H0.riess2020 is forbidden.
```

A stale EDCL+H0 run that uses direct `H0.riess2020` is a configuration failure, not a physics test of the observed-frame mechanism.

## Expected corrected workdir outputs

The canonical runner writes a timestamped workdir such as:

```text
edcl_tiera1_YYYYMMDD_HHMMSS/
```

Expected contents:

```text
manifest.json
logs/
yamls/
chains/
results_summary.json
results_report.md
bundle_edcl_tiera1.zip
```

Rendered YAMLs should be under:

```text
<workdir>/yamls/
```

not written into `cosmology/cobaya/`.

## Validation tests

The workdir validator and chain analyzer cover:

| Test | Purpose |
|---|---|
| Activation | `alpha_R` activates under the local `H0_obs` likelihood |
| Collapse tendency | The no-local-H0 control shifts `alpha_R` toward zero; configured collapse pass requires `q95(alpha_R) <= 0.03` |
| H0_obs match | observed-frame `H0_obs` is consistent with the local anchor |
| Chi-square accounting | best-fit chi-square and component diagnostics are reported |

Current claim boundary:

```text
Tier-A1 supports a working H0_obs calibration-drift mechanism in late-only data: alpha_R activates when the local observed-frame H0_obs likelihood is included, and the no-H0 control shifts alpha_R toward zero. The current compact no-H0 summary has q95(alpha_R)=0.0497, which exceeds the configured q95<=0.03 collapse pass threshold, so the no-H0 result supports a collapse tendency rather than a configured-threshold collapse pass.
```

Do not use Tier-A1 alone as a decisive full Hubble-tension resolution claim.

## Heavy outputs

Do not commit generated heavy/runtime outputs:

```text
class_public/
cobaya_packages/
chains/
edcl_tiera1_*/
bundle_edcl_tiera1.zip
*.updated.yaml
__pycache__/
*.pyc
```

Publish heavy chain/workdir artifacts as GitHub Release assets if needed for external reproducibility.

## Related docs

```text
README.md
docs/COLAB_GUIDE.md
docs/HOW_TO_REPRODUCE_TIER_A1_OUTPUTS.md
docs/TIER_A_ARTIFACT_MANIFEST.md
docs/VALIDATION_MATRIX.md
cosmology/docs/H0_LIKELIHOOD_FIX.md
```
