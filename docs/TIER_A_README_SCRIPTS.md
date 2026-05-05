# Tier-A1 script note

This file is a short Tier-A1-specific companion to:

```text
README_SCRIPTS.md
```

Do not treat this file as a second independent script manual. The repo uses one canonical Tier-A1 execution path:

```text
cosmology/scripts/run_tiera1_lateonly_suite.py
```

Legacy entry points are compatibility wrappers only.

## Canonical Tier-A1 commands

Setup-only check before MCMC:

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

Referee profile:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile referee
```

## Compatibility wrappers

These wrappers should delegate to the canonical Python runner and should not contain separate YAML-generation or direct `cobaya-run` logic:

```text
RUN_TIER_A_VALIDATION.sh
scripts/RUN_TIER_A_VALIDATION.sh
COLAB_TIER_A_VALIDATION.py
colab/COLAB_TIER_A_VALIDATION.py
```

## Chain-only analysis

For existing chains only:

```bash
python3 cosmology/scripts/analyze_chains.py \
  --chains-dir ./chains \
  --output tierA1_chain_verification.json \
  --plot
```

This is a chain-only diagnostic. It does not validate rendered YAMLs, logs, workdir structure, or H0-likelihood invariants. The standalone analyzer uses the configured no-H0 collapse threshold `q95(alpha_R) <= 0.03`; if the no-H0 q95 exceeds that value, report the result as a collapse tendency rather than a configured-threshold collapse pass.

For full workdir validation:

```bash
python3 cosmology/scripts/validate_tiera1_lateonly_results.py \
  --workdir <WORKDIR> \
  --profile iterate
```

## H0_obs convention

EDCL+local-H0 runs must use the custom observed-frame likelihood:

```text
H0_edcl
```

with:

```text
H0_obs = H0 * (1 + alpha_R * 0.7542)
```

Configuration rules:

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

A stale EDCL+H0 run using direct `H0.riess2020` is a configuration failure, not a physics test.

## Corrected workdir outputs

The canonical runner writes:

```text
<workdir>/manifest.json
<workdir>/logs/
<workdir>/yamls/
<workdir>/chains/
<workdir>/results_summary.json
<workdir>/results_report.md
<workdir>/bundle_edcl_tiera1.zip
```

Rendered YAMLs should be under:

```text
<workdir>/yamls/
```

not under:

```text
cosmology/cobaya/
```

## Claim boundary

Current safe Tier-A1 wording:

```text
Tier-A1 supports a working H0_obs calibration-drift mechanism in late-only data: alpha_R activates when the local observed-frame H0_obs likelihood is included, and the no-H0 control shifts alpha_R toward zero. The old compact no-H0 unweighted row quantile q95(alpha_R)=0.0497 is superseded for current claim wording. Current weighted diagnostics give sampled-density no-H0 q95(alpha_R)=0.0470, fixed-density no-H0 q95(alpha_R)=0.0341, and same-model P1/P2 fixed-density no-H0 q95(alpha_R)=0.033860544; all exceed the configured q95<=0.03 posterior-tail threshold, so the no-H0 result supports profile-level collapse/collapse tendency rather than a threshold pass.
```

Do not present Tier-A1 alone as a completed Hubble-tension resolution.

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
