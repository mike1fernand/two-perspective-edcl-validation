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

## Tier-A1 late-only cosmology validation

Canonical entrypoints:

- Colab / local Python: `cosmology/scripts/run_tiera1_lateonly_suite.py`
- Shell wrapper: `RUN_TIER_A_VALIDATION.sh`
- Colab instructions: `docs/COLAB_GUIDE.md`

Canonical run sequence:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py \
  --profile iterate \
  --skip-mcmc \
  --no-validate
```

Then, after setup-only checks pass:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile iterate
```

For a stricter run:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile referee
```

Primary validation / guard scripts:

- `cosmology/scripts/smoke_test_classy_edcl.py`
- `cosmology/scripts/check_no_doublecount_sh0es.py`
- `cosmology/scripts/validate_tiera1_lateonly_results.py`
- `cosmology/scripts/analyze_chains.py` for standalone chain-file analysis with `--chains-dir`

Primary Tier-A documentation:

- `TIER_A_COMPLETE_DOCUMENTATION.md`
- `docs/HOW_TO_REPRODUCE_TIER_A1_OUTPUTS.md`
- `docs/COLAB_GUIDE.md`
- `cosmology/docs/H0_LIKELIHOOD_FIX.md`
- `docs/HUBBLE_RESOLUTION_CLAIM_LADDER.md`
- `docs/HUBBLE_CLAIM_DISCIPLINE.md`
- `docs/TIER_A_ARTIFACT_MANIFEST.md`
- `docs/HUBBLE_FIGURE_TRACEABILITY.md`

EDCL local-H0 convention enforced by the corrected Tier-A1 path:

- EDCL + local H0 must use `H0_edcl`.
- EDCL + local H0 must not use `H0.riess2020`.
- EDCL no-H0 must contain no local-H0 likelihood.
- LCDM may use direct `H0.riess2020`.

Canonical current Tier-A1 result card:

- `cosmology/results/tierA1_hubble_result_card.json`

Current Tier-A1 status:

- The current result validates a working `H0_obs` calibration-drift mechanism and activation/collapse behavior in late-only data.
- Best-fit component accounting is chain-verified in `cosmology/results/tierA1_chain_component_audit.json`: EDCL+H0_obs vs LCDM gives `Delta chi2 = -1.0627`, with H0/H0_obs = `-1.0182`, BAO = `-0.3150`, and SN = `+0.2705`.
- Stronger claims still require workdir-backed provenance, likelihood ablations, robustness scans, fair baselines, and Tier-A2/Planck validation.

Tier-A1 produces:

- CLASS/EDCL smoke and preflight logs under the run workdir.
- rendered YAMLs under `<workdir>/yamls/`.
- MCMC chains under `<workdir>/chains/`.
- validation summary: `<workdir>/results_summary.json`.
- validation report: `<workdir>/results_report.md`.
- run manifest: `<workdir>/manifest.json`.
- optional bundle zip: `<workdir>/bundle_edcl_tiera1.zip`.

Generated Tier-A1 outputs are not intended for normal git history. Heavy run artifacts should be published as GitHub Release assets if needed for external reproducibility.

Next artifact needed:

- timestamped Tier-A workdir artifacts for YAML/config/log/environment provenance, especially `edcl_tiera1_20251221_212236/` and `edcl_tiera1_20251221_212444/`, or regenerated equivalent workdirs produced by the corrected runner.
