# Hubble Claim Discipline

This document gives wording rules for Hubble-related claims in the manuscript and repo.

Use this together with:

```text
docs/HUBBLE_RESOLUTION_CLAIM_LADDER.md
docs/HOW_TO_REPRODUCE_TIER_A1_OUTPUTS.md
cosmology/docs/H0_LIKELIHOOD_FIX.md
```

## Current evidence level

The current public Tier-A1 validation supports:

```text
a custom observed-frame local-Hubble likelihood
activation of alpha_R with the local H0_obs driver
a no-H0 control in which alpha_R shifts toward zero, but does not pass the configured q95 collapse threshold in the current compact summary
a matched observed-frame value H0_obs = 73.04 ± 0.95 km/s/Mpc
a modest late-only best-fit improvement, Delta chi2 = -1.0627
chain-verified best-fit component accounting in cosmology/results/tierA1_chain_component_audit.json
```

Current no-H0 threshold status:

```text
legacy unweighted-row q95(alpha_R) in the original compact no-H0 control = 0.0497; current weighted no-H0 q95 diagnostics are 0.0470 sampled-density, 0.0341 fixed-density, and 0.033860544 same-model P1/P2 fixed-density
configured collapse pass threshold = q95(alpha_R) <= 0.03
status = collapse tendency, not configured-threshold collapse pass
```

Current chain-verified component accounting for EDCL+H0_obs vs LCDM:

```text
Delta chi2_total     = -1.0627
Delta chi2_H0/H0_obs = -1.0182
Delta chi2_BAO       = -0.3150
Delta chi2_SN        = +0.2705
```

## Configuration boundary for any H0_obs claim

An EDCL run counts as an `H0_obs` mechanism test only if it uses the corrected observed-frame likelihood configuration:

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

A stale EDCL+H0 run using direct `H0.riess2020` is a configuration failure, not a physics test of the observed-frame mechanism.

Relevant implementation and enforcement files:

```text
cosmology/likelihoods/H0_edcl_func.py
cosmology/scripts/check_no_doublecount_sh0es.py
cosmology/scripts/validate_tiera1_lateonly_results.py
cosmology/scripts/run_tiera1_lateonly_suite.py
```

## Preferred current wording

Use:

```text
Tier-A1 supports a working H0_obs calibration-drift mechanism in late-only data: alpha_R activates when the local observed-frame H0_obs likelihood is included, and the no-H0 control shifts alpha_R toward zero. The old compact no-H0 unweighted row quantile q95(alpha_R)=0.0497 is superseded for current claim wording. Current weighted diagnostics give sampled-density no-H0 q95(alpha_R)=0.0470, fixed-density no-H0 q95(alpha_R)=0.0341, and same-model P1/P2 fixed-density no-H0 q95(alpha_R)=0.033860544; all exceed the configured q95<=0.03 posterior-tail threshold, so the no-H0 result supports profile-level collapse/collapse tendency rather than a threshold pass.
```

or:

```text
The current Tier-A1 result is a mechanism-activation test with a no-H0 collapse-tendency control, not yet a decisive model-comparison resolution.
```

or:

```text
Tier-A1 verifies an observed-frame H0_obs calibration channel: alpha_R activates under the local H0_obs likelihood, while the no-H0 control shifts alpha_R toward zero but does not satisfy the configured q95 collapse pass threshold in the current compact summary. In this chain set, the total best-fit improvement over LCDM is modest and comes primarily from the H0/H0_obs term, with small BAO/SN reallocations.
```

## Avoid for current Tier-A1

Do not use unqualified phrases such as:

```text
EDCL resolves the Hubble tension.
EDCL successfully resolves the Hubble tension in late-only data.
EDCL is favored by decisive evidence.
alpha_R is 3.9 sigma from zero.
The full Planck/CMB validation is complete.
The Tier-A1 result proves Planck compatibility.
The exp kernel is uniquely viable.
```

Also avoid saying that `alpha_R` simply "collapses without" the local driver unless the configured no-H0 q95 threshold is actually satisfied.

The final statement about the exp kernel requires a documented scan before it can be used.

## Numerical wording

Use:

```text
alpha_R = 0.0826 ± 0.0408, about 2.0 sigma from zero by mean/std.
```

Do not use stronger significance language unless the statistic is explicitly defined and reproduced.

## BBN and integrated-distance wording

BBN and integrated-distance comments should be treated as disclosure/diagnostic items until verified by the relevant corrected chain outputs and/or Tier-A2 runs.

Do not present BBN consistency, high-redshift suppression, or the Hubble-ratio figure as decisive Planck compatibility.

## Stronger wording target

The goal is to earn stronger Hubble-resolution wording through the claim ladder in:

```text
docs/HUBBLE_RESOLUTION_CLAIM_LADDER.md
```

Best-fit component accounting is now chain-verified, but stronger wording still requires:

```text
workdir-backed provenance
likelihood ablations
kernel/prior/local-anchor robustness scans
fair baselines
Tier-A2/Planck validation
documented Bayesian-evidence provenance, if evidence claims are made
```

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
