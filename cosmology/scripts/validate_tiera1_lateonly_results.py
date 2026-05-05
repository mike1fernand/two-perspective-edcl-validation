#!/usr/bin/env python3
"""
validate_tiera1_lateonly_results.py

Purpose
-------
Tier-A1 (late-only) referee-safe validator for the EDCL Phase-1 pipeline.

This script is designed to be:
  - Deterministic (no stochastic thresholds).
  - Defensive (robust chain discovery, robust parsing, strict JSON output).
  - Configuration-aware: stale EDCL direct-H0 YAMLs fail as configuration errors
    before being interpreted as EDCL physics failures.
  - Referee-friendly (explicit, pre-registered acceptance tests).

Inputs
------
Either:
  --workdir <DIR>   : the Tier-A1 suite work directory created by
                      cosmology/scripts/run_tiera1_lateonly_suite.py

Or:
  --bundle <ZIP>    : a bundle zip previously produced by the suite runner.
                      The bundle is extracted to a temp directory for validation.

Outputs (written into the workdir root)
---------------------------------------
  results_summary.json : machine-readable summary
  results_report.md    : human-readable report

Exit codes
----------
  0 : PASS
  1 : WARN (quality warnings in non-referee profiles)
  2 : FAIL
"""
from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import io
import json
import os
import re
import shutil
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml  # type: ignore
except Exception as e:
    raise RuntimeError("PyYAML is required. Install with: pip install pyyaml") from e


# -----------------------------
# Utilities
# -----------------------------
def _utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d_%H%M%S")


def _safe_read_text(path: Path, max_bytes: int = 2_000_000) -> str:
    try:
        data = path.read_bytes()
    except Exception:
        return ""
    if len(data) > max_bytes:
        data = data[:max_bytes] + b"\n[TRUNCATED]\n"
    return data.decode("utf-8", errors="replace")


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise RuntimeError(f"YAML root is not a dictionary: {path}")
    return data


def _write_text(path: Path, s: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(s, encoding="utf-8")


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def _weighted_quantile(x: List[float], w: List[float], q: float) -> float:
    """Weighted quantile, using cumulative weights."""
    if not x:
        return float("nan")
    if q <= 0:
        return min(x)
    if q >= 1:
        return max(x)

    idx = sorted(range(len(x)), key=lambda i: x[i])
    xs = [x[i] for i in idx]
    ws = [w[i] for i in idx]

    tot = float(sum(ws))
    if not (tot > 0):
        n = len(xs)
        k = int(round(q * (n - 1)))
        return xs[max(0, min(n - 1, k))]

    target = q * tot
    c = 0.0
    for xi, wi in zip(xs, ws):
        c += wi
        if c >= target:
            return xi
    return xs[-1]


def _format_float(x: Optional[float], ndp: int = 6) -> str:
    if x is None:
        return "n/a"
    try:
        if x != x:
            return "nan"
        return f"{x:.{ndp}g}"
    except Exception:
        return "n/a"


# -----------------------------
# YAML configuration invariants
# -----------------------------
def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"yes", "true", "1", "on"}
    return False


def _is_direct_h0_key(key: str) -> bool:
    kl = str(key).strip().lower()
    if kl.startswith("h0."):
        return True
    if kl == "sh0es" or kl.startswith("sh0es."):
        return True
    return False


def _is_edcl_h0_key(key: str) -> bool:
    return str(key).strip().lower() == "h0_edcl"


def _contains_sh0es(obj: Any) -> bool:
    if isinstance(obj, str):
        return "sh0es" in obj.lower()
    if isinstance(obj, dict):
        return any("sh0es" in str(k).lower() or _contains_sh0es(v) for k, v in obj.items())
    if isinstance(obj, (list, tuple)):
        return any(_contains_sh0es(v) for v in obj)
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
    return _truthy(extra_args.get("edcl_on", False))


def _infer_h0_mode(run_key: str, yaml_rel: str, label: str) -> Optional[str]:
    """Infer expected H0 mode from validation_config naming."""
    hay = f"{run_key} {yaml_rel} {label}".lower()

    if run_key == "lcdm" or ("lcdm" in hay and "edcl" not in hay):
        return "lcdm_h0"

    if run_key == "edcl_h0":
        return "edcl_h0obs"

    if run_key == "edcl_noh0" or "no_sh0es" in hay or "no-h0" in hay or "noh0" in hay:
        return "edcl_noh0"

    if "edcl" in hay and ("h0" in hay or "sh0es" in hay):
        return "edcl_h0obs"

    return None


def _validate_yaml_h0_mode(yaml_path: Path, mode: str) -> List[str]:
    """Return configuration errors for one YAML/mode pair."""
    errors: List[str] = []
    try:
        cfg = _load_yaml(yaml_path)
    except Exception as e:
        return [f"{yaml_path}: could not load YAML: {e}"]

    like = cfg.get("likelihood", {})
    if not isinstance(like, dict) or not like:
        return [f"{yaml_path}: missing likelihood dictionary"]

    keys = [str(k) for k in like.keys()]
    direct_h0 = [k for k in keys if _is_direct_h0_key(k)]
    edcl_h0 = [k for k in keys if _is_edcl_h0_key(k)]
    edcl_enabled = _is_edcl_enabled(cfg)

    if len(direct_h0) + len(edcl_h0) > 1:
        errors.append(f"{yaml_path}: multiple local-H0 likelihoods present: {direct_h0 + edcl_h0}")

    if mode == "lcdm_h0":
        if edcl_enabled:
            errors.append(f"{yaml_path}: LCDM run has edcl_on enabled")
        if edcl_h0:
            errors.append(f"{yaml_path}: LCDM run must not use H0_edcl")
        if len(direct_h0) != 1:
            errors.append(f"{yaml_path}: LCDM H0 run should have exactly one direct local-H0 likelihood, found {direct_h0}")

    elif mode == "edcl_h0obs":
        if not edcl_enabled:
            errors.append(f"{yaml_path}: EDCL H0_obs run does not have edcl_on enabled")
        if direct_h0:
            errors.append(f"{yaml_path}: EDCL H0_obs run must not use direct local-H0 likelihood(s): {direct_h0}")
        if len(edcl_h0) != 1:
            errors.append(f"{yaml_path}: EDCL H0_obs run must use exactly one H0_edcl likelihood, found {edcl_h0}")

        params = cfg.get("params", {})
        if not isinstance(params, dict):
            errors.append(f"{yaml_path}: missing params dictionary")
        else:
            if "H0_obs" not in params:
                errors.append(f"{yaml_path}: EDCL H0_obs run is missing derived parameter H0_obs")
            if "delta0" not in params:
                errors.append(f"{yaml_path}: EDCL H0_obs run is missing derived parameter delta0")

    elif mode == "edcl_noh0":
        if not edcl_enabled:
            errors.append(f"{yaml_path}: EDCL no-H0 run does not have edcl_on enabled")
        if direct_h0 or edcl_h0:
            errors.append(f"{yaml_path}: EDCL no-H0 run must not use any local-H0 likelihood; found {direct_h0 + edcl_h0}")

    else:
        errors.append(f"{yaml_path}: unknown H0 validation mode: {mode}")

    # Preserve conservative SH0ES marker guard when a local-H0 likelihood is present.
    local_h0_keys = set(direct_h0 + edcl_h0)
    if local_h0_keys:
        for key, value in like.items():
            if str(key) in local_h0_keys:
                continue
            if "sh0es" in str(key).lower() or _contains_sh0es(value):
                errors.append(f"{yaml_path}: possible SH0ES/H0 double-counting marker in likelihood {key!r}")

    # In no-H0 EDCL control, even hidden SH0ES markers are configuration errors.
    if mode == "edcl_noh0":
        for key, value in like.items():
            if "sh0es" in str(key).lower() or _contains_sh0es(value):
                errors.append(f"{yaml_path}: no-H0 control contains SH0ES marker in likelihood {key!r}")

    return errors


# -----------------------------
# Chain parsing
# -----------------------------
@dataclass
class ChainTable:
    columns: List[str]
    rows: List[List[float]]

    @property
    def n_rows(self) -> int:
        return len(self.rows)

    def col(self, name: str) -> Optional[List[float]]:
        try:
            j = self.columns.index(name)
        except ValueError:
            return None
        return [r[j] for r in self.rows]

    def bestfit_index(self, chi2_col: str) -> Optional[int]:
        c = self.col(chi2_col)
        if c is None:
            return None
        best_i = None
        best = None
        for i, v in enumerate(c):
            if best is None or v < best:
                best = v
                best_i = i
        return best_i


def _open_maybe_gz(path: Path) -> io.TextIOBase:
    if path.suffix == ".gz":
        return io.TextIOWrapper(gzip.open(path, "rb"), encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def _load_chain_file(path: Path) -> ChainTable:
    cols: List[str] = []
    rows: List[List[float]] = []
    with _open_maybe_gz(path) as f:
        for line in f:
            if not line.strip():
                continue
            if line.startswith("#"):
                if not cols:
                    cols = line.lstrip("#").split()
                continue
            if not cols:
                continue
            parts = line.split()
            if len(parts) != len(cols):
                continue
            try:
                rows.append([float(p) for p in parts])
            except Exception:
                continue
    return ChainTable(columns=cols, rows=rows)


def _merge_chains(chain_paths: List[Path]) -> ChainTable:
    if not chain_paths:
        return ChainTable(columns=[], rows=[])
    tables = [_load_chain_file(p) for p in chain_paths]
    common = tables[0].columns[:]
    for t in tables[1:]:
        common = [c for c in common if c in t.columns]
    if not common:
        return ChainTable(columns=[], rows=[])
    merged_rows: List[List[float]] = []
    for t in tables:
        idxs = [t.columns.index(c) for c in common]
        for r in t.rows:
            merged_rows.append([r[j] for j in idxs])
    return ChainTable(columns=common, rows=merged_rows)


# -----------------------------
# Discovery helpers
# -----------------------------
def _split_output_prefix(output_value: str) -> Tuple[Path, str]:
    out = Path(output_value)
    if out.parent == Path("."):
        return Path("chains"), out.name
    return out.parent, out.name


def _find_updated_yaml(chain_dir: Path, prefix: str) -> Optional[Path]:
    for suffix in (".updated.yaml", ".updated.yml"):
        cand = chain_dir / f"{prefix}{suffix}"
        if cand.exists():
            return cand
    return None


def _discover_chain_files(chain_dir: Path, prefix: str) -> List[Path]:
    if not chain_dir.exists():
        return []
    pat = re.compile(rf"^{re.escape(prefix)}\.(\d+)\.txt(\.gz)?$")
    pat_single = re.compile(rf"^{re.escape(prefix)}\.txt(\.gz)?$")
    out: List[Path] = []
    for p in sorted(chain_dir.iterdir()):
        if not p.is_file():
            continue
        if pat.match(p.name) or pat_single.match(p.name):
            out.append(p)
    return out


def _resolve_chain_dir(chain_dir_raw: Path, workdir: Path) -> Path:
    if chain_dir_raw.is_absolute():
        if chain_dir_raw.exists():
            return chain_dir_raw
        return workdir / "chains"
    return workdir / chain_dir_raw


def _resolve_yaml_path(workdir: Path, yaml_rel: str) -> Optional[Path]:
    candidates = [
        workdir / yaml_rel,
        workdir / "yamls" / yaml_rel,
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


# -----------------------------
# Chi2 helpers
# -----------------------------
def _first_matching(columns: List[str], patterns: List[str]) -> Optional[str]:
    for pat in patterns:
        try:
            rx = re.compile(pat)
        except re.error:
            continue
        for c in columns:
            if rx.match(c):
                return c
    return None


def _select_unique_chi2_components(columns: List[str]) -> List[str]:
    """Select unique chi2 components without double-counting Cobaya aliases."""
    chi2_cols = [c for c in columns if c.startswith("chi2__")]

    def prefer(long_pat: str, short: str) -> Optional[str]:
        longs = [c for c in chi2_cols if re.match(long_pat, c)]
        if longs:
            return sorted(longs)[0]
        if short in chi2_cols:
            return short
        return None

    selected: List[str] = []
    for c in [
        prefer(r"^chi2__bao\.", "chi2__BAO"),
        prefer(r"^chi2__sn\.", "chi2__SN"),
        prefer(r"^chi2__H0_edcl$", "chi2__H0_edcl"),
        prefer(r"^chi2__H0\.", "chi2__H0"),
    ]:
        if c:
            selected.append(c)

    used = set(selected)
    for c in chi2_cols:
        if c in used:
            continue
        if c in ("chi2__BAO", "chi2__SN", "chi2__H0", "chi2__H0_edcl"):
            continue
        if c.startswith("chi2__bao.") or c.startswith("chi2__sn.") or c.startswith("chi2__H0."):
            continue
        selected.append(c)
    return selected


# -----------------------------
# Log scanning
# -----------------------------
def _scan_logs_for_fatal_patterns(log_dir: Path, patterns: List[str]) -> List[Dict[str, Any]]:
    if not log_dir.exists():
        return []
    compiled: List[re.Pattern] = []
    for p in patterns:
        if p.lower() in ("nan", "NaN".lower()):
            p = r"\bnan\b"
        try:
            compiled.append(re.compile(p, flags=re.IGNORECASE))
        except re.error:
            continue

    hits: List[Dict[str, Any]] = []
    for lp in sorted(log_dir.glob("*.log")):
        txt = _safe_read_text(lp)
        if not txt:
            continue
        for line in txt.splitlines():
            if "ERROR: Cannot uninstall" in line:
                continue
            for rx in compiled:
                if rx.search(line):
                    hits.append({"file": lp.name, "pattern": rx.pattern, "line": line.strip()[:300]})
                    break
    return hits


# -----------------------------
# Validation core
# -----------------------------
def validate(workdir: Path, config_path: Path, profile_requested: str) -> Tuple[int, Dict[str, Any], str]:
    cfg = _load_yaml(config_path)

    profiles = cfg.get("profiles", {}) or {}
    if profile_requested not in profiles:
        raise ValueError(f"Unknown profile '{profile_requested}'. Available: {sorted(profiles.keys())}")

    profile_resolved = profile_requested
    alias_of = (profiles.get(profile_requested) or {}).get("alias_of")
    if isinstance(alias_of, str) and alias_of:
        profile_resolved = alias_of

    prof = profiles.get(profile_resolved, {}) or {}
    quality_policy = prof.get("quality_gate_policy") or prof.get("policy") or "warn"
    quality_policy = "hard" if str(quality_policy).lower().startswith("hard") else "warn"
    min_samples = int(prof.get("min_samples", 0) or 0)
    min_chains = int(prof.get("min_chains", 1) or 1)

    acc = cfg.get("acceptance", {}) or {}
    acc_act = acc.get("activation", {}) or {}
    acc_col = acc.get("collapse", {}) or {}
    acc_ratio = acc.get("collapse_ratio", {}) or {}

    activation_run = str(acc_act.get("run", "edcl_h0"))
    activation_param = str(acc_act.get("param", "alpha_R"))
    activation_q = float(acc_act.get("q", 0.5))
    activation_min = float(acc_act.get("min", 0.03))

    collapse_run = str(acc_col.get("run", "edcl_noh0"))
    collapse_param = str(acc_col.get("param", "alpha_R"))
    collapse_q = float(acc_col.get("q", 0.95))
    collapse_pass_max = float(acc_col.get("pass_max", 0.03))
    collapse_strong_max = float(acc_col.get("strong_pass_max", 0.02))

    ratio_num_run = str(acc_ratio.get("numerator_run", collapse_run))
    ratio_num_q = float(acc_ratio.get("numerator_q", collapse_q))
    ratio_den_run = str(acc_ratio.get("denominator_run", activation_run))
    ratio_den_q = float(acc_ratio.get("denominator_q", activation_q))
    ratio_max = float(acc_ratio.get("max", 0.5))

    checks = cfg.get("checks", {}) or {}
    updated_yaml_required = bool(checks.get("updated_yaml_required", True))
    chi2_total_patterns = list(checks.get("chi2_total_column_patterns", [r"^chi2$"]))
    log_patterns = list(checks.get("log_fail_patterns", [])) or [
        r"Traceback \(most recent call last\)",
        r"Segmentation fault",
        r"\bFATAL\b",
        r"\bAborting\b",
        r"Class did not read input parameter",
        r"Serious error",
        r"RuntimeError:",
        r"ModuleNotFoundError:",
        r"ImportError:",
    ]
    required_paths = list(checks.get("required_paths", []))

    missing_required: List[str] = []
    for rel in required_paths:
        if not (workdir / rel).exists():
            missing_required.append(rel)

    log_hits = _scan_logs_for_fatal_patterns(workdir / "logs", log_patterns)
    runs_cfg = cfg.get("runs", {}) or {}

    needed_params_by_run: Dict[str, List[str]] = {}
    for r, p in [
        (activation_run, activation_param),
        (collapse_run, collapse_param),
        (ratio_num_run, collapse_param),
        (ratio_den_run, activation_param),
    ]:
        needed_params_by_run.setdefault(r, [])
        if p not in needed_params_by_run[r]:
            needed_params_by_run[r].append(p)

    run_results: Dict[str, Any] = {}
    quality_warnings: List[str] = []
    hard_fail_reasons: List[str] = []
    config_errors: List[str] = []
    config_checks: Dict[str, Any] = {}

    def _gate_or_warn(msg: str) -> None:
        if quality_policy == "hard":
            hard_fail_reasons.append(msg)
        else:
            quality_warnings.append(msg)

    for run_key, rcfg in runs_cfg.items():
        yaml_rel = rcfg.get("yaml")
        label = rcfg.get("label", run_key)
        track_params = rcfg.get("track_params") or needed_params_by_run.get(run_key, [])

        if not isinstance(yaml_rel, str):
            hard_fail_reasons.append(f"{run_key}: missing 'yaml' in validation_config.yaml")
            continue

        ypath = _resolve_yaml_path(workdir, yaml_rel)
        if ypath is None:
            hard_fail_reasons.append(f"{run_key}: YAML not found: {yaml_rel}")
            continue

        # Configuration invariant check before chain interpretation.
        mode = _infer_h0_mode(str(run_key), yaml_rel, str(label))
        yaml_config_errors: List[str] = []
        if mode:
            yaml_config_errors.extend(_validate_yaml_h0_mode(ypath, mode))
        else:
            _gate_or_warn(f"{run_key}: could not infer H0-likelihood validation mode for {yaml_rel}")

        ydata = _load_yaml(ypath)
        output_val = ydata.get("output")
        if not isinstance(output_val, str) or not output_val.strip():
            hard_fail_reasons.append(f"{run_key}: YAML missing 'output' path: {yaml_rel}")
            run_results[run_key] = {
                "label": label,
                "yaml": str(yaml_rel),
                "yaml_path": str(ypath),
                "h0_mode": mode,
                "config_errors": yaml_config_errors,
            }
            config_errors.extend(yaml_config_errors)
            continue

        chain_dir_raw, prefix = _split_output_prefix(output_val.strip())
        chain_dir = _resolve_chain_dir(chain_dir_raw, workdir)

        updated_yaml = _find_updated_yaml(chain_dir, prefix)
        if updated_yaml is not None and mode:
            yaml_config_errors.extend(_validate_yaml_h0_mode(updated_yaml, mode))

        if updated_yaml_required and updated_yaml is None:
            _gate_or_warn(f"{run_key}: missing updated YAML: {chain_dir}/{prefix}.updated.yaml")

        if yaml_config_errors:
            config_errors.extend(yaml_config_errors)

        config_checks[run_key] = {
            "mode": mode,
            "yaml_path": str(ypath),
            "updated_yaml": str(updated_yaml) if updated_yaml else None,
            "pass": not yaml_config_errors,
            "errors": yaml_config_errors,
        }

        chain_files = _discover_chain_files(chain_dir, prefix)
        if len(chain_files) < 1:
            hard_fail_reasons.append(f"{run_key}: no chain files found for prefix '{prefix}' in {chain_dir}")
            run_results[run_key] = {
                "label": label,
                "yaml": str(yaml_rel),
                "yaml_path": str(ypath),
                "h0_mode": mode,
                "config_errors": yaml_config_errors,
                "output": {"raw": output_val, "chain_dir": str(chain_dir), "prefix": prefix},
                "updated_yaml": str(updated_yaml) if updated_yaml else None,
                "chain_files": [],
            }
            continue

        if len(chain_files) < min_chains:
            _gate_or_warn(f"{run_key}: only {len(chain_files)} chain file(s) found (min_chains={min_chains})")

        merged = _merge_chains(chain_files)
        if merged.n_rows == 0 or not merged.columns:
            hard_fail_reasons.append(f"{run_key}: could not parse any samples from chain files")
            continue

        w = merged.col("weight") or [1.0] * merged.n_rows
        sum_weights = float(sum(w))
        ess = _effective_sample_size(w)

        if min_samples > 0 and ess < min_samples:
            _gate_or_warn(f"{run_key}: low effective sample size (ESS) = {ess:.0f} < min_samples={min_samples}; sum(weights)={sum_weights:.0f}")

        param_summary: Dict[str, Any] = {}
        for p in track_params:
            col = merged.col(p)
            if col is None:
                _gate_or_warn(f"{run_key}: missing parameter column '{p}' in chains")
                continue
            param_summary[p] = {
                "q05": _weighted_quantile(col, w, 0.05),
                "q50": _weighted_quantile(col, w, 0.50),
                "q95": _weighted_quantile(col, w, 0.95),
                "unweighted_q95_diagnostic": float(np.quantile(col, 0.95)) if "np" in globals() else None,
            }
            if p == "alpha_R":
                param_summary[p]["tail_ess_gt_0p03"] = _tail_effective_sample_size(col, w, 0.03)

        chi2_total_col = _first_matching(merged.columns, chi2_total_patterns)
        bestfit: Dict[str, Any] = {"method": None, "chi2_total_bestfit": None, "components": {}}
        if chi2_total_col and merged.col(chi2_total_col) is not None:
            i_bf = merged.bestfit_index(chi2_total_col)
            if i_bf is not None:
                bestfit["method"] = f"min({chi2_total_col})"
                bestfit["chi2_total_bestfit"] = merged.col(chi2_total_col)[i_bf]
                for cc in _select_unique_chi2_components(merged.columns):
                    cvals = merged.col(cc)
                    if cvals is not None:
                        bestfit["components"][cc] = cvals[i_bf]
        else:
            comp_cols = _select_unique_chi2_components(merged.columns)
            comp_arrays = [merged.col(c) for c in comp_cols]
            if comp_cols and all(a is not None for a in comp_arrays):
                totals = [sum(a[i] for a in comp_arrays if a is not None) for i in range(merged.n_rows)]
                i_bf = min(range(len(totals)), key=lambda i: totals[i])
                bestfit["method"] = "min(sum(unique chi2__))"
                bestfit["chi2_total_bestfit"] = totals[i_bf]
                for cc, arr in zip(comp_cols, comp_arrays):
                    if arr is not None:
                        bestfit["components"][cc] = arr[i_bf]

        run_results[run_key] = {
            "label": label,
            "yaml": str(yaml_rel),
            "yaml_path": str(ypath),
            "h0_mode": mode,
            "config_errors": yaml_config_errors,
            "output": {"raw": output_val, "chain_dir": str(chain_dir), "prefix": prefix},
            "updated_yaml": str(updated_yaml) if updated_yaml else None,
            "chain_files": [str(p) for p in chain_files],
            "n_rows": merged.n_rows,
            "sum_weights": sum_weights,
            "effective_sample_size": ess,
            "columns": merged.columns,
            "tracked_params": param_summary,
            "bestfit": bestfit,
        }

    # -----------------------------
    # Evaluate acceptance criteria
    # -----------------------------
    status = "PASS"
    reasons: List[str] = []

    if missing_required:
        status = "FAIL"
        reasons.append("Missing required paths: " + ", ".join(missing_required))

    if config_errors:
        status = "FAIL"
        reasons.append("Configuration/H0-likelihood invariant failure(s):")
        reasons.extend(config_errors)

    if hard_fail_reasons:
        status = "FAIL"
        reasons.extend(hard_fail_reasons)

    if log_hits:
        msg = f"Fatal-pattern matches detected in logs ({len(log_hits)} hit(s))."
        if quality_policy == "hard":
            status = "FAIL"
            reasons.append(msg)
        else:
            if status != "FAIL":
                status = "WARN"
            quality_warnings.append(msg)

    def _get_q(run_key: str, param: str, qkey: str) -> Optional[float]:
        try:
            return float(run_results[run_key]["tracked_params"][param][qkey])
        except Exception:
            return None

    act_key = "q50" if activation_q == 0.5 else "q95" if activation_q == 0.95 else "q50"
    col_key = "q95" if collapse_q == 0.95 else "q50"
    ratio_num_key = "q95" if ratio_num_q == 0.95 else "q50"
    ratio_den_key = "q50" if ratio_den_q == 0.5 else "q95"

    act_val = _get_q(activation_run, activation_param, act_key)
    activation_pass = (act_val is not None) and (act_val >= activation_min)
    if not activation_pass:
        status = "FAIL"
        reasons.append(
            f"Activation failed: q{int(100*activation_q)}({activation_param}) in {activation_run} = {_format_float(act_val)} < {activation_min}"
        )

    col_val = _get_q(collapse_run, collapse_param, col_key)
    collapse_pass = (col_val is not None) and (col_val <= collapse_pass_max)
    strong_pass = (col_val is not None) and (col_val <= collapse_strong_max)
    if not collapse_pass:
        status = "FAIL"
        reasons.append(
            f"Collapse failed: q{int(100*collapse_q)}({collapse_param}) in {collapse_run} = {_format_float(col_val)} > {collapse_pass_max}"
        )

    num = _get_q(ratio_num_run, collapse_param, ratio_num_key)
    den = _get_q(ratio_den_run, activation_param, ratio_den_key)
    ratio = None
    ratio_pass = None
    if num is not None and den is not None and den > 0:
        ratio = num / den
        ratio_pass = ratio <= ratio_max
        if not ratio_pass:
            status = "FAIL"
            reasons.append(
                f"Relative collapse failed: q{int(100*ratio_num_q)}({collapse_param})/q{int(100*ratio_den_q)}({activation_param}) = {_format_float(ratio)} > {ratio_max}"
            )

    if status == "PASS" and quality_warnings and quality_policy != "hard":
        status = "WARN"

    physics: Dict[str, Any] = {
        "activation": {
            "run": activation_run,
            "param": activation_param,
            "q": activation_q,
            "threshold_min": activation_min,
            "value": act_val,
            "pass": bool(activation_pass),
        },
        "collapse": {
            "run": collapse_run,
            "param": collapse_param,
            "q": collapse_q,
            "pass_max": collapse_pass_max,
            "strong_pass_max": collapse_strong_max,
            "value": col_val,
            "pass": bool(collapse_pass),
            "strong_pass": bool(strong_pass),
        },
        "collapse_ratio": {
            "numerator_run": ratio_num_run,
            "numerator_q": ratio_num_q,
            "denominator_run": ratio_den_run,
            "denominator_q": ratio_den_q,
            "max": ratio_max,
            "value": ratio,
            "pass": (bool(ratio_pass) if ratio_pass is not None else None),
        },
        "reasons": reasons,
    }

    summary: Dict[str, Any] = {
        "timestamp_utc": _utc_stamp(),
        "workdir": str(workdir),
        "config_path": str(config_path),
        "profile_requested": profile_requested,
        "profile_resolved": profile_resolved,
        "quality_gate_policy": quality_policy,
        "quality_warnings": quality_warnings,
        "missing_required_paths": missing_required,
        "log_fatal_hits": log_hits,
        "config_checks": config_checks,
        "configuration_errors": config_errors,
        "runs": run_results,
        "physics": physics,
        "status": status,
    }

    report = _make_report(
        summary=summary,
        activation_q=activation_q,
        activation_param=activation_param,
        activation_run=activation_run,
        activation_min=activation_min,
        collapse_q=collapse_q,
        collapse_param=collapse_param,
        collapse_run=collapse_run,
        collapse_pass_max=collapse_pass_max,
        collapse_strong_max=collapse_strong_max,
        ratio_num_q=ratio_num_q,
        ratio_den_q=ratio_den_q,
        ratio_max=ratio_max,
        act_val=act_val,
        activation_pass=activation_pass,
        col_val=col_val,
        collapse_pass=collapse_pass,
        strong_pass=strong_pass,
        ratio=ratio,
        ratio_pass=ratio_pass,
        reasons=reasons,
    )

    if status == "PASS":
        return 0, summary, report
    if status == "WARN":
        return 1, summary, report
    return 2, summary, report


def _make_report(
    *,
    summary: Dict[str, Any],
    activation_q: float,
    activation_param: str,
    activation_run: str,
    activation_min: float,
    collapse_q: float,
    collapse_param: str,
    collapse_run: str,
    collapse_pass_max: float,
    collapse_strong_max: float,
    ratio_num_q: float,
    ratio_den_q: float,
    ratio_max: float,
    act_val: Optional[float],
    activation_pass: bool,
    col_val: Optional[float],
    collapse_pass: bool,
    strong_pass: bool,
    ratio: Optional[float],
    ratio_pass: Optional[bool],
    reasons: List[str],
) -> str:
    md: List[str] = []
    md.append(f"# Tier-A1 validation report ({summary['timestamp_utc']} UTC)\n")
    md.append(f"**Overall status:** {summary['status']}\n")
    md.append(
        f"**Profile:** requested `{summary['profile_requested']}`, "
        f"resolved `{summary['profile_resolved']}` "
        f"(policy: `{summary['quality_gate_policy']}`)\n"
    )

    config_errors = summary.get("configuration_errors", []) or []
    if config_errors:
        md.append("## Configuration / H0-likelihood invariant failures\n")
        for err in config_errors:
            md.append(f"- {err}\n")
        md.append("\nThese are configuration failures, not EDCL physics failures. Fix the YAML path before interpreting alpha_R activation/collapse.\n")

    config_checks = summary.get("config_checks", {}) or {}
    if config_checks:
        md.append("## Configuration checks\n")
        for rk, check in config_checks.items():
            status = "PASS" if check.get("pass") else "FAIL"
            md.append(f"- `{rk}` [{status}]: mode=`{check.get('mode')}`, yaml=`{check.get('yaml_path')}`")
            if check.get("updated_yaml"):
                md.append(f", updated=`{check.get('updated_yaml')}`")
            md.append("\n")

    missing_required = summary.get("missing_required_paths", []) or []
    if missing_required:
        md.append("## Missing required paths\n")
        for p in missing_required:
            md.append(f"- {p}\n")

    quality_warnings = summary.get("quality_warnings", []) or []
    if quality_warnings:
        md.append("## Quality warnings\n")
        for wmsg in quality_warnings:
            md.append(f"- {wmsg}\n")

    log_hits = summary.get("log_fatal_hits", []) or []
    if log_hits:
        md.append("## Fatal-pattern log hits\n")
        for h in log_hits[:30]:
            md.append(f"- `{h['file']}` matched `{h['pattern']}`: `{h['line']}`\n")
        if len(log_hits) > 30:
            md.append(f"- ... ({len(log_hits)-30} more)\n")

    md.append("## Run summaries\n")
    for rk, rr in (summary.get("runs", {}) or {}).items():
        md.append(f"### {rk}: {rr.get('label','')}\n")
        md.append(f"- YAML: `{rr.get('yaml')}`\n")
        md.append(f"- YAML path: `{rr.get('yaml_path')}`\n")
        md.append(f"- H0 mode: `{rr.get('h0_mode')}`\n")
        if rr.get("config_errors"):
            md.append("- Config errors:\n")
            for err in rr.get("config_errors", []):
                md.append(f"  - {err}\n")
        out = rr.get("output", {}) or {}
        md.append(f"- Output prefix: `{out.get('prefix')}`\n")
        md.append(f"- Chain dir: `{out.get('chain_dir')}`\n")
        md.append(f"- Chain files ({len(rr.get('chain_files', []))}):\n")
        for cf in rr.get("chain_files", [])[:10]:
            md.append(f"  - `{cf}`\n")
        if len(rr.get("chain_files", [])) > 10:
            md.append(f"  - ... ({len(rr.get('chain_files', [])) - 10} more)\n")
        if "n_rows" in rr:
            md.append(f"- Samples: rows={rr.get('n_rows')}, sum(weights)={_format_float(rr.get('sum_weights'))}\n")
        md.append(f"- Updated YAML: `{rr.get('updated_yaml')}`\n" if rr.get("updated_yaml") else "- Updated YAML: **missing**\n")

        tps = rr.get("tracked_params", {}) or {}
        if tps:
            md.append("- Tracked parameter quantiles:\n")
            for p, qs in tps.items():
                md.append(
                    f"  - `{p}`: q05={_format_float(qs.get('q05'))}, "
                    f"q50={_format_float(qs.get('q50'))}, q95={_format_float(qs.get('q95'))}\n"
                )

        bf = rr.get("bestfit", {}) or {}
        if bf.get("chi2_total_bestfit") is not None:
            md.append(f"- Best-fit chi2_total: {_format_float(bf.get('chi2_total_bestfit'))} ({bf.get('method')})\n")
            comps = bf.get("components", {}) or {}
            if comps:
                md.append("  - Components:\n")
                for k, v in comps.items():
                    md.append(f"    - `{k}`: {_format_float(v)}\n")
        md.append("\n")

    md.append("## Acceptance criteria (Tier-A1)\n")
    md.append(
        textwrap.dedent(
            f"""
            **Activation:** q{int(100*activation_q)}({activation_param}) in `{activation_run}` >= {activation_min}

            **Collapse:** q{int(100*collapse_q)}({collapse_param}) in `{collapse_run}` <= {collapse_pass_max}
            - strong pass: <= {collapse_strong_max}

            **Relative collapse:** q{int(100*ratio_num_q)}({collapse_param}) / q{int(100*ratio_den_q)}({activation_param}) <= {ratio_max}
            """
        ).strip()
        + "\n\n"
    )

    md.append("### Results\n")
    md.append(f"- Activation: {_format_float(act_val)} (>= {activation_min}) -> {'PASS' if activation_pass else 'FAIL'}\n")
    md.append(f"- Collapse: {_format_float(col_val)} (<= {collapse_pass_max}) -> {'PASS' if collapse_pass else 'FAIL'}\n")
    if strong_pass:
        md.append(f"  - Strong pass achieved (<= {collapse_strong_max}).\n")
    if ratio is not None:
        md.append(f"- Relative collapse: {_format_float(ratio)} (<= {ratio_max}) -> {'PASS' if ratio_pass else 'FAIL'}\n")
    else:
        md.append("- Relative collapse: n/a (missing required quantiles)\n")

    if reasons:
        md.append("\n## Failure reasons\n")
        for r in reasons:
            md.append(f"- {r}\n")

    return "\n".join(md)


def _resolve_config_path(config_arg: str, workdir: Path) -> Path:
    p = Path(config_arg)
    if p.is_absolute() and p.exists():
        return p
    if p.exists():
        return p.resolve()

    # Bundle-friendly fallback: config may be included under repo/ or not included at all.
    candidates = [
        workdir / config_arg,
        workdir / "repo" / config_arg,
        Path.cwd() / config_arg,
    ]
    for cand in candidates:
        if cand.exists():
            return cand.resolve()

    raise FileNotFoundError(f"Validation config not found: {config_arg}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default="", help="Suite work directory (preferred).")
    ap.add_argument("--bundle", default="", help="Bundle zip to validate (will be extracted).")
    ap.add_argument(
        "--config",
        default="cosmology/config/validation_config.yaml",
        help="Validation config yaml (repo-relative unless absolute).",
    )
    ap.add_argument(
        "--profile",
        default="iterate",
        choices=["iterate", "smoke", "referee"],
        help="Validation profile. 'smoke' is an alias of 'iterate'.",
    )
    args = ap.parse_args()

    if not args.workdir and not args.bundle:
        ap.error("Must provide either --workdir or --bundle")

    cleanup_dir: Optional[str] = None
    workdir = Path(args.workdir).resolve() if args.workdir else None
    if args.bundle:
        bundle = Path(args.bundle).resolve()
        if not bundle.exists():
            raise FileNotFoundError(bundle)
        tmp = tempfile.mkdtemp(prefix="tiera1_validate_")
        cleanup_dir = tmp
        shutil.unpack_archive(str(bundle), tmp)
        workdir = Path(tmp).resolve()

    assert workdir is not None
    cfg_path = _resolve_config_path(args.config, workdir)

    exit_code, summary, report = validate(workdir=workdir, config_path=cfg_path, profile_requested=args.profile)

    _write_json(workdir / "results_summary.json", summary)
    _write_text(workdir / "results_report.md", report)

    print(report)

    if cleanup_dir:
        # Keep extracted temp dir for forensic debugging. It is usually under /tmp and can be deleted by the OS.
        print(f"\n[INFO] Bundle was extracted to: {cleanup_dir}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
