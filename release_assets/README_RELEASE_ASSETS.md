# Release assets (attach to GitHub Releases)

This folder contains **example heavy outputs** that should *not* be committed to git history.

Recommended use:
1. Create a GitHub Release for the paper tag (see `repo/docs/GITHUB_PUBLISH_CHECKLIST.md`).
2. Zip (or upload as-is) the contents of this folder as Release assets.

Contents may include:
- `chains/` — Cobaya/GetDist chain outputs for Tier‑A
- `edcl_tiera1_*/` — timestamped Tier‑A work directories (logs, bundles, configs)

If you re-run Tier‑A, publish the new workdir and chains similarly.


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

## NOH0 checkpointed diagnostics asset

`noh0_checkpointed_diagnostics_2026-05-04.zip` archives the checkpointed BAO-only, SN-only, and same-model P1/P2 fixed-density no-H0 diagnostics used to support the current claim ladder. The asset documents that the strict no-H0 posterior-tail q95 threshold is not passed: sampled-density no-H0 fails, and fixed-density same-model no-H0 remains a near-threshold failure. BAO-only and SN-only results are diagnostic-only.
