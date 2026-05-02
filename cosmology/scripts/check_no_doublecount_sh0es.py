#!/usr/bin/env python3
"""check_no_doublecount_sh0es.py

Referee-facing guardrail for Tier-A/Tier-A1 H0 likelihood usage.

This script has two jobs:

1. Preserve the original conservative SH0ES/H0 double-counting check:
   if a direct local-H0 likelihood is present, fail if another likelihood key
   or likelihood option appears to contain SH0ES-embedded information.

2. Enforce the EDCL observed-frame H0 convention:
   - LCDM may use a direct local-H0 likelihood such as H0.riess2020.
   - EDCL + local-H0 must use the custom H0_edcl likelihood.
   - EDCL must not use a direct H0.riess2020/sh0es-style likelihood.
   - EDCL no-H0 configs may use no local-H0 likelihood at all.

Usage:
  python3 check_no_doublecount_sh0es.py path/to/config.yaml
"""

from __future__ import annotations

import sys
from typing import Any, Dict, List, Sequence, Tuple

import yaml


DIRECT_H0_EXAMPLES = "H0.riess2020 / sh0es.*"
CUSTOM_EDCL_H0_KEY = "H0_edcl"


def _contains(obj: Any, sub: str) -> bool:
    """Recursively search string values and dictionary keys for a substring."""
    sub = sub.lower()
    if isinstance(obj, str):
        return sub in obj.lower()
    if isinstance(obj, dict):
        return any(sub in str(k).lower() or _contains(v, sub) for k, v in obj.items())
    if isinstance(obj, (list, tuple)):
        return any(_contains(v, sub) for v in obj)
    return False


def _truthy_edcl_on(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"yes", "true", "1", "on"}
    return False


def _is_edcl_enabled(cfg: Dict[str, Any]) -> bool:
    theory = cfg.get("theory", {})
    if not isinstance(theory, dict):
        return False

    classy = theory.get("classy", {})
    if not isinstance(classy, dict):
        return False

    extra_args = classy.get("extra_args", {})
    if not isinstance(extra_args, dict):
        return False

    return _truthy_edcl_on(extra_args.get("edcl_on", False))


def _is_direct_h0_key(key: str) -> bool:
    """Direct local-H0/SH0ES likelihood keys, not the EDCL observed-frame wrapper."""
    kl = key.strip().lower()
    if kl.startswith("h0."):
        return True
    if kl == "sh0es" or kl.startswith("sh0es."):
        return True
    return False


def _is_edcl_h0_key(key: str) -> bool:
    return key.strip().lower() == CUSTOM_EDCL_H0_KEY.lower()


def _find_sh0es_offenders(
    likelihood: Dict[str, Any],
    exclude_keys: Sequence[str],
) -> List[Tuple[str, str]]:
    offenders: List[Tuple[str, str]] = []
    excluded = set(exclude_keys)

    for key, value in likelihood.items():
        if key in excluded:
            continue
        key_l = str(key).lower()
        if "sh0es" in key_l:
            offenders.append((str(key), "likelihood key contains 'sh0es'"))
            continue
        if _contains(value, "sh0es"):
            offenders.append((str(key), "likelihood options contain 'sh0es'"))

    return offenders


def _print_likelihood_keys(keys: Sequence[str]) -> None:
    print("Likelihood keys:")
    for key in keys:
        print(" -", key)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 check_no_doublecount_sh0es.py <cobaya_yaml>")
        return 2

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if not isinstance(cfg, dict):
        print("[FAIL] YAML root is not a dictionary.")
        return 2

    likelihood = cfg.get("likelihood", {})
    if not isinstance(likelihood, dict) or not likelihood:
        print("[FAIL] No likelihood dictionary found in YAML.")
        return 2

    keys = [str(k) for k in likelihood.keys()]
    direct_h0_keys = [k for k in keys if _is_direct_h0_key(k)]
    edcl_h0_keys = [k for k in keys if _is_edcl_h0_key(k)]
    edcl_enabled = _is_edcl_enabled(cfg)

    # Universal duplicate-H0 check.
    all_local_h0_keys = direct_h0_keys + edcl_h0_keys
    if len(all_local_h0_keys) >= 2:
        print("[FAIL] Multiple local-H0 likelihoods present (likely double counting):")
        for key in all_local_h0_keys:
            print(" -", key)
        print("Use exactly one local-H0 likelihood, or none for no-H0 control runs.")
        return 2

    if edcl_enabled:
        # EDCL must never use a direct H0 likelihood. The local-H0 anchor must be
        # applied to H0_obs = H0 * (1 + alpha_R * 0.7542) through H0_edcl.
        if direct_h0_keys:
            print("[FAIL] EDCL config uses a direct local-H0 likelihood.")
            print("Direct local-H0 key(s):")
            for key in direct_h0_keys:
                print(" -", key)
            print("EDCL + local-H0 runs must use H0_edcl instead, so the anchor is applied to H0_obs.")
            print("Expected custom key:", CUSTOM_EDCL_H0_KEY)
            return 2

        # EDCL + H0_edcl is allowed, but still guard against a SH0ES-embedded SN
        # likelihood or other hidden SH0ES marker in additional likelihoods.
        if edcl_h0_keys:
            offenders = _find_sh0es_offenders(likelihood, exclude_keys=edcl_h0_keys)
            if offenders:
                print("[FAIL] Potential SH0ES/H0 double-counting detected in EDCL H0_obs run.")
                print("Custom EDCL H0 likelihood:", edcl_h0_keys[0])
                print("Other likelihood(s) appear SH0ES-embedded:")
                for key, why in offenders:
                    print(f" - {key} ({why})")
                print("Use an unanchored SN likelihood when also using H0_edcl.")
                return 2

            print("[PASS] EDCL observed-frame H0 convention satisfied.")
            _print_likelihood_keys(keys)
            print("Mode: EDCL + custom H0_edcl likelihood.")
            print("Note: this scan cannot prove SN is unanchored unless SH0ES markers appear in config strings.")
            return 0

        # EDCL no-H0 control: no direct H0 and no H0_edcl. This is allowed.
        offenders = _find_sh0es_offenders(likelihood, exclude_keys=[])
        if offenders:
            print("[FAIL] EDCL no-H0 config appears to contain SH0ES markers.")
            for key, why in offenders:
                print(f" - {key} ({why})")
            print("No-H0 collapse/control runs must contain no local-H0/SH0ES likelihood information.")
            return 2

        print("[PASS] EDCL no-H0 convention satisfied.")
        _print_likelihood_keys(keys)
        print("Mode: EDCL with no local-H0 likelihood.")
        return 0

    # LCDM/non-EDCL path.
    if edcl_h0_keys:
        print("[FAIL] Non-EDCL config uses H0_edcl.")
        print("H0_edcl requires EDCL alpha_R and the observed-frame H0_obs mapping.")
        print("For LCDM + local-H0, use a direct local-H0 likelihood such as", DIRECT_H0_EXAMPLES)
        return 2

    if len(direct_h0_keys) >= 2:
        print("[FAIL] Multiple direct H0/SH0ES likelihoods present (likely double counting):")
        for key in direct_h0_keys:
            print(" -", key)
        return 2

    if direct_h0_keys:
        offenders = _find_sh0es_offenders(likelihood, exclude_keys=direct_h0_keys)
        if offenders:
            print("[FAIL] Potential SH0ES/H0 double-counting detected.")
            print("Explicit H0 likelihood:", direct_h0_keys[0])
            print("Other likelihood(s) appear SH0ES-embedded:")
            for key, why in offenders:
                print(f" - {key} ({why})")
            print("Action:")
            print(" - Use an unanchored SN likelihood when also using an explicit H0 likelihood, OR")
            print(" - Remove the explicit H0 likelihood if SN is already SH0ES-anchored.")
            return 2

        print("[PASS] No obvious SH0ES/H0 double-counting detected by name/config scan.")
        _print_likelihood_keys(keys)
        print("Mode: non-EDCL + direct local-H0 likelihood.")
        print("Note: this scan cannot prove SN is unanchored unless SH0ES markers appear in config strings.")
        return 0

    offenders = _find_sh0es_offenders(likelihood, exclude_keys=[])
    if offenders:
        print("[WARN] No explicit H0 likelihood found, but SH0ES markers appear in likelihood config.")
        for key, why in offenders:
            print(f" - {key} ({why})")
        print("This is not double-counting by itself, but verify this is intentional.")

    print("[PASS] No explicit local-H0 likelihood found.")
    _print_likelihood_keys(keys)
    print("Mode: non-EDCL with no local-H0 likelihood.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
