# Two-Perspective validation suite

This repository contains validation and reproducibility code for the simulations used in the Two-Perspective / EDCL paper.

The suite is organized into three tiers:

```text
Tier-B   pure-Python formalism/kinematics validations
Track-0  pure-Python kernel/consistency checks
Tier-A1  CLASS + Cobaya late-only cosmology validation
```

If you are a reviewer, start with:

```text
docs/VALIDATION_MATRIX.md
docs/COLAB_GUIDE.md
docs/HOW_TO_REPRODUCE_TIER_A1_OUTPUTS.md
traceability.md
```

## Repository structure

```text
tierB/                         Tier-B simulation modules
scripts/run_all_tierB.py        one-command Tier-B runner
track0/                         Track-0 kernel checks
cosmology/                      Tier-A1 cosmology code, CLASS patch, Cobaya templates, validators
cosmology/patches/              EDCL CLASS patch
cosmology/scripts/              Tier-A1 runners, guards, validators
cosmology/cobaya/               Cobaya YAML templates
docs/                           reviewer-facing documentation
traceability.md                 condensed claim-to-evidence ledger
```

Large Tier-A1 outputs such as chains, timestamped workdirs, patched CLASS builds, and Cobaya package folders should not be committed to normal git history. Publish heavy reproducibility artifacts as GitHub Release assets when needed.

## Quickstart: Tier-B + Track-0

These checks do not require CLASS or Cobaya.

```bash
python -m pip install -r requirements.txt
python scripts/run_all_tierB.py
python track0/run_track0_kernel_consistency.py
```

Typical outputs:

```text
paper_artifacts/*.png
paper_artifacts/*.txt
paper_artifacts/track0/fig_kernel_consistency.png
```

## Tier-A1 late-only cosmology validation

Tier-A1 requires a Linux/Colab/WSL-style environment because it builds CLASS/classy and uses Cobaya likelihood data.

The canonical Tier-A1 runner is:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile iterate
```

The root shell wrapper delegates to the same runner:

```bash
bash RUN_TIER_A_VALIDATION.sh
```

For Google Colab, use:

```text
docs/COLAB_GUIDE.md
```

### Setup-only check before MCMC

Before running chains, verify the patch/build/render/guard path:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py \
  --profile iterate \
  --skip-mcmc \
  --no-validate
```

This should:

```text
clone upstream CLASS
apply cosmology/patches/class_edcl.patch
build CLASS/classy
run EDCL smoke/preflight checks
render Tier-A1 YAMLs into the workdir
check H0-likelihood invariants
run Cobaya initialization tests
create a bundle
```

### Full iterate run

After the setup-only check succeeds:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile iterate
```

### Referee-grade run

After the iterate run is clean and interpretable:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile referee
```

The referee profile is stricter and may take substantially longer.

## Tier-A1 H0-likelihood convention

The current Tier-A1 mechanism test enforces the observed-frame H0 convention:

```text
EDCL + local H0 must use H0_edcl
EDCL + local H0 must not use H0.riess2020
EDCL no-H0 must contain no local-H0 likelihood
LCDM may use direct H0.riess2020
```

The relevant guard and validator are:

```text
cosmology/scripts/check_no_doublecount_sh0es.py
cosmology/scripts/validate_tiera1_lateonly_results.py
```

The corrected EDCL local-H0 likelihood compares:

```text
H0_obs = H0 * (1 + alpha_R * 0.7542)
```

against the local Riess value through `H0_edcl`.

## Re-validating an existing Tier-A1 workdir

Use the validator on a workdir created by the suite runner:

```bash
python3 cosmology/scripts/validate_tiera1_lateonly_results.py \
  --workdir <WORKDIR> \
  --profile iterate
```

For referee mode:

```bash
python3 cosmology/scripts/validate_tiera1_lateonly_results.py \
  --workdir <WORKDIR> \
  --profile referee
```

The validator writes:

```text
<WORKDIR>/results_summary.json
<WORKDIR>/results_report.md
```

## Analyzing existing chain files directly

For standalone chain analysis, use `--chains-dir`:

```bash
python3 cosmology/scripts/analyze_chains.py \
  --chains-dir <CHAINS_DIR> \
  --output <OUTPUT_JSON> \
  --plot
```

This is separate from the workdir-level Tier-A1 validator.

## What not to commit

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

If chain/workdir artifacts are needed for external reproducibility, attach them to a GitHub Release and document the hashes.

## Key documentation

```text
docs/VALIDATION_MATRIX.md
docs/COLAB_GUIDE.md
docs/HOW_TO_REPRODUCE_TIER_A1_OUTPUTS.md
docs/DATA_AVAILABILITY.md
TIER_A_COMPLETE_DOCUMENTATION.md
cosmology/docs/H0_LIKELIHOOD_FIX.md
traceability.md
```

## Claim boundary

Tier-A1 supports a working `H0_obs` calibration-drift mechanism in late-only data: `alpha_R` activates when the local observed-frame `H0_obs` likelihood is included, and the no-H0 control shifts `alpha_R` toward zero. The old compact no-H0 unweighted row quantile `q95(alpha_R)=0.0497` is superseded for current claim wording. Current weighted diagnostics give sampled-density no-H0 `q95(alpha_R)=0.0470`, fixed-density no-H0 `q95(alpha_R)=0.0341`, and same-model P1/P2 fixed-density no-H0 `q95(alpha_R)=0.033860544`; all exceed the configured `q95<=0.03` posterior-tail threshold, so the no-H0 result supports profile-level collapse/collapse tendency rather than a threshold pass.

Tier-A1 alone should not be described as a completed Hubble-tension resolution. Stronger claims require additional provenance, broader likelihood-sector/fair-baseline robustness scans beyond the archived BAO/SN checkpoint diagnostics, and Tier-A2/Planck validation.

## License

See `LICENSE`.

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
