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
- convergence diagnostics;
- environment manifest;
- code commit SHA;
- checksums.

## Current status

At the time this document was added, the public GitHub releases page did not contain the large Tier-A chain/workdir assets. Exact per-likelihood chi2 decomposition should therefore be treated as blocked unless those artifacts are located locally, regenerated, or published.

## Why this matters

The cleaned manuscript treats the Tier-A1 result as a mechanism-activation/collapse test. To move toward stronger Hubble-resolution language, the next required validation layer is exact likelihood-component accounting:

```text
chi2_total = chi2_BAO + chi2_SN + chi2_H0obs
```

This must be extracted from production-chain likelihood components or clearly labeled as emulator-derived if reconstructed from public data.
