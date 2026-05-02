#!/usr/bin/env python3
"""
Render Cobaya YAML templates by substituting __CLASS_PATH__ and __OUTPUT_DIR__.

This avoids assumptions about where CLASS is installed and where chains should go.

Default behavior is backward-compatible: rendered YAMLs are written next to the
*.yaml.in templates. To avoid dirtying the source tree, pass --yaml-dir and the
rendered YAMLs will be written there instead.
"""
from __future__ import annotations

import argparse
import os
import pathlib
from typing import Iterable, List


def render_text(template_text: str, class_path: str, output_dir: str) -> str:
    """Render one template string."""
    return (
        template_text
        .replace("__CLASS_PATH__", class_path)
        .replace("__OUTPUT_DIR__", output_dir)
    )


def render_file(src: str, dst: str, class_path: str, output_dir: str) -> None:
    """Render one YAML template file to a destination path."""
    with open(src, "r", encoding="utf-8") as f:
        template_text = f.read()

    rendered = render_text(template_text, class_path, output_dir)

    dst_path = pathlib.Path(dst)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    with dst_path.open("w", encoding="utf-8") as f:
        f.write(rendered)


def _discover_templates(templates_dir: pathlib.Path, names: Iterable[str] | None = None) -> List[pathlib.Path]:
    """Return sorted *.yaml.in templates, optionally restricted by filename."""
    if names:
        out: List[pathlib.Path] = []
        for name in names:
            p = templates_dir / name
            if not p.exists():
                raise FileNotFoundError(f"Template not found: {p}")
            if not p.name.endswith(".yaml.in"):
                raise ValueError(f"Template must end with .yaml.in: {p}")
            out.append(p)
        return sorted(out)

    return sorted(templates_dir.glob("*.yaml.in"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--class-path",
        required=True,
        help="Path to the CLASS root directory used by Cobaya classy.path.",
    )
    ap.add_argument(
        "--out-root",
        required=True,
        help="Directory where chain outputs will be written.",
    )
    ap.add_argument(
        "--templates-dir",
        default=os.path.join("cosmology", "cobaya"),
        help="Directory containing *.yaml.in templates.",
    )
    ap.add_argument(
        "--yaml-dir",
        default="",
        help=(
            "Directory where rendered YAML files should be written. "
            "Default: write next to the templates for backward compatibility."
        ),
    )
    ap.add_argument(
        "--template",
        action="append",
        default=None,
        help=(
            "Specific template filename to render, e.g. edcl_cosmo_lateonly.yaml.in. "
            "Can be supplied multiple times. Default: render all *.yaml.in files."
        ),
    )
    args = ap.parse_args()

    templates_dir = pathlib.Path(args.templates_dir)
    if not templates_dir.is_dir():
        raise FileNotFoundError(f"Templates directory not found: {templates_dir}")

    yaml_dir = pathlib.Path(args.yaml_dir) if args.yaml_dir else templates_dir

    out_root = pathlib.Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    yaml_dir.mkdir(parents=True, exist_ok=True)

    templates = _discover_templates(templates_dir, args.template)
    if not templates:
        raise FileNotFoundError(f"No *.yaml.in templates found in: {templates_dir}")

    for template in templates:
        name = template.name.replace(".yaml.in", ".yaml")
        dst = yaml_dir / name
        output_dir = str(out_root / name.replace(".yaml", ""))
        render_file(str(template), str(dst), args.class_path, output_dir)
        print(f"Wrote {dst} (output: {output_dir})")


if __name__ == "__main__":
    main()
