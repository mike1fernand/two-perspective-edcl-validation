# How to Reproduce Tier-A1 Outputs

This file is the compact reproduction record for the Tier-A1 late-only Hubble validation outputs used by the TP/EDCL paper and repo.

It is intentionally a documentation file, not a storage location for heavy chains, patched CLASS builds, Cobaya packages, or timestamped workdirs. Heavy run outputs should be published as GitHub Release assets, not committed into normal git history.

## Scope

This file covers the current Tier-A1 late-only validation:

```text
LCDM late-only baseline
EDCL with local observed-frame H0_obs likelihood
EDCL no-H0 collapse control
```

Current claim boundary:

```text
Tier-A1 validates a working H0_obs calibration-drift mechanism and activation/collapse behavior in late-only data.
```

Do not use this Tier-A1 result alone to claim decisive full Hubble-tension resolution.

## Current chain-verified result artifacts

Canonical result card:

```text
cosmology/results/tierA1_hubble_result_card.json
```

Current chain audit:

```text
cosmology/results/tierA1_chain_component_audit.json
```

The chain audit records:

```text
manifest-matching chain hashes
weighted posterior values
EDCL formula checks for delta0 = alpha_R * 0.7542
EDCL formula checks for H0_obs = H0 * (1 + delta0)
best-fit component accounting from chain columns
BBN consistency contrast as an external check, not as a fitted likelihood
```

## Chain files used for the current audit

The current audit was produced from these chain files:

```text
lcdm_production.1.txt
edcl_production.1.txt
edcl_no_h0_medium.1.txt
```

Expected SHA256 values from the release-assets manifest:

```text
8230ad37b61ec7d1c7d8d0d813c5cc8d54e48b344e4d201c14f736223b7730f5  chains/lcdm_production.1.txt
fc89568972ec47216fcd2804f949c556d7813329d851651cbf2eb60d897b6b0b  chains/edcl_production.1.txt
99e6b66bce01cdcdb5a91f00d1acefe4c1d10b74559212a03adb1f0f3141d0d0  chains/edcl_no_h0_medium.1.txt
```

The chain files should be kept out of normal git history. If published, attach them to a GitHub Release as assets.

## Dataset and likelihood configuration

The Tier-A1 late-only data combination is:

```text
DESI DR2 BAO
PantheonPlus
local H0_obs anchor
```

The custom EDCL local-Hubble likelihood compares the observed-frame quantity to the local anchor:

```text
H0_obs = H0_theory * (1 + delta0)
delta0 = alpha_R * 0.7542
chi2_H0_obs = ((H0_obs - 73.04) / 1.04)^2
```

The canonical helper function for this formula is:

```text
cosmology/likelihoods/H0_edcl_func.py
```

For EDCL+H0_obs runs, the local anchor must be applied to `H0_obs`, not directly to the theory-frame `H0`.

For the no-H0 collapse run, the local-Hubble likelihood is removed. The no-H0 run is a collapse/control test, not the primary local-H0 fit.

## H0-likelihood invariants

The corrected Tier-A1 path enforces these configuration rules:

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

The relevant guard and validator are:

```text
cosmology/scripts/check_no_doublecount_sh0es.py
cosmology/scripts/validate_tiera1_lateonly_results.py
```

A stale EDCL YAML using direct `H0.riess2020` should now fail before MCMC interpretation.

## Current verified headline values

From `cosmology/results/tierA1_chain_component_audit.json`:

```text
EDCL+H0_obs:
  H0_theory = 68.8029559 +/- 1.8453255 km/s/Mpc
  alpha_R   = 0.0826276 +/- 0.0408177
  delta0    = 0.0623177 +/- 0.0307847
  H0_obs    = 73.0398272 +/- 0.9512977 km/s/Mpc

EDCL no-H0:
  alpha_R   = 0.0146723 +/- 0.0141722

LCDM:
  H0        = 71.3688046 +/- 0.7169926 km/s/Mpc
```

Best-fit component accounting:

```text
EDCL+H0_obs vs LCDM:
  Delta chi2_total     = -1.0627
  Delta chi2_H0/H0_obs = -1.0182
  Delta chi2_BAO       = -0.3150
  Delta chi2_SN        = +0.2705
```

This means the current chain audit does not support the earlier rough heuristic that EDCL gains about `-2.6` in H0 while paying about `+1.5` in BAO+SN.

## Reproduction commands

### 1. Install lightweight Python dependencies

For Tier-B, Track-0, and local analysis scripts:

```bash
python -m pip install -r requirements.txt
```

Important NumPy note:

```text
At least one lint-pack run failed because the environment's NumPy did not expose np.trapezoid.
A later lint-pack run passed.
To avoid this environment-dependent failure, use a NumPy version that supports np.trapezoid, or modify Tier-B scripts to use a compatibility fallback such as np.trapz when np.trapezoid is unavailable.
```

### 2. Run Tier-A1 setup-only first

Use a Linux/Colab/WSL-style environment. The canonical runner is:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py \
  --profile iterate \
  --skip-mcmc \
  --no-validate
```

This setup-only command should:

```text
clone upstream CLASS
prefer CLASS tag v3.3.4 when available
apply cosmology/patches/class_edcl.patch
build CLASS/classy
run EDCL smoke/preflight checks
render Tier-A1 YAMLs into <workdir>/yamls/
check H0-likelihood invariants before MCMC
run Cobaya install/test initialization
write manifest.json
create bundle_edcl_tiera1.zip
```

Do not run full MCMC until the setup-only path succeeds.

### 3. Run Tier-A1 iterate MCMC

After setup-only passes:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile iterate
```

This is the first end-to-end run to inspect. It is for iteration/debugging, not the final referee-grade run.

### 4. Run Tier-A1 referee profile

After the iterate run is clean and interpretable:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile referee
```

The referee profile is stricter and may take substantially longer.

### 5. Shell wrapper

The root shell script delegates to the same Python runner:

```bash
bash RUN_TIER_A_VALIDATION.sh
```

To use an existing EDCL-patched CLASS build:

```bash
bash RUN_TIER_A_VALIDATION.sh /path/to/class_public
```

Useful wrapper environment variables:

```text
PROFILE=iterate|smoke|referee
WORK_DIR=/path/to/workdir
OUTPUT_DIR=/path/to/workdir   # legacy alias if WORK_DIR is unset
CLASS_PATH=/path/to/class_public
SKIP_APT=1
SKIP_PIP=1
SKIP_COBAYA_INSTALL=1
SKIP_MCMC=1
NO_VALIDATE=1
MCMC_MAX_SAMPLES=N
```

`COBAYA_PACKAGES_PATH` is not required by the corrected wrapper. The Python runner uses a workdir-local Cobaya packages directory.

## EDCL-patched CLASS runtime requirement

A fresh clone of this repository is not, by itself, enough to regenerate the Tier-A1 MCMC chains from scratch until the EDCL-patched CLASS/classy runtime is built.

The EDCL CLASS patch is included in this repo:

```text
cosmology/patches/class_edcl.patch
```

The suite runner is designed to clone upstream CLASS, prefer tag `v3.3.4` when available, apply the included patch, build CLASS/classy, and run smoke/preflight checks.

Plain upstream CLASS is not sufficient unless the EDCL patch has been applied, because the Tier-A1 EDCL YAMLs pass EDCL-specific parameters such as:

```text
edcl_on
kappa_tick
c4
log10_l0
edcl_kernel
edcl_zeta
edcl_ai
alpha_R
```

Before running expensive MCMC chains with an existing CLASS build, verify the runtime with:

```bash
python cosmology/scripts/smoke_test_classy_edcl.py \
  --class-path /path/to/edcl_class_public
```

Required result:

```text
Baseline compute OK.
EDCL compute OK.
```

If the smoke test fails with unknown EDCL parameters, the CLASS source is not the correct EDCL-patched runtime or the parameter names have drifted.

The remaining from-scratch reproducibility tasks are:

```text
build patched CLASS/classy from the included patch
record the exact upstream CLASS commit/tag actually used
record Python/Cobaya/GetDist versions
record the build command and platform
record successful smoke-test output
publish heavy chains/workdirs as Release assets if needed
```

## Workdir outputs from the corrected runner

The corrected runner writes generated runtime artifacts under the timestamped workdir:

```text
<workdir>/manifest.json
<workdir>/logs/
<workdir>/yamls/
<workdir>/chains/
<workdir>/results_summary.json
<workdir>/results_report.md
<workdir>/bundle_edcl_tiera1.zip
```

Rendered YAMLs are written into:

```text
<workdir>/yamls/
```

not into `cosmology/cobaya/`.

Generated workdirs, chains, bundles, patched CLASS builds, Cobaya packages, and `*.updated.yaml` files should not be committed to normal git history.

## Analyze existing chain files directly

If chain files already exist, analyze them directly with `analyze_chains.py`:

```bash
python cosmology/scripts/analyze_chains.py \
  --chains-dir <chains_dir> \
  --output tierA1_chain_verification.json \
  --plot
```

Expected production-chain names include:

```text
lcdm_production.1.txt
edcl_production.1.txt
edcl_no_h0_medium.1.txt
```

This chain-file analysis is separate from the workdir-level validator.

## Re-validate an existing workdir

Use the workdir-level validator on a suite-runner workdir:

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

## Verify the H0_obs likelihood regression test

Run:

```bash
python tests/test_h0_obs_likelihood.py
```

Expected behavior:

```text
verifies H0_obs = H0 * (1 + alpha_R * 0.7542)
verifies the local anchor is applied to H0_obs, not directly to theory-frame H0
```

## Run lint/package gate if available

The lint-pack logs provided for the current validation included these checks:

```text
1. clean/reject __pycache__ and .pyc artifacts
2. scan for known failure patterns
3. YAML guardrails for EDCL/LCDM separation and numeric traps
4. local-H0 / SH0ES double-count guard by name/config scan
5. Python compilation in memory
6. deterministic unit tests without external datasets
```

The local-H0 / SH0ES scan is a guardrail. It cannot prove PantheonPlus is unanchored unless SH0ES markers appear in config strings.

## What still requires timestamped workdirs

The chain files and audit JSON verify the numerical posterior and best-fit component accounting. They do not fully reconstruct the run provenance.

For full referee-grade provenance, preserve or publish timestamped workdirs such as:

```text
edcl_tiera1_20251221_212236/
edcl_tiera1_20251221_212444/
```

or regenerated equivalent workdirs produced by the corrected runner.

Useful workdir contents include:

```text
final rendered YAML files
Cobaya updated YAML files
Cobaya logs
CLASS/Cobaya environment information
run commands
manifest.json
checksums
lint/guard logs
bundle zip
```

Do not commit these workdirs into normal git history. Publish them as GitHub Release assets if needed.

## Minimal release-assets recommendation

A clean GitHub Release should attach one zip, for example:

```text
tierA1_reproducibility_assets.zip
```

Suggested zip contents:

```text
chains/lcdm_production.1.txt
chains/edcl_production.1.txt
chains/edcl_no_h0_medium.1.txt
workdirs/edcl_tiera1_20251221_212236/   # if available
workdirs/edcl_tiera1_20251221_212444/   # if available
logs/00_lint_pack.log
checksums/SHA256SUMS.txt
README_RELEASE_ASSETS.md
```

If the workdirs are not available, publish the chains and logs only, and keep the documentation explicit that workdir-backed provenance remains outstanding.

## Current limitations

The current Tier-A1 validation is not yet enough for stronger Hubble-resolution claims. Stronger language still requires:

```text
workdir-backed provenance
likelihood ablations
kernel/prior/local-anchor robustness scans
fair baselines
Tier-A2/Planck validation
```

## Safe current wording

```text
Tier-A1 verifies an observed-frame H0_obs calibration channel: alpha_R activates under the local H0_obs likelihood and collapses without it. In this chain set, the total best-fit improvement over LCDM is modest and comes primarily from the H0/H0_obs term, with small BAO/SN reallocations.
```
