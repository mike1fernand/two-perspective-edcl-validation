# Tier-A Cosmology Validation: Current Status and Next Steps

## Executive summary

This document describes the current Tier-A1 late-only cosmology validation of the TP/EDCL Hubble mechanism.

**Current Tier-A1 achievement:** EDCL validates a working observed-frame Hubble calibration channel. The local-Hubble likelihood is applied to

```text
H0_obs = H0_theory * (1 + delta0)
delta0 = alpha_R * f_norm
f_norm = 0.7542
```

rather than directly to the theory-frame `H0`.

**Current statistical status:** the Tier-A1 result is a mechanism-activation and collapse test, not yet a decisive full Hubble-tension resolution. The current paper reports:

| Quantity | Current Tier-A1 value |
|---|---:|
| `alpha_R` with local `H0_obs` | `0.0826 ± 0.0408` |
| `delta0 = 0.7542 alpha_R` | `0.0623 ± 0.0308` |
| `H0_theory` in EDCL+H0 run | `68.80 ± 1.85` km/s/Mpc |
| `H0_obs` in EDCL+H0 run | `73.04 ± 0.95` km/s/Mpc |
| LCDM best chi2 | `1417.2453` |
| EDCL+H0 best chi2 | `1416.1826` |
| Delta chi2 vs LCDM | `-1.0627` |
| Approx. Delta AIC | `0.94` |
| Approx. Delta BIC, using N≈1715 | `6.38` |

The `N≈1715` BIC count is an approximate diagnostic, not a primary evidence statistic. Exact BIC requires an explicitly defined effective data count.

## What was fixed

### Original issue

The standard local-Hubble likelihood compares the sampled theory-frame `H0` directly to the local measurement. That does not test the EDCL mechanism, because EDCL modifies the observed quantity:

```text
H0_obs = H0_theory * (1 + delta0)
```

### Corrected likelihood

The EDCL-aware likelihood compares `H0_obs`, not `H0_theory`, to the local anchor:

```text
chi2_H0 = ((H0 * (1 + alpha_R * 0.7542) - 73.04) / 1.04)^2
logp = -0.5 * chi2_H0
```

This technical correction is central and should be preserved.

## What is validated in Tier-A1

| Test | Status | Interpretation |
|---|---|---|
| Custom likelihood applies local H0 to `H0_obs` | validated by code review and `tests/test_h0_obs_likelihood.py` | Required for a meaningful EDCL Hubble test |
| Activation with local H0 included | present | `alpha_R` is about `2.0σ` by mean/std |
| Collapse without local H0 | present | no-H0 run gives `alpha_R = 0.0147 ± 0.0142` |
| Observed-frame H0 match | present | `H0_obs = 73.04 ± 0.95` km/s/Mpc |
| Late-only fit improvement | modest | `Delta chi2 = -1.0627` with one added parameter |
| Best-fit component accounting | chain-verified for the available Tier-A1 chains | EDCL+H0_obs vs LCDM gives `Delta chi2 = -1.0627`, with H0/H0_obs = `-1.0182`, BAO = `-0.3150`, and SN = `+0.2705`; see `cosmology/results/tierA1_chain_component_audit.json` |

## What is not yet validated

The following are resolution targets, not completed Tier-A1 claims:

1. Full workdir-backed provenance for the component accounting, including exact YAML/config/log/environment reconstruction. Best-fit component accounting from the available chain columns is now recorded in `cosmology/results/tierA1_chain_component_audit.json`.
2. Likelihood ablations showing the activation is specifically driven by local `H0_obs`.
3. Kernel, prior, and local-anchor robustness scans.
4. Fair baselines against `wCDM`, `w0waCDM`, and generic calibration offsets.
5. Full Tier-A2 Planck likelihood validation.
6. Bayesian evidence with documented nested-sampler provenance.

## Claim ladder

Use `docs/HUBBLE_RESOLUTION_CLAIM_LADDER.md` as the canonical wording guide.

Current allowed wording:

> Tier-A1 validates a working `H0_obs` calibration-drift mechanism and activation/collapse behavior in late-only data.

Do not use as a completed Tier-A1 claim:

> EDCL decisively resolves the Hubble tension.

That stronger wording requires the later claim-ladder steps.

## How to reproduce

Canonical entrypoints:

```bash
python COLAB_TIER_A_VALIDATION.py --profile referee
bash RUN_TIER_A_VALIDATION.sh
python cosmology/scripts/analyze_chains.py --chains-dir <chains_dir> --output tierA1_chain_verification.json --plot
python cosmology/scripts/validate_tiera1_lateonly_results.py --workdir <workdir> --profile referee
```

## Required artifacts

See `docs/TIER_A_ARTIFACT_MANIFEST.md`. At minimum, a referee-facing Tier-A release should include:

- LCDM late-only chains/workdir/logs;
- EDCL+`H0_obs` chains/workdir/logs;
- EDCL no-H0 chains/workdir/logs;
- YAML/config files;
- environment manifest;
- checksums;
- `cosmology/results/tierA1_hubble_result_card.json`;
- `cosmology/results/tierA1_chain_component_audit.json` for chain-verified posterior values, best-fit component accounting, formula checks, and BBN consistency contrast.

## Next validation priorities

1. Publish or locate the remaining Tier-A workdir artifacts for YAML/config/log/environment provenance.
2. Preserve `cosmology/results/tierA1_chain_component_audit.json` as the current chain-verified best-fit component accounting.
3. Maintain the lightweight `H0_obs` likelihood regression test in `tests/test_h0_obs_likelihood.py`.
4. Run likelihood ablations.
5. Run kernel/prior/local-anchor robustness scans.
6. Run Planck distance-prior preflight and then full Tier-A2.
