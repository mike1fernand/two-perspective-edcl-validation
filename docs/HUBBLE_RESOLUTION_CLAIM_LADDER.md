# Hubble Resolution Claim Ladder

This document preserves the strong Hubble-resolution objective while separating completed evidence from future validation targets.

The current Tier-A1 result is a mechanism-activation/collapse result. It is not, by itself, a decisive full Hubble-tension resolution.

## Current canonical Tier-A1 result

| Quantity | Current value |
|---|---:|
| `alpha_R` | `0.0826 ± 0.0408` |
| `delta0 = 0.7542 alpha_R` | `0.0623 ± 0.0308` |
| `H0_theory` in EDCL+H0_obs run | `68.80 ± 1.85` km/s/Mpc |
| `H0_obs` in EDCL+H0_obs run | `73.04 ± 0.95` km/s/Mpc |
| Delta chi2 vs LCDM | `-1.0627` |
| Approx. Delta AIC | `0.94` |

The current chain-verified component accounting is recorded in:

```text
cosmology/results/tierA1_chain_component_audit.json
```

Current best-fit accounting:

```text
EDCL+H0_obs vs LCDM:
Delta chi2_total     = -1.0627
Delta chi2_H0/H0_obs = -1.0182
Delta chi2_BAO       = -0.3150
Delta chi2_SN        = +0.2705
```

## Required H0_obs configuration boundary

For a run to count as an EDCL `H0_obs` mechanism test, it must use the corrected observed-frame likelihood configuration:

```text
EDCL + local H0:
  H0_edcl is required.
  direct H0.riess2020 is forbidden.
  derived H0_obs is required.
  derived delta0 is required.

EDCL no-H0:
  H0_edcl is forbidden.
  direct H0.riess2020 is forbidden.

LCDM + local H0:
  direct H0.riess2020 is allowed.
```

A stale EDCL+H0 run that uses direct `H0.riess2020` is a configuration failure, not a physics test of the observed-frame `H0_obs` mechanism.

The relevant implementation/guard path is:

```text
cosmology/cobaya/edcl_cosmo_lateonly.yaml.in
cosmology/cobaya/edcl_cosmo_full.yaml.in
cosmology/likelihoods/H0_edcl_func.py
cosmology/scripts/check_no_doublecount_sh0es.py
cosmology/scripts/validate_tiera1_lateonly_results.py
cosmology/scripts/run_tiera1_lateonly_suite.py
```

## Claim levels

| Claim level | Evidence required | Current status | Allowed language |
|---|---|---|---|
| 1. Mechanism activation | Correct `H0_edcl` observed-frame likelihood; nonzero `alpha_R`; no-H0 collapse; high-z safety; stale direct-H0 EDCL configs ruled out by guard/validator | Current Tier-A1 chain audit supports this; corrected runner/guard path is being aligned for reproducibility | “Tier-A1 validates a working `H0_obs` calibration-drift mechanism.” |
| 2. Robust late-time channel | Best-fit component accounting; likelihood ablations; kernel/prior/local-anchor robustness; workdir-backed provenance from corrected runner | Partially complete: best-fit component accounting is chain-verified in `cosmology/results/tierA1_chain_component_audit.json`; ablations, robustness checks, and workdir provenance remain to run/locate | “Robust late-time Hubble-resolution channel.” |
| 3. Planck-compatible resolution | Planck distance-prior preflight and full Tier-A2 Planck likelihood with no-H0 controls; integrated-distance effects quantified | To run | “Substantially resolves the Hubble tension in the tested Planck+late data combination.” |
| 4. Strong model-comparison resolution | Fair baselines (`wCDM`, `w0waCDM`, generic calibration offset) plus AIC/BIC/evidence with documented priors, datasets, and nested-sampler provenance | To run | “Favored over specified alternatives under documented priors and datasets.” |

## Disallowed current wording

Do not currently use unqualified statements like:

- “EDCL decisively resolves the Hubble tension.”
- “EDCL successfully resolves the Hubble tension.”
- “EDCL is favored by decisive evidence.”
- “alpha_R is 3.9 sigma from zero.”
- “Full CMB validation is complete.”
- “The Tier-A1 result proves Planck compatibility.”

## Strong objective to preserve

The research objective remains to earn the stronger claim. The validation path is:

```text
correct H0_edcl observed-frame likelihood
→ corrected runner/guard/validator path
→ best-fit chain component accounting
→ workdir-backed provenance for configs/logs/environment
→ likelihood ablations
→ kernel/prior/local-anchor robustness
→ fair baselines
→ Tier-A2 Planck validation
→ stronger Hubble-resolution wording if results support it
```

## Current safe wording

Use wording like:

```text
Tier-A1 verifies an observed-frame H0_obs calibration channel: alpha_R activates under the local H0_obs likelihood and collapses without it. In this chain set, the total best-fit improvement over LCDM is modest and comes primarily from the H0/H0_obs term, with small BAO/SN reallocations.
```

Do not shorten this to a full-resolution claim.
