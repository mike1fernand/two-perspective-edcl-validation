# Tier-A1 Cosmology Validation: Current Status and Next Steps

## Executive summary

This document describes the current Tier-A1 late-only cosmology validation of the TP/EDCL Hubble mechanism.

**Current Tier-A1 achievement:** EDCL validates a working observed-frame Hubble calibration channel. The local-Hubble likelihood is applied to:

```text
H0_obs = H0_theory * (1 + delta0)
delta0 = alpha_R * f_norm
f_norm = 0.7542
```

rather than directly to the theory-frame `H0`.

**Current statistical status:** the Tier-A1 result is a mechanism-activation and collapse test, not yet a decisive full Hubble-tension resolution. The current paper-chain audit reports:

| Quantity | Current Tier-A1 value |
|---|---:|
| `alpha_R` with local `H0_obs` | `0.0826 ± 0.0408` |
| `delta0 = 0.7542 alpha_R` | `0.0623 ± 0.0308` |
| `H0_theory` in EDCL+H0 run | `68.80 ± 1.85` km/s/Mpc |
| `H0_obs` in EDCL+H0 run | `73.04 ± 0.95` km/s/Mpc |
| LCDM best chi2 | `1417.2453` |
| EDCL+H0 best chi2 | `1416.1826` |
| Delta chi2 vs LCDM | `-1.0627` |
| Approx. Delta AIC | `0.94` |
| Approx. Delta BIC, using N≈1715 | `6.38` |

The `N≈1715` BIC count is an approximate diagnostic, not a primary evidence statistic. Exact BIC requires an explicitly defined effective data count.

## What was fixed

### Original issue

The standard direct local-Hubble likelihood compares the sampled theory-frame `H0` directly to the local measurement. That does not test the EDCL mechanism, because EDCL modifies the observed quantity:

```text
H0_obs = H0_theory * (1 + delta0)
```

### Corrected likelihood

The EDCL-aware likelihood compares `H0_obs`, not `H0_theory`, to the local anchor:

```text
chi2_H0_obs = ((H0 * (1 + alpha_R * 0.7542) - 73.04) / 1.04)^2
logp = -0.5 * chi2_H0_obs
```

The canonical helper function is:

```text
cosmology/likelihoods/H0_edcl_func.py
```

The Cobaya key for the corrected EDCL observed-frame local-H0 likelihood is:

```text
H0_edcl
```

This technical correction is central and should be preserved.

## H0-likelihood invariants

The corrected Tier-A1 path enforces these rules:

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

The main guard and validator are:

```text
cosmology/scripts/check_no_doublecount_sh0es.py
cosmology/scripts/validate_tiera1_lateonly_results.py
```

A stale EDCL+H0 configuration using direct `H0.riess2020` should fail as a configuration error before the result is interpreted as an `alpha_R` activation/collapse result.

## What is validated in Tier-A1

| Test | Status | Interpretation |
|---|---|---|
| Custom likelihood applies local H0 to `H0_obs` | validated by code review, `tests/test_h0_obs_likelihood.py`, YAML invariant checks, and validator checks | Required for a meaningful EDCL Hubble test |
| Activation with local H0 included | present in current chain audit | `alpha_R` is about `2.0σ` by mean/std |
| Collapse without local H0 | present in current chain audit | no-H0 run gives `alpha_R = 0.0147 ± 0.0142` |
| Observed-frame H0 match | present in current chain audit | `H0_obs = 73.04 ± 0.95` km/s/Mpc |
| Late-only fit improvement | modest | `Delta chi2 = -1.0627` with one added parameter |
| Best-fit component accounting | chain-verified for the available Tier-A1 chains | EDCL+H0_obs vs LCDM gives `Delta chi2 = -1.0627`, with H0/H0_obs = `-1.0182`, BAO = `-0.3150`, and SN = `+0.2705`; see `cosmology/results/tierA1_chain_component_audit.json` |

## What is not yet validated

The following are resolution targets, not completed Tier-A1 claims:

```text
full workdir-backed provenance for the original component accounting
likelihood ablations showing activation is specifically driven by local H0_obs
kernel, prior, and local-anchor robustness scans
fair baselines against wCDM, w0waCDM, and generic calibration offsets
full Tier-A2 Planck likelihood validation
Bayesian evidence with documented nested-sampler provenance
```

Best-fit component accounting from the available chain columns is recorded in:

```text
cosmology/results/tierA1_chain_component_audit.json
```

## Claim ladder

Use `docs/HUBBLE_RESOLUTION_CLAIM_LADDER.md` as the canonical wording guide.

Current allowed wording:

> Tier-A1 validates a working `H0_obs` calibration-drift mechanism and activation/collapse behavior in late-only data.

Do not use as a completed Tier-A1 claim:

> EDCL decisively resolves the Hubble tension.

That stronger wording requires the later claim-ladder steps.

## How to reproduce

Use a Linux/Colab/WSL-style environment for Tier-A1 because CLASS/classy and Cobaya likelihood data are required.

### Canonical setup-only command

Run this first:

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

### Full iterate run

After setup-only succeeds:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile iterate
```

### Referee run

After the iterate run is clean and interpretable:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile referee
```

### Shell wrapper

The root shell wrapper delegates to the same canonical Python runner:

```bash
bash RUN_TIER_A_VALIDATION.sh
```

To use an existing EDCL-patched CLASS build:

```bash
bash RUN_TIER_A_VALIDATION.sh /path/to/class_public
```

### Existing chain-file analysis

For standalone chain-file analysis, use:

```bash
python3 cosmology/scripts/analyze_chains.py \
  --chains-dir <chains_dir> \
  --output tierA1_chain_verification.json \
  --plot
```

### Existing workdir validation

For workdir-level validation, use:

```bash
python3 cosmology/scripts/validate_tiera1_lateonly_results.py \
  --workdir <workdir> \
  --profile iterate
```

or:

```bash
python3 cosmology/scripts/validate_tiera1_lateonly_results.py \
  --workdir <workdir> \
  --profile referee
```

## Required artifacts

See `docs/TIER_A_ARTIFACT_MANIFEST.md`.

A corrected Tier-A1 workdir should contain:

```text
<workdir>/manifest.json
<workdir>/logs/
<workdir>/yamls/
<workdir>/chains/
<workdir>/results_summary.json
<workdir>/results_report.md
<workdir>/bundle_edcl_tiera1.zip
```

At minimum, a reviewer-facing Tier-A1 release should include:

```text
LCDM late-only chains/workdir/logs
EDCL+H0_obs chains/workdir/logs
EDCL no-H0 chains/workdir/logs
rendered YAML/config files
Cobaya updated YAMLs, if produced
environment manifest
checksums
cosmology/results/tierA1_hubble_result_card.json
cosmology/results/tierA1_chain_component_audit.json
```

The chain audit provides chain-verified posterior values, best-fit component accounting, formula checks, and BBN consistency contrast.

Generated heavy/runtime outputs should not be committed to normal git history:

```text
class_public/
cobaya_packages/
chains/
edcl_tiera1_*/
bundle_edcl_tiera1.zip
*.updated.yaml
```

Publish heavy chain/workdir artifacts as GitHub Release assets if needed for external reproducibility.

## Next validation priorities

1. Regenerate or locate Tier-A workdir artifacts for YAML/config/log/environment provenance.
2. Preserve `cosmology/results/tierA1_chain_component_audit.json` as the current chain-verified best-fit component accounting.
3. Maintain the lightweight `H0_obs` likelihood regression test in `tests/test_h0_obs_likelihood.py`.
4. Keep the corrected H0-likelihood guard and workdir validator active.
5. Run likelihood ablations.
6. Run kernel/prior/local-anchor robustness scans.
7. Run Planck distance-prior preflight and then full Tier-A2.
8. Add BBN/integrated-distance paper enhancements only after the relevant chain outputs are verified.
