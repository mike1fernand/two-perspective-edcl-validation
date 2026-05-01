# EDCL H0_obs Likelihood Fix

## Purpose

This document records the technical fix that makes the Tier-A Hubble validation test the TP/EDCL mechanism correctly.

The local Hubble anchor must be applied to the observed-frame quantity

```text
H0_obs = H0_theory * (1 + delta0)
```

not directly to the theory-frame `H0` sampled by the cosmology engine.

## Problem fixed

The standard `H0.riess2020` likelihood compares the sampled input `H0` directly to the local-Hubble measurement. That is not the EDCL observable. In TP/EDCL the calibration drift changes the observed quantity through

```text
delta0 = alpha_R * f_norm
f_norm = 0.7542
H0_obs = H0 * (1 + delta0)
```

A standard local-Hubble likelihood can therefore incorrectly penalize a sample whose theory-frame `H0` is lower but whose EDCL observed-frame `H0_obs` is near the local anchor.

## Correct likelihood

For the Riess et al. local anchor used in Tier-A1:

```text
chi2_H0 = ((H0 * (1 + alpha_R * 0.7542) - 73.04) / 1.04)^2
logp = -0.5 * chi2_H0
```

The code implementation may write this equivalently as

```text
delta0 = alpha_R * 12 * kappa_tick * f_norm
```

with `kappa_tick = 1/12`, so that `12 * kappa_tick = 1` and `delta0 = alpha_R * f_norm`.

## Regression test

Add and run:

```bash
python tests/test_h0_obs_likelihood.py
```

The test checks:

1. `H0_obs = H0 * (1 + alpha_R * f_norm)`.
2. `alpha_R = 0` recovers `H0_obs = H0`.
3. The standard theory-frame H0 penalty is large for an EDCL-corrected point.
4. The custom observed-frame H0 penalty is small for the same point.
5. `f_norm = 0.7542` is applied once, not twice.

## Current Tier-A1 status

Current paper values:

| Quantity | Value |
|---|---:|
| `alpha_R` | `0.0826 ± 0.0408` |
| `delta0` | `0.0623 ± 0.0308` |
| `H0_obs` | `73.04 ± 0.95` km/s/Mpc |
| Delta chi2 vs LCDM | `-1.0627` |

This validates a working `H0_obs` calibration-drift mechanism in Tier-A1 late-only data. It should not be described as a decisive full Hubble-tension resolution until exact decomposition, robustness, fair-baseline, and Tier-A2/Planck validations are complete.

## Historical note

Older validation notes reported stronger fixed-likelihood improvements or projected CMB-dependent improvements. Keep those clearly labeled as historical tests or projections unless reproduced by the current canonical Tier-A result card.
