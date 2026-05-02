"""
Observed-frame local-Hubble likelihood for the EDCL Tier-A1 validation.

This module is the canonical Python helper for the EDCL local-H0 likelihood used
by Cobaya external-likelihood YAMLs and by the lightweight regression tests.

The correction being protected is:

    delta0 = alpha_R * F_NORM
    H0_obs = H0_theory * (1 + delta0)

The local Riess anchor is then applied to H0_obs, not directly to the sampled
theory-frame H0.

Cobaya YAML key convention:
    H0_edcl

Current constants:
    H0_MEAN = 73.04
    H0_STD  = 1.04
    F_NORM  = 0.7542
"""

from __future__ import annotations

from numbers import Real


# Riess local-Hubble anchor used by the Tier-A1 EDCL H0_obs likelihood.
H0_MEAN = 73.04
H0_STD = 1.04

# Phase-1 mean-field normalization used for delta0 = alpha_R * F_NORM.
F_NORM = 0.7542


def _as_float(name: str, value: Real) -> float:
    """Convert scalar numeric inputs to float with a clear error on failure."""
    try:
        return float(value)
    except Exception as exc:
        raise TypeError(f"{name} must be a scalar numeric value, got {value!r}") from exc


def edcl_delta0(alpha_R: Real, f_norm: Real = F_NORM) -> float:
    """Return the EDCL calibration drift delta0 = alpha_R * f_norm."""
    alpha = _as_float("alpha_R", alpha_R)
    norm = _as_float("f_norm", f_norm)
    return alpha * norm


def edcl_H0_obs(H0: Real, alpha_R: Real, f_norm: Real = F_NORM) -> float:
    """Return observed-frame H0_obs = H0 * (1 + alpha_R * f_norm)."""
    h0_theory = _as_float("H0", H0)
    return h0_theory * (1.0 + edcl_delta0(alpha_R, f_norm))


def H0_edcl_chi2(H0: Real, alpha_R: Real) -> float:
    """Return chi2 for the EDCL observed-frame local-Hubble likelihood."""
    h0_obs = edcl_H0_obs(H0, alpha_R)
    return ((h0_obs - H0_MEAN) / H0_STD) ** 2


def H0_edcl_logp(H0: Real, alpha_R: Real) -> float:
    """Return log-likelihood for the EDCL observed-frame local-Hubble anchor.

    Parameters
    ----------
    H0
        Theory-frame H0 sampled by CLASS/Cobaya before EDCL calibration.
    alpha_R
        EDCL amplitude parameter.

    Returns
    -------
    float
        logp = -0.5 * ((H0_obs - H0_MEAN) / H0_STD)^2
    """
    return float(-0.5 * H0_edcl_chi2(H0, alpha_R))


__all__ = [
    "H0_MEAN",
    "H0_STD",
    "F_NORM",
    "edcl_delta0",
    "edcl_H0_obs",
    "H0_edcl_chi2",
    "H0_edcl_logp",
]
