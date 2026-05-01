# Hubble Resolution Claim Ladder

This document preserves the strong Hubble-resolution objective while separating completed evidence from future validation targets.

## Current canonical Tier-A1 result

| Quantity | Current value |
|---|---:|
| `alpha_R` | `0.0826 ± 0.0408` |
| `delta0 = 0.7542 alpha_R` | `0.0623 ± 0.0308` |
| `H0_theory` in EDCL+H0 run | `68.80 ± 1.85` km/s/Mpc |
| `H0_obs` in EDCL+H0 run | `73.04 ± 0.95` km/s/Mpc |
| Delta chi2 vs LCDM | `-1.0627` |
| Approx. Delta AIC | `0.94` |

## Claim levels

| Claim level | Evidence required | Current status | Allowed language |
|---|---|---|---|
| 1. Mechanism activation | Custom `H0_obs` likelihood; nonzero `alpha_R`; no-H0 collapse; high-z safety | Current Tier-A1 target | “Tier-A1 validates a working `H0_obs` calibration-drift mechanism.” |
| 2. Robust late-time channel | Exact per-likelihood chi2 decomposition; likelihood ablations; kernel/prior/local-anchor robustness | To run | “Robust late-time Hubble-resolution channel.” |
| 3. Planck-compatible resolution | Planck distance-prior preflight and full Tier-A2 Planck likelihood with no-H0 controls | To run | “Substantially resolves the Hubble tension in the tested Planck+late data combination.” |
| 4. Strong model-comparison resolution | Fair baselines (`wCDM`, `w0waCDM`, generic calibration offset) plus AIC/BIC/evidence with documented priors | To run | “Favored over specified alternatives under documented priors and datasets.” |

## Disallowed current wording

Do not currently use unqualified statements like:

- “EDCL decisively resolves the Hubble tension.”
- “EDCL is favored by decisive evidence.”
- “alpha_R is 3.9 sigma from zero.”
- “Full CMB validation is complete.”

## Strong objective to preserve

The research objective remains to earn the stronger claim. The validation path is:

```text
custom H0_obs likelihood
→ exact chi2 decomposition
→ ablations
→ kernel/prior/local-anchor robustness
→ fair baselines
→ Tier-A2 Planck validation
→ stronger Hubble-resolution wording if results support it
```
