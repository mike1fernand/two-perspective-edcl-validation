#!/usr/bin/env python3
"""Regression tests for the EDCL observed-frame local-Hubble likelihood.

These tests protect the central Tier-A1 Hubble validation fix: the local H0
anchor must be applied to

    H0_obs = H0_theory * (1 + alpha_R * 0.7542)

not directly to the sampled theory-frame H0.

The test also verifies that the canonical helper file and YAML templates remain
aligned with the corrected H0_edcl convention.
"""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path
from types import ModuleType


F_NORM = 0.7542
RIESS_H0 = 73.04
RIESS_SIGMA = 1.04
EXPECTED_H0_OBS = 67.74 * (1.0 + 0.118 * F_NORM)

REPO_ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = REPO_ROOT / "cosmology" / "likelihoods" / "H0_edcl_func.py"

EDCL_H0_TEMPLATES = [
    REPO_ROOT / "cosmology" / "cobaya" / "edcl_cosmo_lateonly.yaml.in",
    REPO_ROOT / "cosmology" / "cobaya" / "edcl_cosmo_full.yaml.in",
]

EDCL_NO_H0_TEMPLATES = [
    REPO_ROOT / "cosmology" / "cobaya" / "edcl_cosmo_lateonly_no_sh0es.yaml.in",
    REPO_ROOT / "cosmology" / "cobaya" / "edcl_cosmo_no_sh0es.yaml.in",
]


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


def load_h0_edcl_helper() -> ModuleType:
    """Load the canonical helper module without requiring package imports."""
    if not HELPER_PATH.exists():
        raise AssertionError(f"Canonical H0_edcl helper not found: {HELPER_PATH}")

    spec = importlib.util.spec_from_file_location("H0_edcl_func", HELPER_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load import spec for {HELPER_PATH}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_text_required(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"Required file not found: {path}")
    return path.read_text(encoding="utf-8")


def test_h0_obs_formula() -> None:
    value = h0_obs(67.74, 0.118)
    assert_close(value, EXPECTED_H0_OBS, tol=1e-10)


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
    assert_close(once, EXPECTED_H0_OBS, tol=1e-10)


def test_canonical_helper_constants_match_regression_constants() -> None:
    helper = load_h0_edcl_helper()

    assert_close(float(helper.F_NORM), F_NORM)
    assert_close(float(helper.H0_MEAN), RIESS_H0)
    assert_close(float(helper.H0_STD), RIESS_SIGMA)


def test_canonical_helper_logp_matches_custom_h0obs_formula() -> None:
    helper = load_h0_edcl_helper()

    h0_theory = 67.74
    alpha_R = 0.118
    expected_logp = -0.5 * chi2_custom_h0obs(h0_theory, alpha_R)
    actual_logp = float(helper.H0_edcl_logp(h0_theory, alpha_R))

    assert_close(actual_logp, expected_logp, tol=1e-12)


def test_canonical_helper_penalizes_theory_frame_h0_less_than_standard_likelihood() -> None:
    helper = load_h0_edcl_helper()

    h0_theory = 67.74
    alpha_R = 0.118
    standard_logp = -0.5 * chi2_standard_h0(h0_theory)
    custom_logp = float(helper.H0_edcl_logp(h0_theory, alpha_R))

    # The corrected observed-frame likelihood should be much less punitive for
    # this EDCL-corrected point than the stale direct-H0 likelihood.
    assert custom_logp > standard_logp + 10.0, (custom_logp, standard_logp)


def test_edcl_h0_templates_use_h0_edcl_not_direct_riess() -> None:
    for path in EDCL_H0_TEMPLATES:
        text = read_text_required(path)

        assert "H0_edcl" in text, f"{path} must use custom H0_edcl likelihood"
        assert "H0.riess2020" not in text, f"{path} must not use direct H0.riess2020"
        assert "H0_obs" in text, f"{path} must define derived H0_obs"
        assert "delta0" in text, f"{path} must define derived delta0"
        assert "alpha_R * 0.7542" in text or "alpha_R*0.7542" in text, (
            f"{path} must use the canonical f_norm = 0.7542 factor"
        )


def test_edcl_no_h0_templates_have_no_local_h0_likelihood() -> None:
    for path in EDCL_NO_H0_TEMPLATES:
        text = read_text_required(path)

        assert "H0_edcl" not in text, f"{path} no-H0 control must not use H0_edcl"
        assert "H0.riess2020" not in text, f"{path} no-H0 control must not use direct H0.riess2020"


def run_all_tests() -> None:
    test_h0_obs_formula()
    test_alpha_zero_recovers_theory_h0()
    test_custom_likelihood_is_small_when_calibration_active()
    test_fnorm_not_applied_twice()
    test_canonical_helper_constants_match_regression_constants()
    test_canonical_helper_logp_matches_custom_h0obs_formula()
    test_canonical_helper_penalizes_theory_frame_h0_less_than_standard_likelihood()
    test_edcl_h0_templates_use_h0_edcl_not_direct_riess()
    test_edcl_no_h0_templates_have_no_local_h0_likelihood()


if __name__ == "__main__":
    run_all_tests()
    print("All EDCL H0_obs likelihood regression tests passed.")
    print(f"H0_obs(67.74, alpha_R=0.118) = {h0_obs(67.74, 0.118):.4f} km/s/Mpc")
    print(
        "standard chi2 = "
        f"{chi2_standard_h0(67.74):.3f}; "
        "custom chi2 = "
        f"{chi2_custom_h0obs(67.74, 0.118):.3f}"
    )
