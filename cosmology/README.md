# Cosmology reproduction harness

This folder supports the Tier-A1 cosmology reproduction workflow for the TP/EDCL paper.

Tier-A1 is the late-only CLASS + Cobaya validation layer for the observed-frame Hubble mechanism. It is heavier than the pure-Python checks because it requires:

```text
EDCL-patched CLASS/classy
Cobaya
external likelihood datasets
```

The current Tier-A1 claim boundary is:

```text
Tier-A1 supports a working H0_obs calibration-drift mechanism in late-only data: alpha_R activates when the local observed-frame H0_obs likelihood is included, and the no-H0 control shifts alpha_R toward zero. The old compact no-H0 unweighted row quantile q95(alpha_R)=0.0497 is superseded for current claim wording. Current weighted diagnostics give sampled-density no-H0 q95(alpha_R)=0.0470, fixed-density no-H0 q95(alpha_R)=0.0341, and same-model P1/P2 fixed-density no-H0 q95(alpha_R)=0.033860544; all exceed the configured q95<=0.03 posterior-tail threshold, so the no-H0 result supports profile-level collapse/collapse tendency rather than a threshold pass.
```

Do not present Tier-A1 alone as a completed Hubble-tension resolution.

## Critical conventions

### 1. CLASS EDCL toggle is a string

The EDCL CLASS patch expects string-style toggles.

Use:

```yaml
edcl_on: 'yes'
```

or:

```yaml
edcl_on: 'no'
```

Avoid booleans such as `true` / `false` in YAMLs unless the patch/parser is explicitly changed and re-tested.

### 2. Do not pass EDCL-only CLASS parameters when EDCL is off

If `edcl_on: 'no'`, do not include EDCL-only CLASS parameters such as:

```text
alpha_R
kappa_tick
c4
log10_l0
edcl_kernel
edcl_zeta
edcl_ai
```

Plain LCDM CLASS runs should not receive EDCL-only parameters.

### 3. EDCL + local H0 must use H0_edcl

For EDCL+local-H0 runs, the local anchor must be applied to the observed-frame quantity:

```text
H0_obs = H0 * (1 + alpha_R * 0.7542)
```

not directly to the sampled theory-frame `H0`.

Correct EDCL local-H0 key:

```text
H0_edcl
```

Forbidden in EDCL+local-H0 runs:

```text
H0.riess2020
```

The configuration rules are:

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

A stale EDCL+H0 YAML using direct `H0.riess2020` is a configuration failure, not a physics test of the observed-frame mechanism.

### 4. Cobaya likelihood keys are install-dependent

The late-time BAO/SN keys observed in a working Cobaya 3.6 environment are:

```text
bao.desi_dr2.desi_bao_all
sn.pantheonplus
```

For LCDM+local-H0 runs, the direct local-H0 key may be:

```text
H0.riess2020
```

For EDCL+local-H0 runs, use the custom external likelihood key:

```text
H0_edcl
```

If your install differs, do not guess. Run `cobaya-install <yaml> -p <packages_dir>` and follow Cobaya’s suggestions for external BAO/SN likelihood names.

### 5. DESI full-shape likelihood is not enabled by default

DESI full-shape likelihood keys and data requirements vary by install. Enable full-shape only if `cobaya-install` recognizes the likelihood in your environment.

## Key files

EDCL CLASS patch:

```text
cosmology/patches/class_edcl.patch
```

Tier-A1 runner:

```text
cosmology/scripts/run_tiera1_lateonly_suite.py
```

YAML renderer:

```text
cosmology/scripts/render_yamls.py
```

H0 guard and validator:

```text
cosmology/scripts/check_no_doublecount_sh0es.py
cosmology/scripts/validate_tiera1_lateonly_results.py
```

Canonical H0 formula helper:

```text
cosmology/likelihoods/H0_edcl_func.py
```

## Templates

Cobaya YAML templates live in:

```text
cosmology/cobaya/*.yaml.in
```

Late-only templates:

```text
lcdm_lateonly.yaml.in
  LCDM BAO + PantheonPlus + direct local H0.

edcl_cosmo_lateonly.yaml.in
  EDCL BAO + PantheonPlus + custom observed-frame H0_edcl.

edcl_cosmo_lateonly_no_sh0es.yaml.in
  EDCL BAO + PantheonPlus with no local-H0 likelihood.
```

Full-stack templates:

```text
lcdm_full.yaml.in
  Planck 2018 + BAO + PantheonPlus + direct local H0.

edcl_cosmo_full.yaml.in
  EDCL Planck 2018 + BAO + PantheonPlus + custom observed-frame H0_edcl.

edcl_cosmo_no_sh0es.yaml.in
  EDCL Planck 2018 + BAO + PantheonPlus with no local-H0 likelihood.
```

## Rendering YAMLs

Render templates by substituting the CLASS path and per-run output directory. The renderer requires either `--yaml-dir` for workdir-safe output or `--in-place` for explicit source-tree rendering.

Explicit legacy source-tree rendering:

```bash
python cosmology/scripts/render_yamls.py \
  --class-path /path/to/class_public \
  --out-root chains \
  --in-place
```

Preferred no-clutter workdir rendering:

```bash
python cosmology/scripts/render_yamls.py \
  --class-path /path/to/class_public \
  --out-root <workdir>/chains \
  --yaml-dir <workdir>/yamls
```

The corrected Tier-A1 runner uses the no-clutter workdir path.

## Tier-A1 automated suite runner

Use a Linux/Colab/WSL-style environment.

Setup-only check before MCMC:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py \
  --profile iterate \
  --skip-mcmc \
  --no-validate
```

Full iterate run:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile iterate
```

Referee run:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile referee
```

The root shell wrapper delegates to this same runner:

```bash
bash RUN_TIER_A_VALIDATION.sh
```

## What the runner does

The suite runner performs, in order:

```text
install dependencies unless skipped
clone CLASS
prefer CLASS tag v3.3.4 when available
apply cosmology/patches/class_edcl.patch
build CLASS/classy
run EDCL smoke/preflight checks
render late-only YAMLs into <workdir>/yamls/
check H0-likelihood invariants before MCMC
run the local-H0 / SH0ES guard
run cobaya-install from the rendered YAMLs
check updated/preferred YAMLs after Cobaya install
run cobaya-run --test
run cobaya-run MCMC unless skipped
run the Tier-A1 validator
write manifest.json
bundle logs, YAMLs, chains, and reports
```

Expected corrected workdir layout:

```text
<workdir>/manifest.json
<workdir>/logs/
<workdir>/yamls/
<workdir>/chains/
<workdir>/results_summary.json
<workdir>/results_report.md
<workdir>/bundle_edcl_tiera1.zip
```

## Validation

Validator script:

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

Outputs:

```text
<WORKDIR>/results_summary.json
<WORKDIR>/results_report.md
```

These are included in:

```text
<WORKDIR>/bundle_edcl_tiera1.zip
```

## Existing chain-file analysis

For standalone chain files, use:

```bash
python3 cosmology/scripts/analyze_chains.py \
  --chains-dir <chains_dir> \
  --output tierA1_chain_verification.json \
  --plot
```

This is separate from the workdir-level validator. The standalone analyzer uses the configured no-H0 collapse threshold `q95(alpha_R) <= 0.03`; if the no-H0 q95 exceeds that value, report the result as a collapse tendency rather than a configured-threshold collapse pass.

## Heavy outputs

Do not commit generated heavy/runtime outputs:

```text
class_public/
cobaya_packages/
chains/
edcl_tiera1_*/
bundle_edcl_tiera1.zip
*.updated.yaml
```

Publish heavy chain/workdir artifacts as GitHub Release assets if needed for external reproducibility.

## Related docs

```text
docs/COLAB_GUIDE.md
docs/HOW_TO_REPRODUCE_TIER_A1_OUTPUTS.md
docs/TIER_A_ARTIFACT_MANIFEST.md
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
