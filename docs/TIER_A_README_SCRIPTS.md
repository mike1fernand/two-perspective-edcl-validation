# Tier-A1 script note

This file is a short Tier-A1-specific companion to:

```text
README_SCRIPTS.md
```

Do not treat this file as a second independent script manual. The repo uses one canonical Tier-A1 execution path:

```text
cosmology/scripts/run_tiera1_lateonly_suite.py
```

Legacy entry points are compatibility wrappers only.

## Canonical Tier-A1 commands

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

Referee profile:

```bash
python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile referee
```

## Compatibility wrappers

These wrappers should delegate to the canonical Python runner and should not contain separate YAML-generation or direct `cobaya-run` logic:

```text
RUN_TIER_A_VALIDATION.sh
scripts/RUN_TIER_A_VALIDATION.sh
COLAB_TIER_A_VALIDATION.py
colab/COLAB_TIER_A_VALIDATION.py
```

## Chain-only analysis

For existing chains only:

```bash
python3 cosmology/scripts/analyze_chains.py \
  --chains-dir ./chains \
  --output tierA1_chain_verification.json \
  --plot
```

For full workdir validation:

```bash
python3 cosmology/scripts/validate_tiera1_lateonly_results.py \
  --workdir <WORKDIR> \
  --profile iterate
```

## H0_obs convention

EDCL+local-H0 runs must use the custom observed-frame likelihood:

```text
H0_edcl
```

with:

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

A stale EDCL+H0 run using direct `H0.riess2020` is a configuration failure, not a physics test.

## Corrected workdir outputs

The canonical runner writes:

```text
<workdir>/manifest.json
<workdir>/logs/
<workdir>/yamls/
<workdir>/chains/
<workdir>/results_summary.json
<workdir>/results_report.md
<workdir>/bundle_edcl_tiera1.zip
```

Rendered YAMLs should be under:

```text
<workdir>/yamls/
```

not under:

```text
cosmology/cobaya/
```

## Claim boundary

Current safe Tier-A1 wording:

```text
Tier-A1 validates a working H0_obs calibration-drift mechanism and activation/collapse behavior in late-only data.
```

Do not present Tier-A1 alone as a decisive full Hubble-tension resolution.
