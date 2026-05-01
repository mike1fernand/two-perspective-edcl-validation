# Validation matrix (paper claim → scripts → artifacts)

This file is referee-facing. Each row maps a paper claim or figure to the script(s), artifacts, and pass/fail criteria that support it.

**Claim-discipline rule for Hubble results:** the current Tier-A1 cosmology result is a **mechanism-activation and collapse test**, not yet a decisive full Hubble-tension resolution. Stronger resolution language is reserved for the evidence ladder in `docs/HUBBLE_RESOLUTION_CLAIM_LADDER.md`.

---

## Tier-B: formalism/kinematics simulations (pure Python)

| Paper claim / figure | What is validated | Script to run | Primary artifact(s) | Pass criterion |
|---|---|---|---|---|
| Theorem 3.1 wavepacket behavior | Wavepacket propagation matches predicted scaling | `python scripts/run_all_tierB.py` | `paper_artifacts/fig_theorem31_wavepacket_validation.png` | Script completes with exit code 0 |
| Theorem 3.1 local-speed validation | Local-speed law holds in adiabatic/small-k regime | `python scripts/run_all_tierB.py` | `paper_artifacts/fig_theorem31_local_speed_validation.png`, `paper_artifacts/theorem31_local_speed_report.txt` | Script completes with exit code 0 |
| Interface scattering invariance | Scattering is invariant under interface placement within tolerance | `python scripts/run_all_tierB.py` | `paper_artifacts/fig_interface_scattering_invariance.png` | Script completes with exit code 0 |
| Spectral mapping | Spectrum mapping identity holds numerically | `python scripts/run_all_tierB.py` | `paper_artifacts/fig_spectral_mapping.png` | Script completes with exit code 0 |
| LR cone/front rescaling | LR cone/front rescaling matches prediction | `python scripts/run_all_tierB.py` | `paper_artifacts/fig_lr_cone_rescaling.png` | Script completes with exit code 0 |
| Real-world Theorem 3.1 variant | Validation on real-world-like parameterization | `python scripts/run_all_tierB.py` | `paper_artifacts/fig_theorem31_realworld_validation.png` | Script completes with exit code 0 |

Notes: Tier-B is designed to run offline with the Python dependencies in `requirements.txt`. Use the default embedded seeds for deterministic regeneration.

---

## Track-0: kernel/FRW consistency (pure Python)

| Paper claim / figure | What is validated | Script to run | Primary artifact(s) | Pass criterion |
|---|---|---|---|---|
| Kernel consistency check | Kernel integration/normalization consistency | `python track0/run_track0_kernel_consistency.py` | `paper_artifacts/track0/fig_kernel_consistency.png` | Script completes with exit code 0 |

---

## Tier-A: late-only cosmology validation (CLASS + Cobaya)

Tier-A is heavier and depends on external downloads/builds. Canonical entrypoints:

- Colab: `COLAB_TIER_A_VALIDATION.py`
- Local: `RUN_TIER_A_VALIDATION.sh`

### Core Tier-A1 claims validated or targeted

| Paper claim / result | What is validated | Script(s) | Evidence location | Pass criterion / current status |
|---|---|---|---|---|
| EDCL implements a custom observed-frame local-Hubble likelihood | The local anchor is applied to `H0_obs = H0_theory * (1 + delta0)`, not directly to the theory-frame `H0` | `RUN_TIER_A_VALIDATION.sh`, `COLAB_TIER_A_VALIDATION.py`, `cosmology/likelihoods/edcl_H0.py`, `tests/test_h0_obs_likelihood.py` | Tier-A reports, chain analysis outputs, regression test | Custom likelihood regression test passes; no standard `H0.riess2020` likelihood active in EDCL+H0 runs |
| Tier-A1 mechanism activation | With the local `H0_obs` constraint included, the calibration parameter activates: `alpha_R = 0.0826 ± 0.0408` in the current paper | Same as above | `cosmology/results/tierA1_hubble_result_card.json` and Tier-A chain artifacts | Activation is present but modest: about `2.0σ` by mean/std |
| No-H0 collapse test | Removing the local H0 driver shifts `alpha_R` toward zero | Same as above | Tier-A no-H0 chain analysis and result card | Current paper: `alpha_R = 0.0147 ± 0.0142` in no-H0 run |
| Observed-frame H0 match | The fitted observed-frame value is consistent with the local anchor under the custom likelihood | Same as above | Tier-A result card and chain outputs | Current paper: `H0_obs = 73.04 ± 0.95` km/s/Mpc |
| Late-only model-comparison status | EDCL has a small best-fit improvement over flat LCDM in the Tier-A1 late-only data combination | Same as above | Tier-A result card and chain outputs | Current paper: `Delta chi2 = -1.0627`, `Delta AIC ≈ 0.94`; not a decisive model-comparison result |
| Full Hubble-resolution target | Test whether the mechanism survives exact decomposition, robustness checks, fair baselines, and Tier-A2/Planck validation | Future analysis | `docs/HUBBLE_RESOLUTION_CLAIM_LADDER.md` | Not yet claimed as completed in Tier-A1 |

For details, see:

- `TIER_A_COMPLETE_DOCUMENTATION.md`
- `cosmology/docs/H0_LIKELIHOOD_FIX.md`
- `docs/HUBBLE_RESOLUTION_CLAIM_LADDER.md`
- `docs/TIER_A_ARTIFACT_MANIFEST.md`
