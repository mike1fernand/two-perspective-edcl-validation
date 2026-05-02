# GitHub publish checklist (referee-ready)

This checklist is optimized for:

```text
easy audit by reviewers
minimal risk of "it works only on my machine"
keeping large artifacts accessible without bloating git history
preserving the corrected Tier-A1 H0_obs / H0_edcl provenance
```

## 1. Repository contents to commit

Commit source-controlled materials:

```text
tierB/
track0/
cosmology/
scripts/
tests/
README.md
docs/
traceability.md
TIER_A_COMPLETE_DOCUMENTATION.md
requirements.txt
LICENSE
```

Commit compact Tier-A1 result summaries:

```text
cosmology/results/tierA1_hubble_result_card.json
cosmology/results/tierA1_chain_component_audit.json
```

Commit the corrected Tier-A1 reproducibility files:

```text
cosmology/patches/class_edcl.patch
cosmology/cobaya/edcl_cosmo_lateonly.yaml.in
cosmology/cobaya/edcl_cosmo_full.yaml.in
cosmology/scripts/run_tiera1_lateonly_suite.py
cosmology/scripts/render_yamls.py
cosmology/scripts/check_no_doublecount_sh0es.py
cosmology/scripts/validate_tiera1_lateonly_results.py
cosmology/likelihoods/H0_edcl_func.py
RUN_TIER_A_VALIDATION.sh
```

## 2. Files and folders not to commit

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

These should be local-only or published as GitHub Release assets.

## 3. Run lightweight checks before tagging

Run fast checks:

```bash
python -m pip install -r requirements.txt
python scripts/run_all_tierB.py
python track0/run_track0_kernel_consistency.py
python tests/test_h0_obs_likelihood.py
```

If available, run the lint/package gate.

## 4. Run Tier-A1 setup-only check

Before creating a release, run the corrected setup-only Tier-A1 path in a Linux/Colab/WSL-style environment:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py \
  --profile iterate \
  --skip-mcmc \
  --no-validate
```

This should verify:

```text
CLASS clone/tag selection
EDCL patch application
CLASS/classy build
EDCL smoke/preflight checks
YAML rendering into <workdir>/yamls/
H0-likelihood invariant checks
Cobaya install/test initialization
manifest and bundle creation
```

## 5. Run Tier-A1 iterate or referee profile

After setup-only succeeds, run an end-to-end MCMC profile:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile iterate
```

For a stricter release-quality run:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile referee
```

The root wrapper may also be used:

```bash
bash RUN_TIER_A_VALIDATION.sh
```

## 6. Verify H0_obs / H0_edcl evidence before release

The release should contain evidence that these invariants were checked:

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

Relevant files/logs:

```text
<workdir>/yamls/
<workdir>/logs/
<workdir>/results_summary.json
<workdir>/results_report.md
cosmology/scripts/check_no_doublecount_sh0es.py
cosmology/scripts/validate_tiera1_lateonly_results.py
```

A stale EDCL+H0 run using direct `H0.riess2020` should be treated as a configuration failure, not as a physics test.

## 7. Create a tagged release for the paper

Recommended flow:

```text
1. Push the cleaned code to GitHub.
2. Create an annotated tag, for example paper-v1.0.0.
3. Create a GitHub Release from that tag.
4. Upload heavy Tier-A1 artifacts as Release assets.
5. Record checksums for every heavy artifact.
```

## 8. Release assets to upload

A complete Tier-A1 Release should include a compact reproducibility zip, for example:

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

A corrected-run workdir should contain:

```text
manifest.json
logs/
yamls/
chains/
results_summary.json
results_report.md
bundle_edcl_tiera1.zip
```

If older timestamped workdirs are unavailable, publish the available chains plus a regenerated corrected-run workdir bundle and clearly state that original workdir-backed provenance remains unavailable.

## 9. Record provenance in the paper

The LaTeX source may define macros such as:

```text
\TPReproURL
\TPReproCommit
\TPReproZenodo
```

Update these to match:

```text
GitHub repo URL
exact release tag or commit hash
optional Zenodo DOI, if minted
```

## 10. Optional Zenodo archival

For journals with strict data-availability requirements:

```text
connect the GitHub repo to Zenodo
mint a DOI for the paper release
cite the DOI in the paper
```

## 11. Optional lightweight CI

If GitHub Actions are enabled, keep CI lightweight:

```text
run Tier-B unit/smoke checks
run Track-0 check
run tests/test_h0_obs_likelihood.py
run static/lint checks for YAML templates and scripts
run Tier-A validator against archived chain/workdir assets if available
do not run heavy MCMC in CI
```

## 12. Final claim-discipline check

Before publishing, search for disallowed overclaiming:

```bash
grep -R "decisively resolves\|successfully resolves the Hubble tension\|3.9 sigma\|3.9σ\|Full CMB validation is complete" .
```

Current safe Tier-A1 wording:

```text
Tier-A1 validates a working H0_obs calibration-drift mechanism and activation/collapse behavior in late-only data.
```

Do not present Tier-A1 alone as a decisive full Hubble-tension resolution.
