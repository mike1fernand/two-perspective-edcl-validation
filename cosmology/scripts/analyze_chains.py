#!/usr/bin/env python3
"""
analyze_chains.py - Standalone analysis for EDCL Tier-A1 Cobaya chain files.

This script is intentionally a chain-file analyzer, not the canonical workdir
validator. For full workdir validation with YAML/config/log checks, use:

  python3 cosmology/scripts/validate_tiera1_lateonly_results.py --workdir <WORKDIR> --profile iterate

Current claim boundary:
  Tier-A1 is a mechanism-activation test with a no-H0 collapse-tendency control.
  Configured collapse pass requires q95(alpha_R) <= 0.03. If q95 exceeds that
  threshold, the no-H0 result must be described as a collapse tendency rather
  than a configured-threshold collapse pass.

This analyzer loads existing Cobaya chain files and computes weighted parameter
summaries, best-fit chi2/component accounting, EDCL formula checks, and
lightweight mechanism diagnostics. It must not be used by itself to claim a
decisive full Hubble-tension resolution.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np

RIESS_H0_MEAN = 73.04
RIESS_H0_STD = 1.04
EDCL_F_NORM = 0.7542
CONFIGURED_COLLAPSE_Q95_THRESHOLD = 0.03


def _open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def load_chain(path: str) -> Tuple[np.ndarray, List[str]]:
    p = Path(path)
    header: Optional[List[str]] = None
    rows: List[List[float]] = []
    with _open_text(p) as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            if s.startswith("#"):
                if header is None:
                    header = s.lstrip("#").split()
                continue
            if header is None:
                continue
            parts = s.split()
            if len(parts) != len(header):
                continue
            try:
                rows.append([float(x) for x in parts])
            except ValueError:
                continue
    if header is None:
        raise ValueError(f"No header found in chain file: {p}")
    if not rows:
        raise ValueError(f"No parseable rows found in chain file: {p}")
    return np.asarray(rows, dtype=float), header


def _get_column(chain: np.ndarray, header: List[str], name: str) -> Optional[np.ndarray]:
    if name not in header:
        return None
    return chain[:, header.index(name)]


def _weight_column(chain: np.ndarray, header: List[str]) -> np.ndarray:
    for name in ("weight", "weights"):
        col = _get_column(chain, header, name)
        if col is not None:
            return col
    return np.ones(chain.shape[0], dtype=float)


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if values.size == 0:
        return float("nan")
    order = np.argsort(values)
    xs = values[order]
    ws = weights[order]
    total = float(np.sum(ws))
    if not np.isfinite(total) or total <= 0:
        return float(np.quantile(xs, q))
    cdf = np.cumsum(ws) / total
    idx = int(np.searchsorted(cdf, q, side="left"))
    idx = max(0, min(idx, len(xs) - 1))
    return float(xs[idx])


def weighted_stats(values: np.ndarray, weights: np.ndarray) -> Dict[str, float]:
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    total = float(np.sum(weights))
    if not np.isfinite(total) or total <= 0:
        mean = float(np.mean(values))
        std = float(np.std(values))
        q05, q16, q50, q84, q95 = [float(np.quantile(values, q)) for q in (0.05, 0.16, 0.50, 0.84, 0.95)]
    else:
        mean = float(np.average(values, weights=weights))
        variance = float(np.average((values - mean) ** 2, weights=weights))
        std = math.sqrt(max(0.0, variance))
        q05 = weighted_quantile(values, weights, 0.05)
        q16 = weighted_quantile(values, weights, 0.16)
        q50 = weighted_quantile(values, weights, 0.50)
        q84 = weighted_quantile(values, weights, 0.84)
        q95 = weighted_quantile(values, weights, 0.95)
    return {"mean": mean, "std": std, "median": q50, "q05": q05, "q16": q16, "q84": q84, "q95": q95}


def _first_existing(header: List[str], names: Iterable[str]) -> Optional[str]:
    for name in names:
        if name in header:
            return name
    return None


def select_unique_chi2_components(header: List[str]) -> List[str]:
    cols = [c for c in header if c.startswith("chi2__")]

    def first_with_prefix(prefixes: Iterable[str], fallback: Optional[str] = None) -> Optional[str]:
        for prefix in prefixes:
            matches = sorted(c for c in cols if c.lower().startswith(prefix.lower()))
            if matches:
                return matches[0]
        if fallback and fallback in cols:
            return fallback
        return None

    selected: List[str] = []
    for cand in [
        first_with_prefix(["chi2__bao."], "chi2__BAO"),
        first_with_prefix(["chi2__sn."], "chi2__SN"),
        _first_existing(header, ["chi2__H0_edcl"]),
        first_with_prefix(["chi2__H0.", "chi2__h0.", "chi2__riess", "chi2__sh0es"], "chi2__H0"),
    ]:
        if cand and cand not in selected:
            selected.append(cand)

    represented_prefixes = ("chi2__bao.", "chi2__sn.", "chi2__H0.", "chi2__h0.", "chi2__riess", "chi2__sh0es")
    alias_cols = {"chi2__BAO", "chi2__SN", "chi2__H0", "chi2__H0_edcl"}
    for col in cols:
        if col in selected or col in alias_cols:
            continue
        if col.lower().startswith(tuple(p.lower() for p in represented_prefixes)):
            continue
        selected.append(col)
    return selected


def bestfit_summary(chain: np.ndarray, header: List[str]) -> Dict[str, Any]:
    chi2_col = _get_column(chain, header, "chi2")
    component_cols = select_unique_chi2_components(header)
    if chi2_col is not None:
        idx = int(np.argmin(chi2_col))
        method = "min(chi2)"
        total = float(chi2_col[idx])
    elif component_cols:
        arrays = [_get_column(chain, header, c) for c in component_cols]
        arrays = [a for a in arrays if a is not None]
        if not arrays:
            return {"method": None, "chi2_total_bestfit": None, "components": {}}
        summed = np.zeros(chain.shape[0], dtype=float)
        for arr in arrays:
            summed += arr
        idx = int(np.argmin(summed))
        method = "min(sum(unique chi2__))"
        total = float(summed[idx])
    else:
        return {"method": None, "chi2_total_bestfit": None, "components": {}}
    components: Dict[str, float] = {}
    for col in component_cols:
        arr = _get_column(chain, header, col)
        if arr is not None:
            components[col] = float(arr[idx])
    return {"method": method, "bestfit_row_index": idx, "chi2_total_bestfit": total, "components": components}


def formula_consistency(chain: np.ndarray, header: List[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    alpha = _get_column(chain, header, "alpha_R")
    h0 = _get_column(chain, header, "H0")
    delta = _get_column(chain, header, "delta0")
    h0_obs = _get_column(chain, header, "H0_obs")
    if alpha is not None and delta is not None:
        err = delta - alpha * EDCL_F_NORM
        out["delta0_equals_alpha_R_times_f_norm"] = {"f_norm": EDCL_F_NORM, "max_abs_error": float(np.max(np.abs(err))), "rms_error": float(np.sqrt(np.mean(err ** 2)))}
    if alpha is not None and h0 is not None and h0_obs is not None:
        expected = h0 * (1.0 + alpha * EDCL_F_NORM)
        err = h0_obs - expected
        out["H0_obs_equals_H0_times_one_plus_delta0"] = {"f_norm": EDCL_F_NORM, "max_abs_error": float(np.max(np.abs(err))), "rms_error": float(np.sqrt(np.mean(err ** 2)))}
    return out


def analyze_chain(path: str, name: str, is_edcl: bool = False) -> Dict[str, Any]:
    chain, header = load_chain(path)
    weights = _weight_column(chain, header)
    result: Dict[str, Any] = {"name": name, "path": str(path), "n_samples": int(chain.shape[0]), "eff_samples": float(np.sum(weights)), "columns": header, "parameters": {}, "bestfit": bestfit_summary(chain, header)}
    for param in ["H0", "omega_b", "omega_cdm"]:
        col = _get_column(chain, header, param)
        if col is not None:
            result["parameters"][param] = weighted_stats(col, weights)
    if is_edcl:
        for param in ["alpha_R", "H0_obs", "delta0"]:
            col = _get_column(chain, header, param)
            if col is not None:
                result["parameters"][param] = weighted_stats(col, weights)
        fc = formula_consistency(chain, header)
        if fc:
            result["formula_consistency"] = fc
    if result["bestfit"].get("chi2_total_bestfit") is not None:
        result["chi2_best"] = result["bestfit"]["chi2_total_bestfit"]
    chi2 = _get_column(chain, header, "chi2")
    if chi2 is not None:
        result["chi2_mean"] = float(np.average(chi2, weights=weights))
    return result


def run_validation_tests(results: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    tests: Dict[str, Dict[str, Any]] = {}
    if "edcl_with_h0" in results and "alpha_R" in results["edcl_with_h0"].get("parameters", {}):
        alpha = results["edcl_with_h0"]["parameters"]["alpha_R"]
        threshold = 0.02
        tests["activation"] = {
            "description": "alpha_R activates with the local H0_obs likelihood",
            "alpha_R_mean": alpha["mean"],
            "alpha_R_std": alpha["std"],
            "alpha_R_q16": alpha["q16"],
            "alpha_R_q84": alpha["q84"],
            "threshold": threshold,
            "pass": bool(alpha["q16"] > threshold),
            "note": "Standalone chain-analyzer check; canonical workdir validator uses validation_config.yaml.",
        }
    if "edcl_with_h0" in results and "edcl_no_h0" in results:
        with_h0 = results["edcl_with_h0"].get("parameters", {}).get("alpha_R", {})
        without_h0 = results["edcl_no_h0"].get("parameters", {}).get("alpha_R", {})
        if with_h0 and without_h0:
            q95 = without_h0.get("q95", float("nan"))
            mean_ratio = without_h0["mean"] / with_h0["mean"] if with_h0.get("mean", 0) > 0 else float("nan")
            threshold_pass = bool(np.isfinite(q95) and q95 <= CONFIGURED_COLLAPSE_Q95_THRESHOLD)
            tests["collapse_tendency"] = {
                "description": "alpha_R shifts toward zero without the local H0_obs likelihood; configured collapse pass requires q95(alpha_R) <= 0.03",
                "alpha_R_with_h0_mean": with_h0["mean"],
                "alpha_R_with_h0_median": with_h0.get("median"),
                "alpha_R_without_h0_mean": without_h0["mean"],
                "alpha_R_without_h0_q95": q95,
                "mean_ratio_diagnostic": mean_ratio,
                "configured_q95_pass_threshold": CONFIGURED_COLLAPSE_Q95_THRESHOLD,
                "status": "PASS_threshold_met" if threshold_pass else "WARN_threshold_not_met",
                "pass": threshold_pass,
                "claim_boundary": "If q95 exceeds 0.03, describe the no-H0 result as a collapse tendency, not a configured-threshold collapse pass.",
            }
    if "edcl_with_h0" in results and "H0_obs" in results["edcl_with_h0"].get("parameters", {}):
        h0_obs = results["edcl_with_h0"]["parameters"]["H0_obs"]
        sigma_combined = math.sqrt(h0_obs["std"] ** 2 + RIESS_H0_STD ** 2)
        tension = abs(h0_obs["mean"] - RIESS_H0_MEAN) / sigma_combined
        tests["h0_match"] = {"description": "H0_obs is consistent with the Riess measurement", "H0_obs_mean": h0_obs["mean"], "H0_obs_std": h0_obs["std"], "H0_riess": RIESS_H0_MEAN, "sigma_riess": RIESS_H0_STD, "tension_sigma": tension, "pass": bool(tension < 1.0)}
    if "lcdm" in results and "edcl_with_h0" in results:
        lcdm_bf = results["lcdm"].get("bestfit", {})
        edcl_bf = results["edcl_with_h0"].get("bestfit", {})
        if lcdm_bf.get("chi2_total_bestfit") is not None and edcl_bf.get("chi2_total_bestfit") is not None:
            delta_chi2 = edcl_bf["chi2_total_bestfit"] - lcdm_bf["chi2_total_bestfit"]
            tests["chi2_improvement"] = {"description": "EDCL has a lower best-fit chi2 than LCDM in this run", "lcdm_chi2_best": lcdm_bf["chi2_total_bestfit"], "edcl_chi2_best": edcl_bf["chi2_total_bestfit"], "delta_chi2": delta_chi2, "pass": bool(delta_chi2 < 0), "claim_boundary": "A lower chi2 here is diagnostic only, not decisive model-comparison evidence."}
    return tests


def _fmt(value: Any, ndp: int = 4) -> str:
    try:
        return f"{float(value):.{ndp}f}"
    except Exception:
        return "n/a"


def print_results(results: Dict[str, Dict[str, Any]], tests: Dict[str, Dict[str, Any]]) -> None:
    print("=" * 70)
    print("TIER-A1 CHAIN ANALYSIS")
    print("=" * 70)
    print("Standalone chain-file analysis; use validate_tiera1_lateonly_results.py for workdir/YAML/log validation.")
    print("Claim boundary: mechanism activation with no-H0 collapse-tendency control, not decisive full Hubble-tension resolution.")
    for _, res in results.items():
        print(f"\n{res['name']}:")
        print(f"  Path: {res['path']}")
        print(f"  Samples: {res['n_samples']}, Effective: {_fmt(res['eff_samples'], 0)}")
        params = res.get("parameters", {})
        for param in ["H0", "alpha_R", "delta0", "H0_obs"]:
            if param in params:
                p = params[param]
                print(f"  {param} = {_fmt(p['mean'])} +/- {_fmt(p['std'])}; q95={_fmt(p.get('q95'))}")
        bf = res.get("bestfit", {})
        if bf.get("chi2_total_bestfit") is not None:
            print(f"  Best chi2 = {_fmt(bf['chi2_total_bestfit'], 4)} ({bf.get('method')})")
    print("\n" + "=" * 70)
    print("VALIDATION / DIAGNOSTIC CHECKS")
    print("=" * 70)
    for name, test in tests.items():
        status = test.get("status") or ("PASS" if test.get("pass") else "FAIL")
        print(f"\n{name.upper()}: {status}")
        print(f"  {test.get('description', '')}")
        if name == "collapse_tendency":
            print(f"  no-H0 q95(alpha_R): {_fmt(test.get('alpha_R_without_h0_q95'))}")
            print(f"  configured pass threshold: <= {_fmt(test.get('configured_q95_pass_threshold'))}")
            print("  Interpretation: collapse tendency only unless threshold is met.")
    n_pass = sum(1 for t in tests.values() if t.get("pass"))
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Checks passing their configured/diagnostic criteria: {n_pass}/{len(tests)}")
    print("Do not treat this standalone analyzer as full workdir-backed provenance.")


def create_plot(results: Dict[str, Dict[str, Any]], output_path: str) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available, skipping plot generation")
        return
    fig, ax = plt.subplots(figsize=(10, 6))
    if "lcdm" in results and "H0" in results["lcdm"].get("parameters", {}):
        h0 = results["lcdm"]["parameters"]["H0"]
        ax.axvspan(h0["mean"] - h0["std"], h0["mean"] + h0["std"], alpha=0.3, label=f'LCDM H0: {h0["mean"]:.1f} +/- {h0["std"]:.1f}')
    if "edcl_with_h0" in results and "H0_obs" in results["edcl_with_h0"].get("parameters", {}):
        h0 = results["edcl_with_h0"]["parameters"]["H0_obs"]
        ax.axvspan(h0["mean"] - h0["std"], h0["mean"] + h0["std"], alpha=0.3, label=f'EDCL H0_obs: {h0["mean"]:.1f} +/- {h0["std"]:.1f}')
    ax.axvline(RIESS_H0_MEAN, linestyle="--", linewidth=2, label=f"Riess ({RIESS_H0_MEAN:.2f} +/- {RIESS_H0_STD:.2f})")
    ax.set_xlabel("H0 (km/s/Mpc)")
    ax.set_ylabel("Posterior summary band")
    ax.set_title("EDCL Tier-A1 H0_obs Mechanism Diagnostic")
    ax.legend(loc="upper left")
    ax.set_xlim(65, 78)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\nPlot saved to: {output_path}")


def find_chains(chains_dir: Path) -> Dict[str, Dict[str, Any]]:
    chain_configs = [
        ("lcdm_production.1.txt", "lcdm", "LCDM (baseline)", False),
        ("lcdm_medium.1.txt", "lcdm", "LCDM (baseline)", False),
        ("lcdm_quick.1.txt", "lcdm", "LCDM (baseline)", False),
        ("lcdm.1.txt", "lcdm", "LCDM (baseline)", False),
        ("lcdm_production.1.txt.gz", "lcdm", "LCDM (baseline)", False),
        ("edcl_production.1.txt", "edcl_with_h0", "EDCL (with H0_obs)", True),
        ("edcl_medium.1.txt", "edcl_with_h0", "EDCL (with H0_obs)", True),
        ("edcl_fixed_test.1.txt", "edcl_with_h0", "EDCL (with H0_obs)", True),
        ("edcl.1.txt", "edcl_with_h0", "EDCL (with H0_obs)", True),
        ("edcl_production.1.txt.gz", "edcl_with_h0", "EDCL (with H0_obs)", True),
        ("edcl_no_h0_medium.1.txt", "edcl_no_h0", "EDCL (no local H0)", True),
        ("edcl_fixed_no_sh0es.1.txt", "edcl_no_h0", "EDCL (no local H0)", True),
        ("edcl_no_h0.1.txt", "edcl_no_h0", "EDCL (no local H0)", True),
        ("edcl_no_h0_medium.1.txt.gz", "edcl_no_h0", "EDCL (no local H0)", True),
    ]
    results: Dict[str, Dict[str, Any]] = {}
    for filename, key, name, is_edcl in chain_configs:
        if key in results:
            continue
        path = chains_dir / filename
        if path.exists():
            print(f"Loading: {path}")
            results[key] = analyze_chain(str(path), name, is_edcl)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze EDCL Tier-A1 validation MCMC chain files.")
    parser.add_argument("-d", "--chains-dir", default="./chains", help="Directory containing chain files.")
    parser.add_argument("-o", "--output", default=None, help="Output file for JSON results.")
    parser.add_argument("-p", "--plot", action="store_true", help="Generate H0 comparison plot.")
    parser.add_argument("--plot-output", default="h0_comparison.png", help="Output path for plot.")
    args = parser.parse_args()
    chains_dir = Path(args.chains_dir)
    if not chains_dir.exists():
        print(f"ERROR: Chains directory not found: {chains_dir}", file=sys.stderr)
        return 1
    results = find_chains(chains_dir)
    if not results:
        print(f"ERROR: No chain files found in {chains_dir}", file=sys.stderr)
        return 1
    tests = run_validation_tests(results)
    print_results(results, tests)
    if args.output:
        output_data = {
            "analysis_type": "standalone_chain_analysis",
            "claim_boundary": "mechanism activation with no-H0 collapse tendency only; not decisive full Hubble-tension resolution",
            "constants": {"RIESS_H0_MEAN": RIESS_H0_MEAN, "RIESS_H0_STD": RIESS_H0_STD, "EDCL_F_NORM": EDCL_F_NORM, "CONFIGURED_COLLAPSE_Q95_THRESHOLD": CONFIGURED_COLLAPSE_Q95_THRESHOLD},
            "chains": results,
            "tests": tests,
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
        print(f"\nResults saved to: {args.output}")
    if args.plot:
        create_plot(results, args.plot_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
