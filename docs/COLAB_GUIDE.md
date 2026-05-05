# Colab guide: Tier-A1 late-only validation

This guide is written so a reviewer can run the Tier-A1 late-only EDCL validation in Google Colab using the canonical suite runner:

```text
cosmology/scripts/run_tiera1_lateonly_suite.py
```

Use Colab code cells for every command below.

## What this Colab path does

The Tier-A1 suite runner is designed to:

```text
clone upstream CLASS
prefer CLASS tag v3.3.4 when available
apply cosmology/patches/class_edcl.patch
build CLASS/classy
run EDCL smoke/preflight checks
render Tier-A1 YAMLs into the run workdir
check H0-likelihood invariants before MCMC
run Cobaya install/test/run steps
validate outputs
write manifest.json
create bundle_edcl_tiera1.zip
```

The key EDCL H0 convention enforced by the current runner is:

```text
EDCL + local H0 must use H0_edcl
EDCL + local H0 must not use H0.riess2020
EDCL no-H0 must contain no local-H0 likelihood
LCDM may use direct H0.riess2020
```

## A. Start a fresh Colab runtime

In Colab, choose:

```text
Runtime -> Change runtime type -> CPU
```

GPU is not needed.

## B. Clone the repo

Run this cell:

```python
!git clone https://github.com/mike1fernand/two-perspective-edcl-validation.git
%cd two-perspective-edcl-validation
```

Verify the required files are present:

```python
!ls cosmology/patches/class_edcl.patch
!ls cosmology/scripts/run_tiera1_lateonly_suite.py
!ls cosmology/scripts/smoke_test_classy_edcl.py
!ls cosmology/scripts/check_no_doublecount_sh0es.py
!ls cosmology/scripts/validate_tiera1_lateonly_results.py
```

## C. Optional: Tier-B + Track-0 quick checks

These checks are separate from Tier-A1 MCMC:

```python
!python -m pip install -r requirements.txt
!python scripts/run_all_tierB.py
!python track0/run_track0_kernel_consistency.py
```

Artifacts may be written to:

```text
paper_artifacts/
track0/
```

## D. Tier-A1 setup-only run

Run this first before launching MCMC:

```python
!python3 cosmology/scripts/run_tiera1_lateonly_suite.py \
  --profile iterate \
  --skip-mcmc \
  --no-validate
```

This should verify the hard setup path:

```text
CLASS clone/patch/build
EDCL smoke/preflight
YAML rendering
H0-likelihood invariant checks
Cobaya install/test initialization
bundle creation
```

Do not run the full MCMC until this setup-only run succeeds.

## E. Inspect the setup-only bundle

Find the latest bundle:

```python
!find /content -name "bundle_edcl_tiera1.zip" -print
```

To inspect the generated YAMLs quickly:

```python
!WORKDIR=$(ls -td /content/edcl_tiera1_* | head -1); \
  echo "$WORKDIR"; \
  grep -R "H0_edcl\|H0.riess2020" "$WORKDIR/yamls" || true
```

Expected:

```text
lcdm_lateonly.yaml may contain H0.riess2020
edcl_cosmo_lateonly.yaml must contain H0_edcl
edcl_cosmo_lateonly.yaml must not contain H0.riess2020
edcl_cosmo_lateonly_no_sh0es.yaml must contain neither H0_edcl nor H0.riess2020
```

## F. Run the Tier-A1 iterate MCMC

After the setup-only run succeeds, run:

```python
!python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile iterate
```

This is the first full end-to-end MCMC run. It is intended for iteration/debugging, not final referee-grade production.

## G. Optional referee-grade run

Only after the iterate run is clean and interpretable, run:

```python
!python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile referee
```

The referee profile is stricter and may take substantially longer.

## H. Download the output bundle

Find and download the newest bundle:

```python
from google.colab import files

paths = !find /content -name "bundle_edcl_tiera1.zip" -print
paths = [p for p in paths if p.strip()]
print("\n".join(paths))

bundle = paths[-1]
print("Downloading:", bundle)
files.download(bundle)
```

The bundle should include:

```text
manifest.json
logs/
yamls/
chains/
results_summary.json
results_report.md
bundle_edcl_tiera1.zip
```

## I. If the run fails

The runner should still create a bundle when possible. Download the bundle and inspect:

```text
logs/
manifest.json
results_report.md
results_summary.json
yamls/
```

If no bundle is available, package the latest run directory manually:

```python
!WORKDIR=$(ls -td /content/edcl_tiera1_* | head -1); \
  echo "$WORKDIR"; \
  zip -r /content/tiera1_failure_artifacts.zip \
    "$WORKDIR/logs" \
    "$WORKDIR/yamls" \
    "$WORKDIR/manifest.json" \
    "$WORKDIR/results_report.md" \
    "$WORKDIR/results_summary.json" || true
```

Then download:

```python
from google.colab import files
files.download("/content/tiera1_failure_artifacts.zip")
```

## J. Re-validate an existing workdir

If you already have a workdir in the current Colab session:

```python
!python3 cosmology/scripts/validate_tiera1_lateonly_results.py \
  --workdir /content/edcl_tiera1_YYYYMMDD_HHMMSS \
  --profile iterate
```

For referee mode:

```python
!python3 cosmology/scripts/validate_tiera1_lateonly_results.py \
  --workdir /content/edcl_tiera1_YYYYMMDD_HHMMSS \
  --profile referee
```

## K. Do not commit generated outputs

Do not commit generated Colab artifacts to normal git history:

```text
class_public/
cobaya_packages/
chains/
edcl_tiera1_*/
bundle_edcl_tiera1.zip
*.updated.yaml
```

Heavy reproducibility artifacts should be kept locally or attached to a GitHub Release.

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

## NOH0 Colab checkpoint notebook

Commit and use `colab/NOH0_CLEAN_COLAB_BAO_SN_ABLATIONS_ENHANCED_v3_HOTFIX.ipynb` for the checkpointed BAO/SN ablation and same-model P1/P2 no-H0 repeat workflow. Run Cells 1--10 for BAO/SN diagnostics, inspect/upload the checkpoint ZIP, and run Cell 11 only for the same-model P1/P2 repeat after the diagnostic outputs are understood. The notebook is a reproducibility aid; the canonical repo script is `cosmology/scripts/noh0_checkpointed_diagnostics.py`.
