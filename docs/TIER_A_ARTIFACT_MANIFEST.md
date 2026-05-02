# Tier-A Artifact Manifest

This manifest lists the artifacts needed for a referee-verifiable Tier-A1 Hubble validation.

## Required artifact groups

A complete Tier-A1 release should include these groups:

```text
release_assets/
  tierA1_lcdm_lateonly/
  tierA1_edcl_h0obs/
  tierA1_edcl_noh0/
  manifests/
  checksums/
```

## Minimum required files per run

Each run directory should include:

- final Cobaya YAML/config used for the run;
- chain files;
- chain `.paramnames` / metadata files, if produced;
- best-fit or minimum-chi2 sample record;
- Cobaya logs;
- likelihood/component chi2 outputs, if available;
- `cosmology/results/tierA1_chain_component_audit.json`, when available, for chain-verified posterior values, formula checks, and best-fit component accounting;
- convergence diagnostics;
- environment manifest;
- code commit SHA;
- checksums.

## Current status

The public GitHub releases page still needs the large Tier-A chain/workdir assets for full referee-grade provenance. However, the available manifest-matching chain files have been used to produce `cosmology/results/tierA1_chain_component_audit.json`.

That audit file verifies the Tier-A1 headline posterior values, the EDCL formula relations, and best-fit component accounting from the chain columns. Full YAML/config/log/environment provenance remains blocked until the timestamped workdir artifacts are located locally, regenerated, or published as Release assets.

## Why this matters

The cleaned manuscript treats the Tier-A1 result as a mechanism-activation/collapse test. The current chain audit supplies best-fit likelihood-component accounting for the available Tier-A1 chains:

```text
EDCL+H0_obs vs LCDM:
Delta chi2_total = -1.0627
Delta chi2_H0/H0_obs = -1.0182
Delta chi2_BAO = -0.3150
Delta chi2_SN = +0.2705
```

This accounting is chain-derived, not emulator-derived. Stronger Hubble-resolution language still requires ablations, robustness checks, fair baselines, Tier-A2/Planck validation, and workdir-backed provenance.
