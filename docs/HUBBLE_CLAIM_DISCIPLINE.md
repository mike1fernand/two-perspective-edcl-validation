# Hubble Claim Discipline

This document gives wording rules for Hubble-related claims in the manuscript and repo.

## Current evidence level

The current public Tier-A1 validation supports:

- a custom observed-frame local-Hubble likelihood;
- activation of `alpha_R` with the local `H0_obs` driver;
- collapse of `alpha_R` when the local driver is removed;
- a matched observed-frame value `H0_obs = 73.04 ± 0.95` km/s/Mpc;
- a modest late-only best-fit improvement, `Delta chi2 = -1.0627`;
- chain-verified best-fit component accounting in `cosmology/results/tierA1_chain_component_audit.json`, where EDCL+H0_obs vs LCDM gives H0/H0_obs = `-1.0182`, BAO = `-0.3150`, and SN = `+0.2705`.

## Preferred current wording

Use:

```text
Tier-A1 validates a working H0_obs calibration-drift mechanism and activation/collapse behavior in late-only data.
```

or:

```text
The current Tier-A1 result is a mechanism-activation test, not yet a decisive model-comparison resolution.
```

## Avoid for current Tier-A1

Do not use unqualified phrases such as:

- “EDCL decisively resolves the Hubble tension.”
- “EDCL successfully resolves the Hubble tension in late-only data.”
- “alpha_R is 3.9 sigma from zero.”
- “The full Planck/CMB validation is complete.”
- “The exp kernel is uniquely viable” unless supported by a documented scan.

## Numerical wording

Use:

```text
alpha_R = 0.0826 ± 0.0408, about 2.0 sigma from zero by mean/std.
```

Do not use stronger significance language unless the statistic is explicitly defined and reproduced.

## Stronger wording target

The goal is to earn stronger Hubble-resolution wording through the claim ladder in `docs/HUBBLE_RESOLUTION_CLAIM_LADDER.md`. Best-fit component accounting is now chain-verified, but stronger wording still requires workdir-backed provenance, likelihood ablations, robustness scans, fair baselines, and Tier-A2/Planck validation.
