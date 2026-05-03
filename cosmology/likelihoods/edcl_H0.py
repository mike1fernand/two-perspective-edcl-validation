"""
Deprecated compatibility wrapper for the old EDCL H0 likelihood path.

Canonical implementation:
    cosmology/likelihoods/H0_edcl_func.py

Canonical Cobaya YAML key:
    H0_edcl

Canonical observed-frame formula:
    delta0 = alpha_R * F_NORM
    H0_obs = H0 * (1 + delta0)

This file exists only so old imports of cosmology/likelihoods/edcl_H0.py do
not fail immediately. Do not use this file for new Tier-A1 configurations.
Use H0_edcl_func.py and the current *.yaml.in templates instead.

Important correction:
    The old implementation mixed kappa_tick into the local-Hubble drift
    normalization. The current Tier-A1 convention is delta0 = alpha_R * F_NORM,
    with F_NORM = 0.7542. The kappa_tick field is retained below only for
    backward compatibility with old Cobaya class settings; it is not used in
    the current likelihood calculation.
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, Dict


try:
    from cobaya.likelihood import Likelihood  # type: ignore
except Exception:  # pragma: no cover - allows lightweight syntax/import tests without Cobaya
    class Likelihood:  # type: ignore
        """Fallback base class used only when Cobaya is unavailable."""
        pass


try:
    from .H0_edcl_func import (
        F_NORM,
        H0_MEAN,
        H0_STD,
        edcl_delta0,
        edcl_H0_obs,
        H0_edcl_chi2,
        H0_edcl_logp,
    )
except Exception:
    # Support direct execution/import by path when this directory is not a package.
    _THIS_DIR = Path(__file__).resolve().parent
    if str(_THIS_DIR) not in sys.path:
        sys.path.insert(0, str(_THIS_DIR))
    from H0_edcl_func import (  # type: ignore
        F_NORM,
        H0_MEAN,
        H0_STD,
        edcl_delta0,
        edcl_H0_obs,
        H0_edcl_chi2,
        H0_edcl_logp,
    )


class edcl_H0_riess2022(Likelihood):
    """Deprecated Cobaya class shim for the canonical H0_edcl likelihood.

    New YAMLs should use the external likelihood key `H0_edcl` instead of this
    class. This shim applies the current Tier-A1 formula:

        H0_obs = H0 * (1 + alpha_R * f_norm)

    with f_norm defaulting to 0.7542.
    """

    H0_mean: float = H0_MEAN
    H0_std: float = H0_STD
    f_norm: float = F_NORM

    # Deprecated field retained so old class configs that pass kappa_tick do not
    # fail during object construction. It is intentionally not used.
    kappa_tick: float = 0.08333333333333333

    def initialize(self) -> None:
        log = getattr(self, "log", None)
        if log is not None:
            log.warning(
                "cosmology/likelihoods/edcl_H0.py is deprecated; "
                "use cosmology/likelihoods/H0_edcl_func.py with YAML key H0_edcl."
            )
            log.info("EDCL H0_obs likelihood constants: H0_mean=%s, H0_std=%s, f_norm=%s",
                     self.H0_mean, self.H0_std, self.f_norm)

    def get_requirements(self) -> Dict[str, Any]:
        return {"H0": None, "alpha_R": None}

    def logp(self, **params_values: float) -> float:
        h0 = params_values.get("H0")
        if h0 is None:
            raise ValueError("H0 parameter is required for edcl_H0_riess2022.logp")

        alpha_R = params_values.get("alpha_R", 0.0)
        h0_obs = edcl_H0_obs(h0, alpha_R, self.f_norm)
        chi2 = ((h0_obs - float(self.H0_mean)) / float(self.H0_std)) ** 2
        return float(-0.5 * chi2)


class edcl_H0_riess2020(edcl_H0_riess2022):
    """Deprecated non-canonical local-H0 variant retained for old imports only."""

    H0_mean: float = 73.2
    H0_std: float = 1.3


class edcl_H0_freedman2024(edcl_H0_riess2022):
    """Deprecated non-canonical TRGB variant retained for old imports only."""

    H0_mean: float = 69.85
    H0_std: float = 1.75


__all__ = [
    "F_NORM",
    "H0_MEAN",
    "H0_STD",
    "edcl_delta0",
    "edcl_H0_obs",
    "H0_edcl_chi2",
    "H0_edcl_logp",
    "edcl_H0_riess2022",
    "edcl_H0_riess2020",
    "edcl_H0_freedman2024",
]
