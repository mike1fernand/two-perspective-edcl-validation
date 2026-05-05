# Hubble Figure Traceability

This document records the provenance bridge for the Hubble-ratio / Hubble-drift figure used in the manuscript.

## Manuscript figure

The cleaned manuscript/package uses:

```text
figures/hubble_drift_phase1.png
```

## Repository generation script

The repository script is:

```text
cosmology/scripts/make_fig_hubble_ratio_from_class.py
```

The script computes and plots the background diagnostic:

```text
H_EDCL(z) / H_LCDM(z)
```

from patched CLASS. Its stated purpose is to verify the LCDM limit and the high-redshift-safety behavior of the Phase-1 background rescaling.

The script's default output path is currently:

```text
cosmology/paper_artifacts/fig_hubble_ratio_from_class.png
```

Example command:

```bash
python cosmology/scripts/make_fig_hubble_ratio_from_class.py \
  --class-path /path/to/edcl_class_public \
  --alpha_R 0.118 \
  --log10_l0 -20.91
```

## Required CLASS runtime

This figure requires an EDCL-patched CLASS/classy runtime. The repo includes the patch at:

```text
cosmology/patches/class_edcl.patch
```

Before generating the figure, verify the runtime with:

```bash
python cosmology/scripts/smoke_test_classy_edcl.py \
  --class-path /path/to/edcl_class_public
```

Required smoke-test result:

```text
Baseline compute OK.
EDCL compute OK.
```

## Required provenance bridge

When producing the manuscript asset, document the copy/rename step explicitly:

```text
cosmology/paper_artifacts/fig_hubble_ratio_from_class.png
→ figures/hubble_drift_phase1.png
```

If the script is updated in the future to write directly to the manuscript asset path, update this document and `docs/VALIDATION_MATRIX.md`.

## Relation to Tier-A1 H0_obs validation

This figure is a background/high-redshift-safety diagnostic. It is not the Tier-A1 MCMC validation and it does not by itself establish the observed-frame local-Hubble mechanism.

The Tier-A1 H0_obs mechanism evidence is traced through:

```text
cosmology/scripts/run_tiera1_lateonly_suite.py
cosmology/scripts/check_no_doublecount_sh0es.py
cosmology/scripts/validate_tiera1_lateonly_results.py
cosmology/results/tierA1_hubble_result_card.json
cosmology/results/tierA1_chain_component_audit.json
```

The corrected Tier-A1 path enforces:

```text
EDCL + local H0 must use H0_edcl
EDCL + local H0 must not use H0.riess2020
EDCL no-H0 must contain no local-H0 likelihood
LCDM may use direct H0.riess2020
```

## Validation status

The figure supports the Phase-1 background/high-redshift-safety diagnostic. It should not be used by itself as evidence for decisive Hubble-tension resolution.

Stronger resolution claims require:

```text
exact likelihood decomposition
likelihood ablations
robustness scans
fair baselines
workdir-backed provenance
Tier-A2/Planck validation
```

as described in `docs/HUBBLE_RESOLUTION_CLAIM_LADDER.md`.

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
