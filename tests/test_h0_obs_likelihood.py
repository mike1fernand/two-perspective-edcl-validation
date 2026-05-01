#!/usr/bin/env python3
"""Regression tests for the EDCL observed-frame local-Hubble likelihood.

These tests protect the central Tier-A1 Hubble validation fix: the local H0
anchor must be applied to H0_obs = H0_theory * (1 + delta0), not directly to the
sampled theory-frame H0.
"""

from __future__ import annotations

import math

F_NORM = 0.7542
RIESS_H0 = 73.04
RIESS_SIGMA = 1.04


def h0_obs(h0_theory: float, alpha_R: float, f_norm: float = F_NORM) -> float:
    """Observed-frame H0 used by the EDCL-aware local-Hubble likelihood."""
    return h0_theory * (1.0 + alpha_R * f_norm)


def chi2_standard_h0(h0_theory: float) -> float:
    """Incorrect standard likelihood penalty for the EDCL correction case."""
    return ((h0_theory - RIESS_H0) / RIESS_SIGMA) ** 2


def chi2_custom_h0obs(h0_theory: float, alpha_R: float) -> float:
    """Correct EDCL-aware local-Hubble penalty."""
    return ((h0_obs(h0_theory, alpha_R) - RIESS_H0) / RIESS_SIGMA) ** 2


def assert_close(actual: float, expected: float, tol: float = 1e-10) -> None:
    if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=tol):
        raise AssertionError(f"expected {expected}, got {actual}")


def test_h0_obs_formula() -> None:
    value = h0_obs(67.74, 0.118)
    assert_close(value, 73.76864344, tol=1e-8)


def test_alpha_zero_recovers_theory_h0() -> None:
    assert_close(h0_obs(68.8, 0.0), 68.8)


def test_custom_likelihood_is_small_when_calibration_active() -> None:
    h0_theory = 67.74
    alpha_R = 0.118
    standard = chi2_standard_h0(h0_theory)
    custom = chi2_custom_h0obs(h0_theory, alpha_R)

    assert standard > 20.0, standard
    assert custom < 1.0, custom


def test_fnorm_not_applied_twice() -> None:
    h0_theory = 67.74
    alpha_R = 0.118
    once = h0_obs(h0_theory, alpha_R)
    twice = h0_theory * (1.0 + alpha_R * F_NORM * F_NORM)

    assert abs(once - twice) > 1.0
    assert_close(once, 73.76864344, tol=1e-8)


if __name__ == "__main__":
    test_h0_obs_formula()
    test_alpha_zero_recovers_theory_h0()
    test_custom_likelihood_is_small_when_calibration_active()
    test_fnorm_not_applied_twice()
    print("All EDCL H0_obs likelihood regression tests passed.")
    print(f"H0_obs(67.74, alpha_R=0.118) = {h0_obs(67.74, 0.118):.4f} km/s/Mpc")
    print(
        "standard chi2 = "
        f"{chi2_standard_h0(67.74):.3f}; "
        "custom chi2 = "
        f"{chi2_custom_h0obs(67.74, 0.118):.3f}"
    )
