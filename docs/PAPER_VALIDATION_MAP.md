# Paper validation map (Two-Perspective / EDCL)

This document maps paper claims to the current scripts and artifacts in this repository.

For the expanded referee-facing matrix, see:

```text
docs/VALIDATION_MATRIX.md
```

## Claim boundary

Current Tier-A1 status:

```text
Tier-A1 supports a working H0_obs calibration-drift mechanism with activation and no-H0 best-fit/profile-collapse evidence; the strict no-H0 posterior-tail q95 collapse criterion is not passed.
```

Do not use Tier-A1 alone as a completed Hubble-tension resolution claim.

---

## Tier-B: formalism validations, Sections 2–4

Run:

```bash
python scripts/run_all_tierB.py
```

| Paper claim / element | Script | Main artifact(s) |
|---|---|---|
| Constant local observed speed iff matched calibration / Theorem 3.1 | `scripts/run_all_tierB.py` | `paper_artifacts/fig_theorem31_wavepacket_validation.png`, `paper_artifacts/fig_theorem31_local_speed_validation.png`, `paper_artifacts/theorem31_local_speed_report.txt` |
| Interface scattering invariance | `scripts/run_all_tierB.py` | `paper_artifacts/fig_interface_scattering_invariance.png` |
| Spectral Jacobian mapping | `scripts/run_all_tierB.py` | `paper_artifacts/fig_spectral_mapping.png` |
| LR cone / microcausality rescaling | `scripts/run_all_tierB.py` | `paper_artifacts/fig_lr_cone_rescaling.png` |
| Real-world Theorem 3.1 variant | `scripts/run_all_tierB.py` | `paper_artifacts/fig_theorem31_realworld_validation.png` |

---

## Track-0: kernel-only / Phase-1 background mapping

Run:

```bash
python track0/run_track0_kernel_consistency.py
```

| Paper claim / element | Script | Main artifact(s) |
|---|---|---|
| Kernel consistency / high-z safety diagnostic | `track0/run_track0_kernel_consistency.py` | `paper_artifacts/track0/fig_kernel_consistency.png` |

---

## Tier-A1: late-only cosmology validation / Hubble subsection

Canonical runner:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile iterate
```

Setup-only check before MCMC:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py \
  --profile iterate \
  --skip-mcmc \
  --no-validate
```

Compatibility wrappers:

```text
RUN_TIER_A_VALIDATION.sh
scripts/RUN_TIER_A_VALIDATION.sh
COLAB_TIER_A_VALIDATION.py
colab/COLAB_TIER_A_VALIDATION.py
```

These wrappers should delegate to the canonical runner.

### Tier-A1 configuration

Late-only EDCL validation uses:

```text
DESI DR2 BAO
PantheonPlus
local observed-frame H0_obs anchor
```

YAML templates:

```text
cosmology/cobaya/lcdm_lateonly.yaml.in
cosmology/cobaya/edcl_cosmo_lateonly.yaml.in
cosmology/cobaya/edcl_cosmo_lateonly_no_sh0es.yaml.in
```

Canonical H0 helper:

```text
cosmology/likelihoods/H0_edcl_func.py
```

Guard and validator:

```text
cosmology/scripts/check_no_doublecount_sh0es.py
cosmology/scripts/validate_tiera1_lateonly_results.py
```

Standalone chain analyzer:

```text
cosmology/scripts/analyze_chains.py
```

### H0-likelihood rule

EDCL local-H0 runs must apply the local anchor to:

```text
H0_obs = H0 * (1 + alpha_R * 0.7542)
```

not directly to sampled theory-frame `H0`.

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

### Current compact Tier-A1 result artifacts

```text
cosmology/results/tierA1_hubble_result_card.json
cosmology/results/tierA1_chain_component_audit.json
```

Corrected runner workdir artifacts:

```text
<workdir>/manifest.json
<workdir>/logs/
<workdir>/yamls/
<workdir>/chains/
<workdir>/results_summary.json
<workdir>/results_report.md
<workdir>/bundle_edcl_tiera1.zip
```

---

## Related documentation

```text
README.md
README_SCRIPTS.md
traceability.md
docs/COLAB_GUIDE.md
docs/HOW_TO_REPRODUCE_TIER_A1_OUTPUTS.md
docs/TIER_A_ARTIFACT_MANIFEST.md
docs/HUBBLE_RESOLUTION_CLAIM_LADDER.md
cosmology/docs/H0_LIKELIHOOD_FIX.md
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
