# How to Reproduce Tier-A1 Outputs

This file is the compact reproduction record for the Tier-A1 late-only Hubble validation outputs used by the TP/EDCL paper and repo.

It is intentionally a documentation file, not a storage location for heavy chains, patched CLASS builds, Cobaya packages, or timestamped workdirs. Heavy run outputs should be published outside normal git history.

## Scope

This file covers the current Tier-A1 late-only validation:

```text
LCDM late-only baseline
EDCL with local observed-frame H0_obs likelihood
EDCL no-H0 control
```

Current claim boundary:

```text
Tier-A1 supports a working H0_obs calibration-drift mechanism in late-only data: alpha_R activates when the local observed-frame H0_obs likelihood is included, and the no-H0 control shifts alpha_R toward zero.
```

Do **not** use this Tier-A1 result alone to claim decisive full Hubble-tension resolution.

Do **not** claim that the current no-H0 compact summary passes the stricter pre-registered q95 collapse threshold unless a validator-backed workdir run confirms that threshold.

## Current chain-verified result artifacts

Canonical result card:

```text
cosmology/results/tierA1_hubble_result_card.json
```

Current chain audit:

```text
cosmology/results/tierA1_chain_component_audit.json
```

Current compact final summary:

```text
cosmology/paper_artifacts/final_validation_summary.json
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

## Important current limitation: templates versus production-chain provenance

The committed late-only YAML templates in:

```text
cosmology/cobaya/*.yaml.in
```

are guarded source templates for the current H0_obs configuration. They are useful for smoke/setup checks and for preventing stale direct-H0 EDCL configurations.

They should **not yet** be treated as exact rendered production YAML provenance for the compact chain summaries unless the corresponding rendered/updated YAMLs and workdir manifest are supplied.

Reason:

```text
The committed late-only templates currently fix omega_b and omega_cdm for a minimal late-only smoke/reference configuration, while the compact chain summaries report posterior means and standard deviations for omega_b and omega_cdm.
```

Therefore, current chain summaries should be described as compact chain-audit summaries, not as fully workdir-backed reproduction from the committed templates alone.

A full referee-grade reproduction still requires:

```text
the original or regenerated rendered YAMLs
Cobaya updated YAMLs
workdir manifest
CLASS/Cobaya logs
environment metadata
validator report
chain hashes tied to exact YAML hashes
```

## No-H0 control status

The current compact final summary reports:

```text
alpha_R_95upper = 0.04969474355
```

The configured q95 pass threshold in:

```text
cosmology/config/validation_config.yaml
```

is:

```text
q95(alpha_R) <= 0.03
```

Since `0.0497 > 0.03`, the current compact summary supports a **collapse tendency**, not a threshold pass under the current validation configuration.

Use wording like:

```text
The no-H0 control shifts alpha_R toward zero, supporting the interpretation that the local H0_obs channel drives activation. In the current compact chain summary, however, the q95 no-H0 value exceeds the stricter pre-registered collapse threshold, so this should be described as a collapse tendency unless a validator-backed workdir run confirms threshold passage.
```

Avoid wording that describes the current no-H0 compact summary as satisfying the pre-registered collapse criterion unless the validator-backed workdir output actually satisfies the configured threshold.

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

The chain files should be kept out of normal git history. If published, attach them as external release/archive assets rather than committing heavy runtime outputs.

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

For the no-H0 control run, the local-Hubble likelihood is removed. The no-H0 run is a control test, not the primary local-H0 fit.

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

A stale EDCL YAML using direct `H0.riess2020` should fail before MCMC interpretation.

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
  q95(alpha_R) = 0.0496947

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
clean/reject __pycache__ and .pyc artifacts
scan for known failure patterns
YAML guardrails for EDCL/LCDM separation and numeric traps
local-H0 / SH0ES double-count guard by name/config scan
Python compilation in memory
deterministic unit tests without external datasets
```

The local-H0 / SH0ES scan is a guardrail. It cannot prove PantheonPlus is unanchored unless SH0ES markers appear in config strings.

## What still requires timestamped workdirs

The chain files and audit JSON verify the numerical posterior and best-fit component accounting. They do not fully reconstruct the run provenance.

For full referee-grade provenance, preserve or publish timestamped workdirs produced by the corrected runner.

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
validator report
bundle zip
```

Do not commit these workdirs into normal git history.

## Current limitations

The current Tier-A1 validation is not yet enough for stronger Hubble-resolution claims. Stronger language still requires:

```text
workdir-backed provenance
likelihood ablations
kernel/prior/local-anchor robustness scans
fair baselines
Tier-A2/Planck validation
```

Additional unresolved provenance notes:

```text
PantheonPlus no-embedded-SH0ES/local-H0 evidence is not yet filled in cosmology/data_provenance/pantheonplus_note.md.
The committed smoke/reference templates should not be treated as exact production-chain provenance for the compact chain summaries.
```

## Safe current wording

```text
Tier-A1 verifies an observed-frame H0_obs calibration channel: alpha_R activates under the local H0_obs likelihood, and the no-H0 control shifts alpha_R toward zero. In this chain set, however, q95(alpha_R) for the no-H0 control exceeds the stricter configured collapse threshold, so the no-H0 result should be described as a collapse tendency unless a validator-backed workdir run confirms threshold passage. The total best-fit improvement over LCDM is modest and comes primarily from the H0/H0_obs term, with small BAO/SN reallocations.
```
