#!/usr/bin/env python3
"""
Compatibility wrapper for legacy Colab Tier-A validation commands.

This file is intentionally no longer a separate Tier-A workflow. It delegates to
canonical scripts so Colab, shell, and local workflows cannot drift apart.

Canonical full-suite runner:
  cosmology/scripts/run_tiera1_lateonly_suite.py

Canonical chain-file analyzer:
  cosmology/scripts/analyze_chains.py

Preferred Colab guide:
  docs/COLAB_GUIDE.md

Legacy examples still supported:
  python COLAB_TIER_A_VALIDATION.py --validate-only --chains-dir ./chains
  python COLAB_TIER_A_VALIDATION.py --full-run --class-path ./class_public

Recommended current commands:
  python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile iterate --skip-mcmc --no-validate
  python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile iterate
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List


REPO_ROOT = Path(__file__).resolve().parent


def _run(cmd: List[str]) -> int:
    print("\nDelegating to canonical command:")
    print(" ".join(repr(c) if " " in c else c for c in cmd))
    print()
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT))
    return int(proc.returncode)


def _existing_file(path: Path, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"ERROR: {label} not found: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Legacy compatibility wrapper for Tier-A1 EDCL validation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Preferred current workflow:
  python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile iterate --skip-mcmc --no-validate
  python3 cosmology/scripts/run_tiera1_lateonly_suite.py --profile iterate

Legacy-compatible examples:
  python COLAB_TIER_A_VALIDATION.py --validate-only --chains-dir ./chains
  python COLAB_TIER_A_VALIDATION.py --full-run --class-path ./class_public
""",
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--validate-only",
        action="store_true",
        help="Analyze existing chain files by delegating to cosmology/scripts/analyze_chains.py.",
    )
    mode.add_argument(
        "--full-run",
        action="store_true",
        help="Run the corrected Tier-A1 suite by delegating to run_tiera1_lateonly_suite.py.",
    )

    parser.add_argument(
        "-d",
        "--chains-dir",
        default="./chains",
        help="Legacy chain directory for --validate-only. For --full-run, use --work-dir instead.",
    )
    parser.add_argument(
        "-c",
        "--class-path",
        default="",
        help="Optional existing EDCL-patched CLASS path for --full-run.",
    )
    parser.add_argument(
        "-p",
        "--cobaya-packages",
        default="",
        help="Legacy argument retained for compatibility. The corrected runner uses a workdir-local package dir.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="",
        help="Output JSON for --validate-only. Default: tierA1_chain_verification.json.",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Forward --plot to analyze_chains.py in --validate-only mode.",
    )
    parser.add_argument(
        "--profile",
        default="iterate",
        choices=["iterate", "smoke", "referee"],
        help="Profile for --full-run. Default: iterate.",
    )
    parser.add_argument(
        "--work-dir",
        default="",
        help="Optional workdir for --full-run.",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=0,
        help="Forward as --mcmc-max-samples for --full-run when >0.",
    )
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="For --full-run, run setup/init checks only: forwards --skip-mcmc --no-validate.",
    )
    parser.add_argument("--skip-apt", action="store_true", help="Forward to full-suite runner.")
    parser.add_argument("--skip-pip", action="store_true", help="Forward to full-suite runner.")
    parser.add_argument("--skip-cobaya-install", action="store_true", help="Forward to full-suite runner.")
    parser.add_argument("--skip-mcmc", action="store_true", help="Forward to full-suite runner.")
    parser.add_argument("--no-validate", action="store_true", help="Forward to full-suite runner.")

    args = parser.parse_args()

    os.chdir(REPO_ROOT)

    if args.validate_only:
        analyzer = REPO_ROOT / "cosmology" / "scripts" / "analyze_chains.py"
        _existing_file(analyzer, "canonical chain analyzer")

        output = args.output or "tierA1_chain_verification.json"
        cmd = [
            sys.executable,
            str(analyzer),
            "--chains-dir",
            args.chains_dir,
            "--output",
            output,
        ]
        if args.plot:
            cmd.append("--plot")
        return _run(cmd)

    # --full-run path: delegate to corrected suite runner.
    runner = REPO_ROOT / "cosmology" / "scripts" / "run_tiera1_lateonly_suite.py"
    _existing_file(runner, "canonical Tier-A1 runner")

    if args.cobaya_packages:
        print(
            "NOTE: --cobaya-packages is retained for legacy compatibility but is not forwarded. "
            "The corrected runner uses a workdir-local cobaya_packages directory."
        )

    cmd = [sys.executable, str(runner), "--profile", args.profile]

    if args.work_dir:
        cmd.extend(["--work-dir", args.work_dir])

    if args.class_path:
        class_path = Path(args.class_path)
        if not class_path.exists():
            raise SystemExit(f"ERROR: --class-path directory not found: {class_path}")
        cmd.extend(["--skip-class-build", "--class-path", str(class_path)])

    if args.max_samples and args.max_samples > 0:
        cmd.extend(["--mcmc-max-samples", str(args.max_samples)])

    if args.setup_only:
        cmd.extend(["--skip-mcmc", "--no-validate"])

    if args.skip_apt:
        cmd.append("--skip-apt")
    if args.skip_pip:
        cmd.append("--skip-pip")
    if args.skip_cobaya_install:
        cmd.append("--skip-cobaya-install")
    if args.skip_mcmc:
        cmd.append("--skip-mcmc")
    if args.no_validate:
        cmd.append("--no-validate")

    return _run(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
