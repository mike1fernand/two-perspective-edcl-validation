# Tier-A1 Artifact Manifest

This manifest lists the artifacts needed for a reviewer-verifiable Tier-A1 late-only Hubble validation.

Tier-A1 is a mechanism-activation/collapse validation layer. It should not be presented as a decisive full Hubble-tension resolution without additional provenance, ablations, robustness scans, fair baselines, and Tier-A2/Planck validation.

## Canonical artifact-producing runner

The canonical Tier-A1 runner is:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile iterate
```

The shell wrapper delegates to the same runner:

```bash
bash RUN_TIER_A_VALIDATION.sh
```

For setup-only verification before MCMC:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py \
  --profile iterate \
  --skip-mcmc \
  --no-validate
```

## Corrected Tier-A1 workdir layout

The corrected runner writes artifacts under a timestamped workdir such as:

```text
edcl_tiera1_YYYYMMDD_HHMMSS/
```

Expected workdir contents:

```text
edcl_tiera1_YYYYMMDD_HHMMSS/
  manifest.json
  logs/
  yamls/
  chains/
  results_summary.json
  results_report.md
  bundle_edcl_tiera1.zip
```

The rendered YAMLs should be written under:

```text
<workdir>/yamls/
```

not into `cosmology/cobaya/`.

## Required artifact groups in a complete run bundle

A complete Tier-A1 bundle should include:

```text
manifest.json
logs/
yamls/
chains/
results_summary.json
results_report.md
```

The bundle file itself is expected at:

```text
<workdir>/bundle_edcl_tiera1.zip
```

## Required files or evidence per run

Each complete Tier-A1 run should preserve enough evidence to verify:

```text
CLASS clone/tag/commit
EDCL patch hash
patch validation / dry-run / application logs
CLASS/classy build logs
EDCL smoke-test output
EDCL background preflight output
rendered Cobaya YAMLs
Cobaya updated YAMLs, if produced
Cobaya install/test/run logs
chain files
chain metadata files, if produced
validator results_summary.json
validator results_report.md
manifest.json
checksums or release-asset SHA256 values
```

## Required H0-likelihood configuration evidence

The bundle must make the following H0-likelihood invariants inspectable:

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

The relevant guard and validator logs should be preserved under:

```text
<workdir>/logs/
```

The main scripts enforcing this are:

```text
cosmology/scripts/check_no_doublecount_sh0es.py
cosmology/scripts/validate_tiera1_lateonly_results.py
```

The canonical formula helper is:

```text
cosmology/likelihoods/H0_edcl_func.py
```

## Current chain-audit artifacts

Current compact result artifacts in git:

```text
cosmology/results/tierA1_hubble_result_card.json
cosmology/results/tierA1_chain_component_audit.json
```

The chain audit verifies the Tier-A1 headline posterior values, EDCL formula relations, and best-fit component accounting from available chain columns.

Current chain-verified accounting:

```text
EDCL+H0_obs vs LCDM:
Delta chi2_total     = -1.0627
Delta chi2_H0/H0_obs = -1.0182
Delta chi2_BAO       = -0.3150
Delta chi2_SN        = +0.2705
```

This accounting is chain-derived, not emulator-derived.

## Heavy artifacts should not be committed

Do not commit generated heavy/runtime outputs to normal git history:

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

If chain/workdir artifacts are needed for external reproducibility, publish them as GitHub Release assets and document their checksums.

## Minimal GitHub Release asset recommendation

A clean release should attach a compact reproducibility bundle, for example:

```text
tierA1_reproducibility_assets.zip
```

Suggested contents:

```text
chains/lcdm_production.1.txt
chains/edcl_production.1.txt
chains/edcl_no_h0_medium.1.txt
workdirs/edcl_tiera1_20251221_212236/      # if available
workdirs/edcl_tiera1_20251221_212444/      # if available
workdirs/<corrected-run-workdir>/           # regenerated equivalent if older workdirs are unavailable
checksums/SHA256SUMS.txt
README_RELEASE_ASSETS.md
```

If the old timestamped workdirs are unavailable, publish the available chain files plus a regenerated corrected-run workdir bundle and state that the original workdir-backed provenance remains unavailable.

## Current status

The public GitHub releases page still needs large Tier-A1 chain/workdir assets for full referee-grade provenance.

Available manifest-matching chain files have been used to produce:

```text
cosmology/results/tierA1_chain_component_audit.json
```

Full YAML/config/log/environment provenance remains incomplete until the timestamped workdir artifacts are located locally, regenerated with the corrected runner, or published as Release assets.

## Why this matters

The cleaned manuscript treats the Tier-A1 result as a mechanism-activation/collapse test. The current chain audit supplies best-fit likelihood-component accounting for the available Tier-A1 chains.

Stronger Hubble-resolution language still requires:

```text
workdir-backed provenance
likelihood ablations
kernel/prior/local-anchor robustness scans
fair baselines
Tier-A2/Planck validation
```
