# Local run guide (developer/local)

This guide is optional for referees, but useful for archiving and for reproducing runs outside Colab.

---

## Tier‑B + Track‑0 (pure Python)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

python scripts/run_all_tierB.py
python track0/run_track0_kernel_consistency.py
```

---

## Tier‑A late‑only (CLASS + Cobaya)

Tier‑A requires:
- a compiler toolchain (gcc/g++, gfortran, make)
- python dev headers
- Cobaya and its likelihood data

Canonical runner:

```bash
bash RUN_TIER_A_VALIDATION.sh
```

The script prints the final work directory. Use it to run validation again if needed:

```bash
python cosmology/scripts/validate_tiera1_lateonly_results.py --workdir <WORKDIR> --profile referee
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
