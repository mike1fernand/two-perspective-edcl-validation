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

## Tier-A1: late-only cosmology validation (CLASS + Cobaya)

Tier-A1 is heavier and depends on external downloads/builds. The canonical entrypoint is now the Python suite runner:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile iterate
```

The shell wrapper delegates to the same runner:

```bash
bash RUN_TIER_A_VALIDATION.sh
```

For Colab cell-ready commands, use `docs/COLAB_GUIDE.md`.

Before running MCMC, run the setup-only path:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py \
  --profile iterate \
  --skip-mcmc \
  --no-validate
```

The setup-only path must pass CLASS patch/build, EDCL smoke/preflight, YAML rendering, H0-likelihood invariant checks, Cobaya initialization tests, and bundle creation before full MCMC results are interpreted.

### H0-likelihood convention enforced by the corrected Tier-A1 path

| Run type | Required local-H0 behavior |
|---|---|
| LCDM + local H0 | May use direct `H0.riess2020` |
| EDCL + local H0 | Must use custom `H0_edcl` |
| EDCL + local H0 | Must not use direct `H0.riess2020` |
| EDCL no-H0 control | Must contain no local-H0 likelihood |

The EDCL local-H0 likelihood compares:

```text
H0_obs = H0 * (1 + alpha_R * 0.7542)
```

against the local Riess value through `H0_edcl`.

### Core Tier-A1 claims validated or targeted

| Paper claim / result | What is validated | Script(s) | Evidence location | Pass criterion / current status |
|---|---|---|---|---|
| EDCL implements a custom observed-frame local-Hubble likelihood | The local anchor is applied to `H0_obs = H0_theory * (1 + delta0)`, not directly to the theory-frame `H0` | `cosmology/scripts/run_tiera1_lateonly_suite.py`, `RUN_TIER_A_VALIDATION.sh`, `cosmology/scripts/check_no_doublecount_sh0es.py`, `cosmology/scripts/validate_tiera1_lateonly_results.py`, `cosmology/likelihoods/H0_edcl_func.py`, `tests/test_h0_obs_likelihood.py` | rendered YAMLs under `<workdir>/yamls/`, validator report, guard logs, regression test | EDCL+H0_obs YAML uses `H0_edcl`; EDCL+H0_obs YAML does not use `H0.riess2020`; regression test passes |
| Tier-A1 setup/build reproducibility | A fresh Linux/Colab-style run can clone CLASS, apply `cosmology/patches/class_edcl.patch`, build `classy`, and pass EDCL smoke/preflight checks | `cosmology/scripts/run_tiera1_lateonly_suite.py`, `cosmology/scripts/smoke_test_classy_edcl.py`, `cosmology/scripts/preflight_tiera_background.py`, `cosmology/scripts/validate_patch.py` | `<workdir>/logs/`, `<workdir>/manifest.json`, `<workdir>/bundle_edcl_tiera1.zip` | setup-only run completes and bundle contains logs, YAMLs, manifest, and smoke/preflight output |
| Tier-A1 mechanism activation | With the local `H0_obs` constraint included, the calibration parameter activates: `alpha_R = 0.0826 ± 0.0408` in the current paper chain audit | `cosmology/scripts/validate_tiera1_lateonly_results.py`, `cosmology/scripts/analyze_chains.py` for standalone chain-file analysis | `cosmology/results/tierA1_hubble_result_card.json` and `cosmology/results/tierA1_chain_component_audit.json` | Activation is present but modest: about `2.0σ` by mean/std |
| No-H0 collapse test | Removing the local H0 driver shifts `alpha_R` toward zero | `cosmology/scripts/validate_tiera1_lateonly_results.py`, `cosmology/scripts/analyze_chains.py` for standalone chain-file analysis | `cosmology/results/tierA1_hubble_result_card.json` and `cosmology/results/tierA1_chain_component_audit.json` | Current paper chain audit: `alpha_R = 0.0147 ± 0.0142` in no-H0 run |
| Observed-frame H0 match | The fitted observed-frame value is consistent with the local anchor under the custom likelihood | `cosmology/scripts/validate_tiera1_lateonly_results.py`, `cosmology/likelihoods/H0_edcl_func.py`, `tests/test_h0_obs_likelihood.py` | `cosmology/results/tierA1_hubble_result_card.json` and `cosmology/results/tierA1_chain_component_audit.json` | Current paper chain audit: `H0_obs = 73.04 ± 0.95` km/s/Mpc |
| Late-only model-comparison status | EDCL has a small best-fit improvement over flat LCDM in the Tier-A1 late-only data combination | `cosmology/scripts/analyze_chains.py`, `cosmology/scripts/validate_tiera1_lateonly_results.py` | `cosmology/results/tierA1_hubble_result_card.json` and `cosmology/results/tierA1_chain_component_audit.json` | Current paper chain audit: `Delta chi2 = -1.0627`, `Delta AIC ≈ 0.94`; not a decisive model-comparison result |
| Tier-A1 component accounting | Chain columns decompose the best-fit chi2 into BAO, SN, and H0/H0_obs components for the available LCDM, EDCL+H0_obs, and EDCL no-H0 chains | `cosmology/scripts/analyze_chains.py` and release/uploaded Tier-A chain artifacts | `cosmology/results/tierA1_chain_component_audit.json` | Chain-verified best-fit accounting: EDCL+H0_obs vs LCDM gives `Delta chi2 = -1.0627`, with H0/H0_obs = `-1.0182`, BAO = `-0.3150`, SN = `+0.2705` |
| Full Hubble-resolution target | Test whether the mechanism survives exact decomposition, robustness checks, fair baselines, and Tier-A2/Planck validation | Future analysis | `docs/HUBBLE_RESOLUTION_CLAIM_LADDER.md` | Not yet claimed as completed in Tier-A1 |

For details, see:

- `TIER_A_COMPLETE_DOCUMENTATION.md`
- `docs/HOW_TO_REPRODUCE_TIER_A1_OUTPUTS.md`
- `docs/COLAB_GUIDE.md`
- `cosmology/docs/H0_LIKELIHOOD_FIX.md`
- `docs/HUBBLE_RESOLUTION_CLAIM_LADDER.md`
- `docs/TIER_A_ARTIFACT_MANIFEST.md`
