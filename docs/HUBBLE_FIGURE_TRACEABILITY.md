# Hubble Figure Traceability

This document records the provenance bridge for the Hubble-ratio / Hubble-drift figure used in the manuscript.

## Manuscript figure

The cleaned manuscript/package uses:

```text
figures/hubble_drift_phase1.png
```

## Repository generation script

The repository script is:

```text
cosmology/scripts/make_fig_hubble_ratio_from_class.py
```

The script's default output path is currently:

```text
cosmology/paper_artifacts/fig_hubble_ratio_from_class.png
```

## Required provenance bridge

When producing the manuscript asset, document the copy/rename step explicitly:

```text
cosmology/paper_artifacts/fig_hubble_ratio_from_class.png
→ figures/hubble_drift_phase1.png
```

If the script is updated in the future to write directly to the manuscript asset path, update this document and `docs/VALIDATION_MATRIX.md`.

## Validation status

The figure supports the Phase-1 background/high-redshift-safety diagnostic. It should not be used by itself as evidence for decisive Hubble-tension resolution. Stronger resolution claims require exact likelihood decomposition, robustness scans, fair baselines, and Tier-A2/Planck validation as described in `docs/HUBBLE_RESOLUTION_CLAIM_LADDER.md`.
