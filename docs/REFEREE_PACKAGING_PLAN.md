# Referee-oriented packaging plan

This repository contains a tiered validation suite intended to let a referee or third party reproduce:

```text
Tier-B   formalism/kinematics simulations, pure Python, fast
Track-0  kernel/FRW consistency checks, pure Python, fast
Tier-A1  late-only cosmology validation, CLASS + Cobaya, heavier
```

The packaging goal is:

```text
one canonical path per tier
clear paper-claim to script to artifact traceability
no duplicated Tier-A1 workflows
heavy artifacts outside normal git history
claim wording matched to completed evidence
```

## A. Canonical entrypoints

### Tier-B

Canonical runner:

```bash
python scripts/run_all_tierB.py
```

Primary artifacts:

```text
paper_artifacts/
```

### Track-0

Canonical runner:

```bash
python track0/run_track0_kernel_consistency.py
```

Primary artifact:

```text
paper_artifacts/track0/fig_kernel_consistency.png
```

### Tier-A1

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

Referee profile:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile referee
```

Compatibility wrappers:

```text
RUN_TIER_A_VALIDATION.sh
scripts/RUN_TIER_A_VALIDATION.sh
COLAB_TIER_A_VALIDATION.py
colab/COLAB_TIER_A_VALIDATION.py
```

These wrappers should delegate to `cosmology/scripts/run_tiera1_lateonly_suite.py` or, for chain-only legacy validation, `cosmology/scripts/analyze_chains.py`. They should not maintain independent YAML-generation or direct `cobaya-run` logic.

## B. Required referee-facing documentation

The minimum documentation set is:

```text
README.md
README_SCRIPTS.md
traceability.md
docs/VALIDATION_MATRIX.md
docs/COLAB_GUIDE.md
docs/HOW_TO_REPRODUCE_TIER_A1_OUTPUTS.md
docs/TIER_A_ARTIFACT_MANIFEST.md
docs/DATA_AVAILABILITY.md
docs/GITHUB_PUBLISH_CHECKLIST.md
docs/HUBBLE_RESOLUTION_CLAIM_LADDER.md
docs/HUBBLE_CLAIM_DISCIPLINE.md
cosmology/docs/H0_LIKELIHOOD_FIX.md
```

Avoid adding more docs unless they remove ambiguity that cannot be handled in one of these existing files.

## C. Tier-A1 H0_obs configuration contract

The corrected Tier-A1 validation tests the observed-frame local-Hubble channel:

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

A stale EDCL+H0 run using direct `H0.riess2020` is a configuration failure, not a physics test of the observed-frame mechanism.

Relevant implementation files:

```text
cosmology/likelihoods/H0_edcl_func.py
cosmology/scripts/check_no_doublecount_sh0es.py
cosmology/scripts/validate_tiera1_lateonly_results.py
tests/test_h0_obs_likelihood.py
```

## D. Tier-A1 corrected workdir contract

The canonical runner should write a timestamped workdir such as:

```text
edcl_tiera1_YYYYMMDD_HHMMSS/
```

Expected contents:

```text
manifest.json
logs/
yamls/
chains/
results_summary.json
results_report.md
bundle_edcl_tiera1.zip
```

Rendered YAMLs should live under:

```text
<workdir>/yamls/
```

not under:

```text
cosmology/cobaya/
```

## E. What goes in git

Commit:

```text
source code
tests
YAML templates
CLASS patch files
small deterministic Tier-B / Track-0 artifacts, if desired
compact Tier-A1 result summaries
documentation
```

Compact Tier-A1 summaries currently expected in git:

```text
cosmology/results/tierA1_hubble_result_card.json
cosmology/results/tierA1_chain_component_audit.json
```

## F. What stays out of git

Do not commit generated heavy/runtime outputs:

```text
class_public/
cobaya_packages/
chains/
edcl_tiera1_*/
bundle_edcl_tiera1.zip
*.updated.yaml
__pycache__/
*.pyc
```

Publish heavy Tier-A1 chain/workdir artifacts as GitHub Release assets if needed for external reproducibility.

## G. Release asset recommendation

A useful release should include a compact Tier-A1 reproducibility zip, for example:

```text
tierA1_reproducibility_assets.zip
```

Suggested contents:

```text
chains/lcdm_production.1.txt
chains/edcl_production.1.txt
chains/edcl_no_h0_medium.1.txt
workdirs/<corrected-run-workdir>/
checksums/SHA256SUMS.txt
README_RELEASE_ASSETS.md
```

If original timestamped workdirs are unavailable, publish available chains plus a regenerated corrected-run workdir bundle and state that the original workdir-backed provenance remains unavailable.

## H. Claim boundary

Current safe claim:

```text
Tier-A1 supports a working H0_obs calibration-drift mechanism with activation and no-H0 best-fit/profile-collapse evidence; the strict no-H0 posterior-tail q95 collapse criterion is not passed.
```

Do not present Tier-A1 alone as:

```text
a completed Hubble-tension resolution
completed Planck compatibility
decisive model-comparison evidence
```

Stronger language requires:

```text
workdir-backed provenance
broader likelihood-sector and fair-baseline ablations beyond the archived BAO/SN checkpoint diagnostics
kernel/prior/local-anchor robustness scans
fair baselines
Tier-A2/Planck validation
documented Bayesian-evidence provenance, if evidence claims are made
```

## I. Final publication checklist

Before tagging/releasing:

```text
1. Run Tier-B.
2. Run Track-0.
3. Run tests/test_h0_obs_likelihood.py.
4. Run Tier-A1 setup-only.
5. Run Tier-A1 iterate or referee profile.
6. Confirm H0_edcl invariants in rendered YAMLs.
7. Confirm results_summary.json and results_report.md exist.
8. Confirm bundle_edcl_tiera1.zip exists.
9. Confirm heavy outputs are not committed.
10. Attach heavy chains/workdirs as Release assets.
11. Run final claim-discipline search from docs/GITHUB_PUBLISH_CHECKLIST.md.
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
