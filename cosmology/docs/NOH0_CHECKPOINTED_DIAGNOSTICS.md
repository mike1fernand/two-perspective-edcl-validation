# NOH0 checkpointed diagnostics

This document records the checkpointed no-H0 diagnostics added after the Tier-A1 no-H0 threshold audit.

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


## Archived run labels

| Label | Role | Key result |
|---|---|---|
| `C1_fixedDensity_BAO_only_noH0` | Diagnostic BAO-only no-H0 ablation | best fit near `alpha_R=0`; `q95(alpha_R)≈0.120856`; diagnostic-only. |
| `C2_fixedDensity_SN_only_noH0` | Diagnostic SN-only no-H0 ablation | best fit near `alpha_R=0`; `q95(alpha_R)≈0.153656`; diagnostic-only. |
| `P1_A1b_ultra_fixed_noH0_seed61001` | Same-model fixed-density BAO+SN no-H0 repeat | `q95(alpha_R)=0.034149371`; near-threshold failure. |
| `P2_A1b_ultra_fixed_noH0_seed61002` | Same-model fixed-density BAO+SN no-H0 repeat | `q95(alpha_R)=0.033575635`; near-threshold failure. |
| `COMBINED_P1P2_A1b_ultra_fixed_noH0` | Combined same-model repeat | `q95(alpha_R)=0.033860544`; strict q95 threshold not passed. |

## How to reproduce or inspect

Use either:

```bash
python cosmology/scripts/noh0_checkpointed_diagnostics.py --help
```

or the Colab notebook:

```text
colab/NOH0_CLEAN_COLAB_BAO_SN_ABLATIONS_ENHANCED_v3_HOTFIX.ipynb
```

The archived checkpoint package is:

```text
release_assets/noh0_checkpointed_diagnostics_2026-05-04.zip
```

## Claim boundary

The diagnostics support activation plus no-H0 best-fit/profile collapse. They do **not** support a statement that the strict no-H0 posterior-tail q95 criterion passes, and they do **not** establish a completed Hubble-tension resolution.
