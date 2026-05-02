#!/usr/bin/env python3
"""
run_tiera1_lateonly_suite.py

Tier-A1 "late-time Cobaya" suite runner for the Two-Perspective / EDCL project.

Design goals:
- ZERO hand-typed likelihood guessing: always run cobaya-install from the rendered YAMLs.
- Hard separation of LCDM vs EDCL CLASS inputs.
- Deterministic CLASS checkout: prefer v3.3.4 if available; else highest semver tag.
- Fail-fast on build/patch/preflight and on YAML H0-likelihood invariants before MCMC.
- Forensic logs for every command.
- End-to-end bundle zip suitable for a referee (manifest + logs + YAMLs + updated YAMLs + validator reports).

What it runs (late-time only):
  1) LCDM late-only (BAO+SN+direct local H0)
  2) EDCL late-only (BAO+SN+custom observed-frame H0_obs likelihood)
  3) EDCL late-only (BAO+SN only; no explicit H0)  [no-H0 collapse test]

It also runs Tier-A0 preflight scripts:
  cosmology/scripts/smoke_test_classy_edcl.py
  cosmology/scripts/preflight_tiera_background.py

And validates outputs:
  cosmology/scripts/validate_tiera1_lateonly_results.py

Usage (Colab or local):
  python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile iterate   # (alias: smoke)
  python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile referee

Outputs:
  <WORKDIR>/manifest.json
  <WORKDIR>/logs/*.log
  <WORKDIR>/yamls/*.yaml (+ *.updated.yaml created by cobaya-install)
  <WORKDIR>/chains/*
  <WORKDIR>/results_summary.json
  <WORKDIR>/results_report.md
  <WORKDIR>/bundle_edcl_tiera1.zip

Notes for Colab:
- You must run this from the repo root (folder containing cosmology/).
- Internet access is required to clone CLASS and to install Cobaya likelihood data.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import zipfile
from typing import Dict, Any, List, Optional, Tuple

try:
    import yaml  # type: ignore
except Exception:
    yaml = None  # type: ignore


# ----------------------------
# Utilities
# ----------------------------
def _utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d_%H%M%S")


def _is_colab() -> bool:
    if os.path.isdir("/content"):
        try:
            import google.colab  # type: ignore  # noqa: F401
            return True
        except Exception:
            return False
    return False


def _print_cmd(args: List[str]) -> str:
    # For printing only; do not execute via shell.
    out = []
    for a in args:
        if re.fullmatch(r"[A-Za-z0-9_/@%+=:,.\-]+", a):
            out.append(a)
        else:
            out.append("'" + a.replace("'", "'\"'\"'") + "'")
    return " ".join(out)


def run_cmd(
    args: List[str],
    *,
    cwd: Optional[str] = None,
    log_path: Optional[str] = None,
    check: bool = True,
    env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess[str]:
    cmd_str = _print_cmd(args)
    print("\n$ " + cmd_str)
    p = subprocess.run(
        args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    out = p.stdout or ""
    print(out)
    if log_path:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(out)
    if check and p.returncode != 0:
        raise RuntimeError(
            f"Command failed (exit {p.returncode}): {cmd_str}\nSee log: {log_path}"
        )
    return p


def md5_file(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_repo_root(start: str) -> str:
    p = pathlib.Path(start).resolve()
    for parent in [p] + list(p.parents):
        if (parent / "cosmology" / "cobaya").is_dir():
            return str(parent)
    raise RuntimeError(
        "Could not locate repo root (expected cosmology/cobaya/). Run from within the repo."
    )


def parse_tag_semver(tag: str) -> Optional[Tuple[int, int, int]]:
    m = re.fullmatch(r"v(\d+)\.(\d+)(?:\.(\d+))?", tag.strip())
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))


def choose_class_tag(tags: List[str]) -> Tuple[str, str]:
    tags = [t.strip() for t in tags if t.strip()]
    if "v3.3.4" in tags:
        return "v3.3.4", "preferred v3.3.4 present"
    sem = []
    for t in tags:
        v = parse_tag_semver(t)
        if v is not None:
            sem.append((v, t))
    if not sem:
        raise RuntimeError("No semver-like tags found in CLASS repo (expected vMAJOR.MINOR[.PATCH]).")
    sem.sort()
    return sem[-1][1], "v3.3.4 not present; chose highest available semver"


def _resolve_updated_yaml(path: str) -> str:
    """If <path>.updated.yaml exists, use it; else return original path."""
    p = pathlib.Path(path)
    cand = p.with_name(p.stem + ".updated.yaml")
    cand2 = p.with_name(p.stem + ".updated.yml")
    if cand.exists():
        return str(cand)
    if cand2.exists():
        return str(cand2)
    return path


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)


def _load_yaml(path: str) -> Dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML required for YAML invariant checks (pip install pyyaml).")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise RuntimeError(f"YAML root is not a dictionary: {path}")
    return data


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


def _check_class_path_in_yaml(cfg: Dict[str, Any], expected_class_dir: str, yaml_path: str) -> None:
    theory = cfg.get("theory", {})
    classy = theory.get("classy", {}) if isinstance(theory, dict) else {}
    path = classy.get("path") if isinstance(classy, dict) else None
    if not isinstance(path, str) or not path:
        raise RuntimeError(f"{yaml_path}: theory.classy.path is missing or not a string")
    if os.path.abspath(path) != os.path.abspath(expected_class_dir):
        raise RuntimeError(
            f"{yaml_path}: theory.classy.path points to {path!r}, expected patched CLASS path {expected_class_dir!r}"
        )


def check_h0_likelihood_invariant(yaml_path: str, mode: str, expected_class_dir: Optional[str] = None) -> None:
    """Fail fast if a rendered/updated YAML uses the wrong H0 convention.

    Modes:
      lcdm_h0      : LCDM with one direct local-H0 likelihood.
      edcl_h0obs   : EDCL with custom H0_edcl and no direct local-H0 likelihood.
      edcl_noh0    : EDCL with no local-H0 likelihood at all.
    """
    cfg = _load_yaml(yaml_path)
    like = cfg.get("likelihood", {})
    if not isinstance(like, dict) or not like:
        raise RuntimeError(f"{yaml_path}: missing likelihood dictionary")

    keys = [str(k) for k in like.keys()]
    direct_h0 = [k for k in keys if _is_direct_h0_key(k)]
    edcl_h0 = [k for k in keys if _is_edcl_h0_key(k)]
    edcl_enabled = _is_edcl_enabled(cfg)

    if expected_class_dir is not None:
        _check_class_path_in_yaml(cfg, expected_class_dir, yaml_path)

    if mode == "lcdm_h0":
        if edcl_enabled:
            raise RuntimeError(f"{yaml_path}: LCDM run has edcl_on enabled")
        if edcl_h0:
            raise RuntimeError(f"{yaml_path}: LCDM run must not use H0_edcl")
        if len(direct_h0) != 1:
            raise RuntimeError(f"{yaml_path}: LCDM H0 run should have exactly one direct local-H0 likelihood, found {direct_h0}")
        return

    if mode == "edcl_h0obs":
        if not edcl_enabled:
            raise RuntimeError(f"{yaml_path}: EDCL H0_obs run does not have edcl_on enabled")
        if direct_h0:
            raise RuntimeError(f"{yaml_path}: EDCL H0_obs run must not use direct local-H0 likelihood(s): {direct_h0}")
        if len(edcl_h0) != 1:
            raise RuntimeError(f"{yaml_path}: EDCL H0_obs run must use exactly one H0_edcl likelihood, found {edcl_h0}")

        params = cfg.get("params", {})
        if not isinstance(params, dict):
            raise RuntimeError(f"{yaml_path}: missing params dictionary")
        if "H0_obs" not in params:
            raise RuntimeError(f"{yaml_path}: EDCL H0_obs run is missing derived parameter H0_obs")
        if "delta0" not in params:
            raise RuntimeError(f"{yaml_path}: EDCL H0_obs run is missing derived parameter delta0")
        return

    if mode == "edcl_noh0":
        if not edcl_enabled:
            raise RuntimeError(f"{yaml_path}: EDCL no-H0 run does not have edcl_on enabled")
        if direct_h0 or edcl_h0:
            raise RuntimeError(f"{yaml_path}: EDCL no-H0 run must not use any local-H0 likelihood; found {direct_h0 + edcl_h0}")
        return

    raise RuntimeError(f"Unknown H0 invariant mode: {mode}")


def check_tiera1_yaml_set(yamls_dir: str, expected_class_dir: str, *, use_updated: bool = False) -> Dict[str, str]:
    specs = {
        "lcdm_lateonly.yaml": "lcdm_h0",
        "edcl_cosmo_lateonly.yaml": "edcl_h0obs",
        "edcl_cosmo_lateonly_no_sh0es.yaml": "edcl_noh0",
    }
    checked: Dict[str, str] = {}
    for name, mode in specs.items():
        path = os.path.join(yamls_dir, name)
        if use_updated:
            path = _resolve_updated_yaml(path)
        if not os.path.exists(path):
            raise RuntimeError(f"Expected YAML not found: {path}")
        check_h0_likelihood_invariant(path, mode, expected_class_dir=expected_class_dir)
        checked[name] = path
    return checked


# ----------------------------
# Main runner
# ----------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="iterate", choices=["iterate", "smoke", "referee"],
                    help="Run profile. iterate=fast (alias: smoke); referee=paper-grade.")
    ap.add_argument("--work-dir", default="", help="Working directory (default: timestamped under /content or repo root).")
    ap.add_argument("--skip-apt", action="store_true", help="Skip apt-get installs (local envs).")
    ap.add_argument("--skip-pip", action="store_true", help="Skip pip installs (deps already present).")
    ap.add_argument("--skip-class-build", action="store_true", help="Skip CLASS clone/patch/build (requires --class-path).")
    ap.add_argument("--class-path", default="", help="Path to existing CLASS repo (class_public) if --skip-class-build is set.")
    ap.add_argument("--mcmc-max-samples", type=int, default=0,
                    help="Override sampler.mcmc.max_samples in rendered YAMLs (0=use template defaults).")
    ap.add_argument("--skip-cobaya-install", action="store_true", help="Skip cobaya-install (assumes datasets already installed).")
    ap.add_argument("--skip-mcmc", action="store_true", help="Skip cobaya-run MCMC (still runs --test and validator may fail on missing chains).")
    ap.add_argument("--no-validate", action="store_true", help="Skip validator step at end.")
    ap.add_argument("--self-test-only", action="store_true", help="Only run lint-style self checks (no CLASS/Cobaya).")
    args = ap.parse_args()

    # Robust: locate repo root from this script's location (not the current working directory).
    repo_root = find_repo_root(str(pathlib.Path(__file__).resolve().parent))
    print("[INFO] Repo root:", repo_root)

    # Profile defaults (runner-side).
    default_max_samples = 20000 if args.profile in ("iterate", "smoke") else 100000

    stamp = _utc_stamp()
    if args.work_dir:
        work = args.work_dir
    else:
        work = f"/content/edcl_tiera1_{stamp}" if _is_colab() else os.path.join(repo_root, f"edcl_tiera1_{stamp}")

    logs = os.path.join(work, "logs")
    yamls_dir = os.path.join(work, "yamls")
    chains_dir = os.path.join(work, "chains")
    pkgs_dir = os.path.join(work, "cobaya_packages")
    os.makedirs(logs, exist_ok=True)
    os.makedirs(yamls_dir, exist_ok=True)
    os.makedirs(chains_dir, exist_ok=True)
    os.makedirs(pkgs_dir, exist_ok=True)

    manifest_path = os.path.join(work, "manifest.json")
    manifest: Dict[str, Any] = {
        "timestamp_utc": stamp,
        "profile": args.profile,
        "repo_root": repo_root,
        "workdir": work,
        "logs": logs,
        "yamls": yamls_dir,
        "chains": chains_dir,
        "cobaya_packages": pkgs_dir,
        "steps": [],
    }

    def write_manifest() -> None:
        _write_json(manifest_path, manifest)

    write_manifest()

    def step(name: str, fn, *, continue_on_failure: bool = False) -> Dict[str, Any]:
        print("\n" + "=" * 80)
        print("STEP:", name)
        print("=" * 80)
        rec: Dict[str, Any] = {"name": name, "ok": False}
        try:
            result = fn()
            if isinstance(result, dict):
                rec.update(result)
                rec["ok"] = bool(rec.get("ok", True))
            elif result is False:
                rec["ok"] = False
            else:
                rec["ok"] = True

            if not rec["ok"] and not continue_on_failure:
                raise RuntimeError(f"Step reported failure: {name}")
        except Exception as e:
            rec["ok"] = False
            rec["error"] = str(e)
            print("\n[FAIL]", e)
            if not continue_on_failure:
                raise
        finally:
            manifest["steps"].append(rec)
            write_manifest()
        return rec

    if args.self_test_only:
        # We rely on scripts/lint_pack.py for the deterministic self-test suite.
        lint = os.path.join(repo_root, "scripts", "lint_pack.py")
        run_cmd([sys.executable, lint], cwd=repo_root, log_path=os.path.join(logs, "00_lint_pack.log"))
        print("[OK] self-test-only complete.")
        return 0

    def install_deps():
        if not args.skip_apt:
            run_cmd(["apt-get", "update", "-qq"], log_path=os.path.join(logs, "01_apt_update.log"))
            run_cmd(["apt-get", "install", "-y", "-qq",
                     "git", "patch", "build-essential", "gfortran", "python3-dev", "zip", "unzip"],
                    log_path=os.path.join(logs, "02_apt_install.log"))
        else:
            print("[INFO] Skipping apt-get (per flag).")

        if not args.skip_pip:
            run_cmd([sys.executable, "-m", "pip", "-q", "install", "--upgrade", "pip"], log_path=os.path.join(logs, "03_pip_upgrade.log"))
            run_cmd([sys.executable, "-m", "pip", "-q", "install", "numpy", "scipy", "matplotlib", "cython", "pyyaml"],
                    log_path=os.path.join(logs, "04_pip_scientific.log"))
            run_cmd([sys.executable, "-m", "pip", "-q", "install", "cobaya==3.6"],
                    log_path=os.path.join(logs, "05_pip_cobaya.log"))
        else:
            print("[INFO] Skipping pip installs (per flag).")

    step("Install dependencies", install_deps)

    class_dir = os.path.join(work, "class_public")
    patch_path = os.path.join(repo_root, "cosmology", "patches", "class_edcl.patch")
    manifest["patch_md5"] = md5_file(patch_path)
    write_manifest()

    def build_class():
        nonlocal class_dir
        if args.skip_class_build:
            if not args.class_path:
                raise RuntimeError("--skip-class-build requires --class-path /path/to/class_public")
            class_dir = args.class_path
            print("[INFO] Using existing CLASS path:", class_dir)
            manifest["class_dir"] = class_dir
            write_manifest()
            return

        run_cmd(["git", "clone", "https://github.com/lesgourg/class_public.git", class_dir],
                log_path=os.path.join(logs, "10_git_clone_class.log"))

        run_cmd(["git", "fetch", "--tags", "--force"], cwd=class_dir, log_path=os.path.join(logs, "11_git_fetch_tags.log"))
        tags_txt = run_cmd(["git", "tag", "-l", "v*"], cwd=class_dir, log_path=os.path.join(logs, "12_git_tags.log")).stdout
        chosen, reason = choose_class_tag(tags_txt.splitlines())
        manifest["class_tag_chosen"] = chosen
        manifest["class_tag_reason"] = reason

        run_cmd(["git", "checkout", "-f", chosen], cwd=class_dir, log_path=os.path.join(logs, "13_git_checkout.log"))
        manifest["class_commit"] = run_cmd(["git", "rev-parse", "HEAD"], cwd=class_dir, log_path=os.path.join(logs, "14_git_commit.log")).stdout.strip()
        manifest["class_describe"] = run_cmd(["git", "describe", "--tags", "--always", "--dirty"], cwd=class_dir, log_path=os.path.join(logs, "15_git_describe.log")).stdout.strip()
        manifest["class_dir"] = class_dir
        write_manifest()

        val_script = os.path.join(repo_root, "cosmology", "scripts", "validate_patch.py")
        run_cmd([sys.executable, val_script, patch_path], cwd=repo_root, log_path=os.path.join(logs, "16_validate_patch.log"))

        run_cmd(["patch", "--dry-run", "-p1", "-i", patch_path], cwd=class_dir, log_path=os.path.join(logs, "17_patch_dryrun.log"))
        run_cmd(["patch", "-p1", "-i", patch_path], cwd=class_dir, log_path=os.path.join(logs, "18_patch_apply.log"))

        run_cmd(["make", "-j2"], cwd=class_dir, log_path=os.path.join(logs, "20_make.log"))
        run_cmd(["make", "classy"], cwd=class_dir, log_path=os.path.join(logs, "21_make_classy.log"))

    step("Clone/patch/build CLASS", build_class)

    def run_preflight():
        art = os.path.join(repo_root, "cosmology", "paper_artifacts")
        # Keep previous artifacts but avoid mixing old/new within same run.
        os.makedirs(art, exist_ok=True)

        smoke = os.path.join(repo_root, "cosmology", "scripts", "smoke_test_classy_edcl.py")
        pre = os.path.join(repo_root, "cosmology", "scripts", "preflight_tiera_background.py")

        run_cmd([sys.executable, smoke, "--class-path", class_dir], cwd=repo_root, log_path=os.path.join(logs, "30_smoke_test.log"))
        run_cmd(
            [
                sys.executable,
                pre,
                "--class-path",
                class_dir,
                "--alpha_R",
                "0.11824",
                "--log10_l0",
                "-20.908",
                "--kappa_tick",
                "0.08333333333333333",
                "--c4",
                "0.06",
                "--zeta",
                "0.5",
                "--ai",
                "1e-4",
                "--kernel",
                "exp",
            ],
            cwd=repo_root,
            log_path=os.path.join(logs, "31_preflight.log"),
        )

    step("Tier-A0 preflight (patched CLASS background)", run_preflight)

    def render_yamls():
        render = os.path.join(repo_root, "cosmology", "scripts", "render_yamls.py")
        run_cmd([sys.executable, render, "--class-path", class_dir, "--out-root", chains_dir],
                cwd=repo_root, log_path=os.path.join(logs, "40_render_yamls.log"))

        cob = os.path.join(repo_root, "cosmology", "cobaya")
        for name in ["lcdm_lateonly.yaml", "edcl_cosmo_lateonly.yaml", "edcl_cosmo_lateonly_no_sh0es.yaml"]:
            src = os.path.join(cob, name)
            if not os.path.exists(src):
                raise RuntimeError(f"Expected rendered YAML not found: {src}")
            shutil.copy2(src, os.path.join(yamls_dir, name))

        # Default run length by profile if not overridden.
        max_samples = int(args.mcmc_max_samples or default_max_samples)
        if max_samples > 0:
            if yaml is None:
                raise RuntimeError("PyYAML required to edit max_samples (pip install pyyaml).")
            for name in ["lcdm_lateonly.yaml", "edcl_cosmo_lateonly.yaml", "edcl_cosmo_lateonly_no_sh0es.yaml"]:
                p = os.path.join(yamls_dir, name)
                d = yaml.safe_load(open(p, "r", encoding="utf-8"))
                d.setdefault("sampler", {}).setdefault("mcmc", {})["max_samples"] = max_samples
                with open(p, "w", encoding="utf-8") as f:
                    yaml.safe_dump(d, f, sort_keys=False)

    step("Render Tier-A1 late-only YAMLs", render_yamls)

    def check_rendered_yamls():
        checked = check_tiera1_yaml_set(yamls_dir, class_dir, use_updated=False)
        print("[PASS] Rendered YAML H0-likelihood invariants satisfied.")
        for name, path in checked.items():
            print(f" - {name}: {path}")
        return {"checked_yamls": checked}

    step("Check rendered Tier-A1 H0-likelihood invariants", check_rendered_yamls)

    def run_guard():
        guard = os.path.join(repo_root, "cosmology", "scripts", "check_no_doublecount_sh0es.py")
        checked: Dict[str, str] = {}
        for name in ["lcdm_lateonly.yaml", "edcl_cosmo_lateonly.yaml", "edcl_cosmo_lateonly_no_sh0es.yaml"]:
            path = os.path.join(yamls_dir, name)
            run_cmd([sys.executable, guard, path],
                    cwd=repo_root, log_path=os.path.join(logs, f"45_guard_{name}.log"))
            checked[name] = path
        return {"guarded_yamls": checked}

    step("Run local-H0 / SH0ES guard on rendered YAMLs", run_guard)

    def cobaya_install():
        if args.skip_cobaya_install:
            print("[INFO] Skipping cobaya-install (per flag).")
            return
        for name in ["lcdm_lateonly.yaml", "edcl_cosmo_lateonly.yaml", "edcl_cosmo_lateonly_no_sh0es.yaml"]:
            y = os.path.join(yamls_dir, name)
            run_cmd(["cobaya-install", y, "-p", pkgs_dir],
                    cwd=repo_root, log_path=os.path.join(logs, f"50_cobaya_install_{name}.log"))

    step("cobaya-install datasets for Tier-A1", cobaya_install)

    def check_updated_yamls():
        checked = check_tiera1_yaml_set(yamls_dir, class_dir, use_updated=True)
        print("[PASS] Updated/preferred YAML H0-likelihood invariants satisfied.")
        for name, path in checked.items():
            print(f" - {name}: {path}")
        return {"checked_yamls": checked}

    step("Check updated Tier-A1 H0-likelihood invariants", check_updated_yamls)

    def cobaya_test_suite():
        # Prefer updated YAMLs after installation to avoid key drift.
        for name in ["lcdm_lateonly.yaml", "edcl_cosmo_lateonly.yaml", "edcl_cosmo_lateonly_no_sh0es.yaml"]:
            y = _resolve_updated_yaml(os.path.join(yamls_dir, name))
            run_cmd(["cobaya-run", y, "--test", "-p", pkgs_dir],
                    cwd=repo_root, log_path=os.path.join(logs, f"58_cobaya_test_{os.path.basename(y)}.log"))

    step("cobaya-run --test (initialisation-only)", cobaya_test_suite)

    def cobaya_run_suite():
        if args.skip_mcmc:
            print("[INFO] Skipping MCMC runs (per flag).")
            return
        for name in ["lcdm_lateonly.yaml", "edcl_cosmo_lateonly.yaml", "edcl_cosmo_lateonly_no_sh0es.yaml"]:
            y = _resolve_updated_yaml(os.path.join(yamls_dir, name))
            run_cmd(["cobaya-run", y, "-p", pkgs_dir],
                    cwd=repo_root, log_path=os.path.join(logs, f"60_cobaya_run_{os.path.basename(y)}.log"))

    step("Run Tier-A1 late-only suite (Cobaya)", cobaya_run_suite)

    def run_validator():
        if args.no_validate:
            print("[INFO] Skipping validator (per flag).")
            manifest["validator_exit_code"] = None
            manifest["validation_status"] = "skipped"
            write_manifest()
            return {"ok": True, "validation_status": "skipped", "validator_exit_code": None}

        val = os.path.join(repo_root, "cosmology", "scripts", "validate_tiera1_lateonly_results.py")
        p = run_cmd([sys.executable, val, "--workdir", work, "--profile", args.profile],
                    cwd=repo_root, log_path=os.path.join(logs, "70_validate_tiera1.log"), check=False)
        manifest["validator_exit_code"] = p.returncode

        if p.returncode == 0:
            status = "pass"
            ok = True
            print("[OK] Tier-A1 validation: PASS")
        elif p.returncode == 1:
            status = "warn"
            ok = True
            print("[WARN] Tier-A1 validation: WARN (see results_report.md)")
        else:
            status = "fail"
            ok = False
            print(f"[FAIL] Tier-A1 validation: FAIL (exit code {p.returncode}). See logs/70_validate_tiera1.log and results_report.md")

        manifest["validation_status"] = status
        write_manifest()

        # Copy validation artifacts to /content for easy download in Colab.
        try:
            if os.path.isdir("/content"):
                for fn in ["results_report.md", "results_summary.json"]:
                    src = os.path.join(work, fn)
                    if os.path.exists(src):
                        shutil.copy2(src, os.path.join("/content", fn))
                print("[INFO] Copied validation artifacts to /content/results_report.md and /content/results_summary.json")
        except Exception as e:
            print(f"[WARN] Could not copy validation artifacts to /content: {e}")

        return {"ok": ok, "validation_status": status, "validator_exit_code": p.returncode}

    step("Validate Tier-A1 outputs", run_validator, continue_on_failure=True)

    def bundle():
        write_manifest()

        bundle_path = os.path.join(work, "bundle_edcl_tiera1.zip")
        if os.path.exists(bundle_path):
            os.remove(bundle_path)

        include_paths = [
            "manifest.json",
            "logs",
            "yamls",
            "chains",
            "results_summary.json",
            "results_report.md",
        ]

        with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for rel in include_paths:
                p = os.path.join(work, rel)
                if not os.path.exists(p):
                    continue
                if os.path.isdir(p):
                    for dp, _, fn in os.walk(p):
                        for n in fn:
                            full = os.path.join(dp, n)
                            z.write(full, arcname=os.path.relpath(full, work))
                else:
                    z.write(p, arcname=rel)

            # Also include repo-side cosmology artifacts (preflight plots, AI probe logs, validation spec, etc.).
            # We include the cosmology/paper_artifacts tree, not the root paper_artifacts.
            cpa = os.path.join(repo_root, "cosmology", "paper_artifacts")
            if os.path.exists(cpa):
                for dp, _, fn in os.walk(cpa):
                    for n in fn:
                        full = os.path.join(dp, n)
                        arc = os.path.join("repo", os.path.relpath(full, repo_root))
                        z.write(full, arcname=arc)

        manifest["bundle_path"] = bundle_path
        write_manifest()

        # Re-open the bundle and update manifest inside it with bundle_path.
        with zipfile.ZipFile(bundle_path, "a", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True))

        print("\nCreated bundle:", bundle_path)
        print("[INFO] Bundle location:", bundle_path)
        print("[INFO] In Colab: open the Files pane (left sidebar) and download the bundle from that path.")
        return {"bundle_path": bundle_path}

    step("Bundle outputs", bundle)

    print("\nAll steps completed.")
    print("Workdir:", work)

    # In referee mode, propagate validator exit code for CI-style gating.
    if args.profile == "referee":
        vcode = int(manifest.get("validator_exit_code", 0) or 0)
        return vcode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
