# Hubble Resolution Claim Ladder

This document preserves the strong Hubble-resolution objective while separating completed evidence from future validation targets.

The current Tier-A1 result is a mechanism-activation result with a no-H0 collapse-tendency control. It is not, by itself, a completed Hubble-tension resolution.

## Current canonical Tier-A1 result

| Quantity | Current value |
|---|---:|
| `alpha_R` | `0.0826 ± 0.0408` |
| `delta0 = 0.7542 alpha_R` | `0.0623 ± 0.0308` |
| `H0_theory` in EDCL+H0_obs run | `68.80 ± 1.85` km/s/Mpc |
| `H0_obs` in EDCL+H0_obs run | `73.04 ± 0.95` km/s/Mpc |
| No-H0 sampled-density `q95(alpha_R)` | `0.0470` |
| No-H0 fixed-density `q95(alpha_R)` | `0.0341` |
| No-H0 same-model P1/P2 fixed-density `q95(alpha_R)` | `0.033860544` |
| Configured collapse pass threshold | `q95(alpha_R) <= 0.03` |
| No-H0 threshold status | collapse tendency, not configured-threshold collapse pass |
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
| 1. Mechanism activation | Correct `H0_edcl` observed-frame likelihood; nonzero `alpha_R`; no-H0 control that shifts `alpha_R` toward zero; explicit threshold accounting for the configured no-H0 collapse test; high-z safety; stale direct-H0 EDCL configs ruled out by guard/validator | Current Tier-A1 chain audit supports activation and no-H0 best-fit/profile collapse. The sampled-density no-H0 posterior-tail criterion fails (`q95=0.0470`) and the fixed-density same-model control remains a near-threshold failure (`q95=0.033860544 > 0.03`); corrected runner/guard path is aligned for reproducibility | “Tier-A1 supports a working `H0_obs` calibration-drift mechanism with a no-H0 collapse-tendency control.” |
| 2. Robust late-time channel | Best-fit component accounting; archived BAO/SN checkpoint diagnostics plus broader likelihood-sector/fair-baseline robustness; workdir-backed provenance from corrected runner; configured-threshold no-H0 collapse or a clearly justified revised threshold | Partially complete: best-fit component accounting and BAO/SN diagnostic ablations are archived; broader robustness checks, threshold-passing no-H0 collapse, fair baselines, and workdir provenance remain future/partial | “Robust late-time Hubble-resolution channel.” |
| 3. Planck-compatible resolution | Planck distance-prior preflight and full Tier-A2 Planck likelihood with no-H0 controls; integrated-distance effects quantified | To run | “Substantially resolves the Hubble tension in the tested Planck+late data combination.” |
| 4. Strong model-comparison resolution | Fair baselines (`wCDM`, `w0waCDM`, generic calibration offset) plus AIC/BIC/evidence with documented priors, datasets, and nested-sampler provenance | To run | “Favored over specified alternatives under documented priors and datasets.” |

## Disallowed current wording

Do not currently use unqualified statements like:

- “EDCL resolves the Hubble tension.”
- “EDCL resolves the Hubble tension.”
- “EDCL is favored by decisive evidence.”
- “alpha_R is 3.9 sigma from zero.”
- “Full CMB validation is complete.”
- “The Tier-A1 result proves Planck compatibility.”
- “The no-H0 control passes the configured collapse threshold.”

## Strong objective to preserve

The research objective remains to earn the stronger claim. The validation path is:

```text
correct H0_edcl observed-frame likelihood
→ corrected runner/guard/validator path
→ best-fit chain component accounting
→ configured-threshold no-H0 collapse or explicitly revised validation criterion
→ workdir-backed provenance for configs/logs/environment
→ archived BAO/SN diagnostics plus broader likelihood-sector/fair-baseline ablations
→ kernel/prior/local-anchor robustness
→ fair baselines
→ Tier-A2 Planck validation
→ stronger Hubble-resolution wording if results support it
```

## Current safe wording

Use wording like:

```text
Tier-A1 verifies an observed-frame H0_obs calibration channel: alpha_R activates under the local H0_obs likelihood, while the no-H0 control shifts alpha_R toward zero but does not satisfy the configured q95 collapse pass threshold in the current compact summary. In this chain set, the total best-fit improvement over LCDM is modest and comes primarily from the H0/H0_obs term, with small BAO/SN reallocations.
```

or:

```text
Tier-A1 supports a working H0_obs calibration-drift mechanism in late-only data: alpha_R activates when the local observed-frame H0_obs likelihood is included, and the no-H0 control shifts alpha_R toward zero. The old compact no-H0 unweighted row quantile q95(alpha_R)=0.0497 is superseded for current claim wording. Current weighted diagnostics give sampled-density no-H0 q95(alpha_R)=0.0470, fixed-density no-H0 q95(alpha_R)=0.0341, and same-model P1/P2 fixed-density no-H0 q95(alpha_R)=0.033860544; all exceed the configured q95<=0.03 posterior-tail threshold, so the no-H0 result supports profile-level collapse/collapse tendency rather than a threshold pass.
```

Do not shorten this to a full-resolution claim.

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
