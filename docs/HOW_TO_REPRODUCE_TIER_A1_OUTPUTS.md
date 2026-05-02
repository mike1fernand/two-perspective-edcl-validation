# How to Reproduce Tier-A1 Outputs

This file is the compact reproduction record for the Tier-A1 late-only Hubble validation outputs used by the TP/EDCL paper and repo.

It is intentionally a documentation file, not a storage location for heavy chains or timestamped workdirs. Heavy run outputs should be published as GitHub Release assets, not committed into normal git history.

## Scope

This file covers the current Tier-A1 late-only validation:

- LCDM late-only baseline
- EDCL with local observed-frame `H0_obs` likelihood
- EDCL no-H0 collapse control

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

- manifest-matching chain hashes;
- weighted posterior values;
- EDCL formula checks for `delta0 = alpha_R * 0.7542`;
- EDCL formula checks for `H0_obs = H0 * (1 + delta0)`;
- best-fit component accounting from chain columns;
- BBN consistency contrast as an external check, not as a fitted likelihood.

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

For EDCL+H0_obs runs, the local anchor must be applied to `H0_obs`, not directly to the theory-frame `H0`.

For the no-H0 collapse run, the local-Hubble likelihood is removed. The no-H0 run is a collapse/control test, not the primary local-H0 fit.

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

- At least one lint-pack run failed because the environment's NumPy did not expose `np.trapezoid`.
- A later lint-pack run passed.
- To avoid this environment-dependent failure, use a NumPy version that supports `np.trapezoid`, or modify the Tier-B scripts to use a compatibility fallback such as `np.trapz` when `np.trapezoid` is unavailable.

### 2. Run Tier-A locally

The local runner is:

```bash
bash RUN_TIER_A_VALIDATION.sh
```

or with an explicit CLASS path:

```bash
bash RUN_TIER_A_VALIDATION.sh /path/to/class_public
```

Required environment variables:

```bash
export CLASS_PATH=/path/to/class_public
export COBAYA_PACKAGES_PATH=/path/to/cobaya_packages
export OUTPUT_DIR=./chains
```

Required external packages/tools:

```text
Python 3.8+
Cobaya
GetDist, optional for analysis
CLASS with the EDCL patch compiled
Cobaya data packages for DESI DR2 BAO and PantheonPlus
```

The runner generates or renders YAML configurations, runs three MCMC chains, and then calls:

```bash
python cosmology/scripts/analyze_chains.py \
  --chains-dir "$OUTPUT_DIR" \
  --output "$OUTPUT_DIR/validation_results.json" \
  --plot
```

### 3. Analyze existing chain files

If the chain files already exist, analyze them directly:

```bash
python cosmology/scripts/analyze_chains.py \
  --chains-dir <chains_dir> \
  --output tierA1_chain_verification.json \
  --plot
```

Expected chain names include:

```text
lcdm_production.1.txt
edcl_production.1.txt
edcl_no_h0_medium.1.txt
```

### 4. Verify the H0_obs likelihood regression test

Run:

```bash
python tests/test_h0_obs_likelihood.py
```

Expected behavior:

- verifies `H0_obs = H0 * (1 + alpha_R * 0.7542)`;
- verifies the local anchor is applied to `H0_obs`, not directly to theory-frame `H0`.

### 5. Run lint/package gate if available

The lint-pack logs provided for the current validation included these checks:

```text
1. clean/reject __pycache__ and .pyc artifacts
2. scan for known failure patterns
3. YAML guardrails for EDCL/LCDM separation and numeric traps
4. SH0ES/H0 double-count guard by name/config scan
5. Python compilation in memory
6. deterministic unit tests without external datasets
```

A passing lint-pack record reported:

```text
[PASS] No __pycache__ / .pyc artifacts found.
[PASS] No known failure patterns found.
[PASS] YAML guardrails: OK
[PASS] No obvious SH0ES/H0 double-counting detected by name/config scan.
[PASS] Python compilation: OK
[PASS] Unit tests: OK
[PASS] Lint gate passed.
```

The lint-pack double-count guard reports likelihood keys by name/config scan. It cannot prove PantheonPlus is unanchored unless SH0ES markers appear in config strings, so this remains a guardrail rather than a mathematical proof.

## What still requires timestamped workdirs

The chain files and audit JSON verify the numerical posterior and best-fit component accounting. They do not fully reconstruct the run provenance.

For full referee-grade provenance, preserve or publish timestamped workdirs such as:

```text
edcl_tiera1_20251221_212236/
edcl_tiera1_20251221_212444/
```

Useful workdir contents include:

```text
final YAML/config files
Cobaya logs
CLASS/Cobaya environment information
run commands
package manifests
checksums
lint-pack logs
bundle zips
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
