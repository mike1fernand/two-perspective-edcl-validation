# EDCL H0_obs Likelihood Fix

## Purpose

This document records the technical fix that makes the Tier-A1 Hubble validation test the TP/EDCL mechanism correctly.

The local Hubble anchor must be applied to the observed-frame quantity:

```text
H0_obs = H0_theory * (1 + delta0)
```

not directly to the theory-frame `H0` sampled by the cosmology engine.

## Problem fixed

The standard direct local-H0 likelihood compares the sampled input `H0` directly to the local-Hubble measurement. That is not the EDCL observable.

In TP/EDCL, the calibration drift changes the observed quantity through:

```text
delta0 = alpha_R * f_norm
f_norm = 0.7542
H0_obs = H0 * (1 + delta0)
```

A standard direct local-H0 likelihood can therefore incorrectly penalize a sample whose theory-frame `H0` is lower but whose EDCL observed-frame `H0_obs` is near the local anchor.

## Correct likelihood

For the Riess local anchor used in Tier-A1:

```text
chi2_H0_obs = ((H0 * (1 + alpha_R * 0.7542) - 73.04) / 1.04)^2
logp = -0.5 * chi2_H0_obs
```

The canonical helper function for this formula is:

```text
cosmology/likelihoods/H0_edcl_func.py
```

The Cobaya YAML key for the custom EDCL observed-frame likelihood is:

```text
H0_edcl
```

A portable inline YAML form is:

```yaml
H0_edcl:
  external: "lambda H0, alpha_R: -0.5 * ((H0 * (1.0 + alpha_R * 0.7542) - 73.04) / 1.04) ** 2"
```

The corresponding derived parameters should be present in EDCL+H0_obs runs:

```yaml
H0_obs:
  derived: 'lambda H0, alpha_R: H0 * (1.0 + alpha_R * 0.7542)'

delta0:
  derived: 'lambda alpha_R: alpha_R * 0.7542'
```

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

A stale EDCL YAML that uses direct `H0.riess2020` should now fail before MCMC interpretation.

## Files that implement the fix

Corrected EDCL YAML templates:

```text
cosmology/cobaya/edcl_cosmo_lateonly.yaml.in
cosmology/cobaya/edcl_cosmo_full.yaml.in
```

Formula helper:

```text
cosmology/likelihoods/H0_edcl_func.py
```

Regression test:

```text
tests/test_h0_obs_likelihood.py
```

Guard and validator:

```text
cosmology/scripts/check_no_doublecount_sh0es.py
cosmology/scripts/validate_tiera1_lateonly_results.py
```

Canonical Tier-A1 runner:

```text
cosmology/scripts/run_tiera1_lateonly_suite.py
```

Shell wrapper:

```text
RUN_TIER_A_VALIDATION.sh
```

Colab guide:

```text
docs/COLAB_GUIDE.md
```

## Corrected runner behavior

The canonical Tier-A1 runner now renders YAMLs into:

```text
<workdir>/yamls/
```

not into:

```text
cosmology/cobaya/
```

The runner performs H0-likelihood invariant checks before MCMC and repeats checks after Cobaya install/update handling. It should fail fast if an EDCL+H0_obs configuration uses direct `H0.riess2020`.

Setup-only run:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py \
  --profile iterate \
  --skip-mcmc \
  --no-validate
```

Full iterate run:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile iterate
```

Referee run:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile referee
```

## Regression test

Run:

```bash
python tests/test_h0_obs_likelihood.py
```

The test checks:

```text
H0_obs = H0 * (1 + alpha_R * f_norm)
alpha_R = 0 recovers H0_obs = H0
the standard theory-frame H0 penalty is large for an EDCL-corrected point
the custom observed-frame H0 penalty is small for the same point
f_norm = 0.7542 is applied once, not twice
```

## Current Tier-A1 status

Current paper-chain values:

| Quantity | Value |
|---|---:|
| `alpha_R` | `0.0826 ± 0.0408` |
| `delta0` | `0.0623 ± 0.0308` |
| `H0_obs` | `73.04 ± 0.95` km/s/Mpc |
| Delta chi2 vs LCDM | `-1.0627` |

This validates a working `H0_obs` calibration-drift mechanism in Tier-A1 late-only data. It should not be described as a completed Hubble-tension resolution until exact decomposition/provenance, broader likelihood-sector and fair-baseline robustness scans beyond the archived BAO/SN checkpoint diagnostics, workdir-backed provenance, and Tier-A2/Planck validations are complete.

## Historical note

Older validation notes reported stronger fixed-likelihood improvements or projected CMB-dependent improvements. Keep those clearly labeled as historical tests or projections unless reproduced by the current canonical Tier-A result card and chain/workdir artifacts.

Do not interpret a failed run using direct `H0.riess2020` in an EDCL+H0 configuration as a physics failure of the observed-frame `H0_obs` mechanism. That is a stale-configuration failure.

## Current no-H0 checkpointed diagnostics status (2026-05-04)

Tier-A1 should be described as a **mechanism-level Hubble calibration-channel test**, not as a completed Hubble-tension resolution.

Current claim ladder:

| Diagnostic | Current status | Interpretation |
|---|---|---|
| With-H0 activation | Supported / pass | `alpha_R` activates when the local observed-frame `H0_obs` channel is included. |
| No-H0 best-fit/profile collapse | Supported | No-H0 best fits move to `alpha_R ≈ 0`; fixed-alpha profile diagnostics penalize `alpha_R=0.03` by `Delta chi2 ≈ 4.64` relative to `alpha_R=0`. |
| No-H0 posterior-tail q95 collapse | **Not passed** | Sampled-density no-H0 gives `q95(alpha_R)=0.0470`; fixed-density no-H0 gives `q95(alpha_R)=0.0341`; same-model P1/P2 fixed-density repeat gives `q95(alpha_R)=0.033860544`, still above the configured `0.03` threshold. |
| Full Hubble-tension resolution | Not established | Full Planck/CMB, distance-ladder/`M_B`, growth, fair-baseline, and provenance checks remain future validation targets. |

BAO-only and SN-only no-H0 runs are **diagnostic ablations only**, not validation gates. In the archived checkpoint diagnostics, they place the best fit near `alpha_R=0` while retaining broad positive-amplitude tails (`q95≈0.120856` for BAO-only and `q95≈0.153656` for SN-only). This supports the interpretation that the residual no-H0 q95 failure is a weak-identifiability/posterior-volume issue in the compact late-time test, not a best-fit preference for nonzero EDCL drift.

Do not state that EDCL resolves the Hubble tension or that the no-H0 q95 threshold passes. Use: **activation plus profile-collapse evidence; posterior-tail q95 not passed**.
