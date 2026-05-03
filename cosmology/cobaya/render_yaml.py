#!/usr/bin/env python3
"""
Compatibility wrapper for the legacy cosmology/cobaya/render_yaml.py path.

The canonical renderer is now:

  cosmology/scripts/render_yamls.py

Use the canonical renderer directly when possible:

  python3 cosmology/scripts/render_yamls.py \
    --class-path /path/to/class_public \
    --out-root <workdir>/chains \
    --yaml-dir <workdir>/yamls

This wrapper exists only to keep older commands from failing. It translates the
legacy --output-dir argument into the canonical --out-root argument and delegates
to cosmology/scripts/render_yamls.py.

It does not print direct MCMC-run instructions and does not require
COBAYA_PACKAGES_PATH. The corrected Tier-A1 suite runner manages Cobaya package
installation/test steps in a workdir-local environment.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List


# This file lives in <repo>/cosmology/cobaya/.
REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_RENDERER = REPO_ROOT / "cosmology" / "scripts" / "render_yamls.py"


def _run(cmd: List[str]) -> int:
    print("Delegating to canonical renderer:")
    print(" ".join(repr(c) if " " in c else c for c in cmd))
    return int(subprocess.run(cmd, cwd=str(REPO_ROOT)).returncode)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Legacy wrapper for rendering Tier-A1 Cobaya YAML templates.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Preferred current command:
  python3 cosmology/scripts/render_yamls.py \\
    --class-path /path/to/class_public \\
    --out-root <workdir>/chains \\
    --yaml-dir <workdir>/yamls

Legacy-compatible command:
  python3 cosmology/cobaya/render_yaml.py \\
    --class-path /path/to/class_public \\
    --output-dir <workdir>/chains \\
    --yaml-dir <workdir>/yamls
""",
    )
    parser.add_argument(
        "-c",
        "--class-path",
        default=os.environ.get("CLASS_PATH", ""),
        help="Path to CLASS root directory used by Cobaya classy.path.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=os.environ.get("OUTPUT_DIR", "./chains"),
        help="Legacy alias for canonical --out-root. Default: ./chains or OUTPUT_DIR.",
    )
    parser.add_argument(
        "--out-root",
        default="",
        help="Canonical output-root directory for chain outputs. Overrides --output-dir.",
    )
    parser.add_argument(
        "--templates-dir",
        default=str(REPO_ROOT / "cosmology" / "cobaya"),
        help="Directory containing *.yaml.in templates.",
    )
    parser.add_argument(
        "--yaml-dir",
        default="",
        help="Directory where rendered YAML files should be written. Recommended: <workdir>/yamls.",
    )
    parser.add_argument(
        "-t",
        "--template",
        action="append",
        default=None,
        help="Specific *.yaml.in template filename to render. Can be supplied multiple times.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Accepted for backward compatibility; canonical renderer already prints written files.",
    )

    args = parser.parse_args()

    if not CANONICAL_RENDERER.exists():
        print(f"ERROR: canonical renderer not found: {CANONICAL_RENDERER}", file=sys.stderr)
        return 1

    if not args.class_path:
        print("ERROR: CLASS path not specified. Use --class-path or set CLASS_PATH.", file=sys.stderr)
        return 1

    out_root = args.out_root or args.output_dir

    cmd = [
        sys.executable,
        str(CANONICAL_RENDERER),
        "--class-path",
        args.class_path,
        "--out-root",
        out_root,
        "--templates-dir",
        args.templates_dir,
    ]

    if args.yaml_dir:
        cmd.extend(["--yaml-dir", args.yaml_dir])

    if args.template:
        for template in args.template:
            if template.endswith(".yaml.template"):
                print(
                    "ERROR: legacy *.yaml.template files are no longer canonical. "
                    "Use a *.yaml.in template from cosmology/cobaya/ instead.",
                    file=sys.stderr,
                )
                return 1
            cmd.extend(["--template", template])

    if os.environ.get("COBAYA_PACKAGES_PATH"):
        print(
            "NOTE: COBAYA_PACKAGES_PATH is set, but this renderer does not require it. "
            "The Tier-A1 suite runner manages Cobaya package handling separately."
        )

    return _run(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
