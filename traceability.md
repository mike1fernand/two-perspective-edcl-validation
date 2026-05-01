# Traceability ledger

This file maps paper elements to code paths and artifacts. For the expanded table, see `docs/VALIDATION_MATRIX.md`.

---

## Tier-B pure Python validations

| Paper element | Script(s) | Output artifact(s) |
|---|---|---|
| Theorem 3.1 wavepacket validation | `scripts/run_all_tierB.py` | `paper_artifacts/fig_theorem31_wavepacket_validation.png` |
| Theorem 3.1 local-speed validation | `scripts/run_all_tierB.py` | `paper_artifacts/fig_theorem31_local_speed_validation.png`, `paper_artifacts/theorem31_local_speed_report.txt` |
| Interface scattering invariance | `scripts/run_all_tierB.py` | `paper_artifacts/fig_interface_scattering_invariance.png` |
| Spectral mapping validation | `scripts/run_all_tierB.py` | `paper_artifacts/fig_spectral_mapping.png` |
| LR cone/front rescaling | `scripts/run_all_tierB.py` | `paper_artifacts/fig_lr_cone_rescaling.png` |
| Theorem 3.1 real-world variant | `scripts/run_all_tierB.py` | `paper_artifacts/fig_theorem31_realworld_validation.png` |

---

## Track-0 kernel consistency

| Paper element | Script(s) | Output artifact(s) |
|---|---|---|
| Kernel consistency check | `track0/run_track0_kernel_consistency.py` | `paper_artifacts/track0/fig_kernel_consistency.png` |

---

## Tier-A late-only cosmology validation

Canonical entrypoints:

- Colab: `COLAB_TIER_A_VALIDATION.py`
- Local: `RUN_TIER_A_VALIDATION.sh`

Primary validation scripts:

- `cosmology/scripts/analyze_chains.py`
- `cosmology/scripts/validate_tiera1_lateonly_results.py`

Primary Tier-A documentation:

- `TIER_A_COMPLETE_DOCUMENTATION.md`
- `cosmology/docs/H0_LIKELIHOOD_FIX.md`
- `docs/HUBBLE_RESOLUTION_CLAIM_LADDER.md`
- `docs/HUBBLE_CLAIM_DISCIPLINE.md`
- `docs/TIER_A_ARTIFACT_MANIFEST.md`
- `docs/HUBBLE_FIGURE_TRACEABILITY.md`

Canonical current Tier-A1 result card:

- `cosmology/results/tierA1_hubble_result_card.json`

Current Tier-A1 status:

- The current result validates a working `H0_obs` calibration-drift mechanism and activation/collapse behavior in late-only data.
- Stronger claims require exact component chi2 accounting, ablations, robustness scans, fair baselines, and Tier-A2/Planck validation.

Tier-A produces:

- preflight plots: `cosmology/paper_artifacts/`
- run output workdir: `edcl_tiera1_YYYYMMDD_HHMMSS/` (not intended for git; publish as a Release asset)
- optional bundle zip in the workdir (publish as a Release asset)

Next artifact needed:

- exact per-likelihood chi2 decomposition from production-chain likelihood components, or a clearly labeled emulator-derived substitute if chain components are unavailable.
