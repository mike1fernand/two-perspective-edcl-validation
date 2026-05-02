#!/usr/bin/env python3
"""
run_tiera1_ablations.py - Generate, optionally run, and summarize Tier-A1 EDCL
likelihood-ablation configurations.

Purpose
-------
This script supports the next Hubble-mechanism validation step after the
Tier-A1 chain-component audit. It tests whether the EDCL calibration parameter
alpha_R activates specifically when the local observed-frame H0_obs likelihood
is present, and whether BAO/SN alone spuriously prefer alpha_R.

Default behavior is no-clutter and safe:
  * generated YAML files are written under an output directory, not into the
    repo source tree;
  * Cobaya is NOT launched unless --run is explicitly provided;
  * generated chains and run directories should not be committed to git.

Canonical ablations generated
-----------------------------
  edcl_bao_sn_only       : DESI BAO + PantheonPlus, no local H0_obs
  edcl_bao_h0obs         : DESI BAO + local H0_obs
  edcl_sn_h0obs          : PantheonPlus + local H0_obs
  edcl_h0obs_only        : local H0_obs only
  edcl_alphaR0_full      : DESI BAO + PantheonPlus + local H0_obs, alpha_R fixed 0

Example usage
-------------
Generate YAMLs only:

    python cosmology/scripts/run_tiera1_ablations.py \
      --class-path /path/to/class_public \
      --output-dir ./chains/tierA1_ablations \
      --dry-run

Run all generated ablations:

    export COBAYA_PACKAGES_PATH=/path/to/cobaya_packages
    python cosmology/scripts/run_tiera1_ablations.py \
      --class-path /path/to/class_public \
      --output-dir ./chains/tierA1_ablations \
      --run

Analyze already-run ablation chains:

    python cosmology/scripts/run_tiera1_ablations.py \
      --output-dir ./chains/tierA1_ablations \
      --analyze \
      --summary-json cosmology/results/tierA1_ablation_summary.json

Notes
-----
The generated EDCL configs intentionally mirror the production EDCL template:
  * edcl_on: 'yes'
  * edcl_kernel: exp
  * edcl_zeta: 0.5
  * edcl_ai: 0.0001
  * H0_obs = H0 * (1 + alpha_R * 0.7542)

Stronger Hubble-resolution wording still requires full ablation results,
robustness scans, fair baselines, and Tier-A2/Planck validation.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np


F_NORM = 0.7542
H0_LOCAL = 73.04
SIGMA_H0_LOCAL = 1.04

BAO_KEY = "bao.desi_dr2.desi_bao_all"
SN_KEY = "sn.pantheonplus"

EDCL_EXTRA_ARGS = {
    "edcl_on": "'yes'",
    "kappa_tick": "0.08333333333333333",
    "c4": "0.06",
    "log10_l0": "-20.908",
    "edcl_kernel": "exp",
    "edcl_zeta": "0.5",
    "edcl_ai": "0.0001",
}


@dataclass(frozen=True)
class Ablation:
    key: str
    description: str
    use_bao: bool
    use_sn: bool
    use_h0obs: bool
    alpha_r_fixed: Optional[float] = None

    @property
    def output_prefix(self) -> str:
        return f"ablation_{self.key}"


ABLATIONS: Tuple[Ablation, ...] = (
    Ablation(
        key="edcl_bao_sn_only",
        description="EDCL with DESI BAO + PantheonPlus only; tests whether BAO/SN alone spuriously activate alpha_R.",
        use_bao=True,
        use_sn=True,
        use_h0obs=False,
    ),
    Ablation(
        key="edcl_bao_h0obs",
        description="EDCL with DESI BAO + local observed-frame H0_obs likelihood.",
        use_bao=True,
        use_sn=False,
        use_h0obs=True,
    ),
    Ablation(
        key="edcl_sn_h0obs",
        description="EDCL with PantheonPlus + local observed-frame H0_obs likelihood.",
        use_bao=False,
        use_sn=True,
        use_h0obs=True,
    ),
    Ablation(
        key="edcl_h0obs_only",
        description="EDCL with local observed-frame H0_obs likelihood only.",
        use_bao=False,
        use_sn=False,
        use_h0obs=True,
    ),
    Ablation(
        key="edcl_alphaR0_full",
        description="EDCL full late-only likelihood with alpha_R fixed to zero; negative/control baseline for calibration channel.",
        use_bao=True,
        use_sn=True,
        use_h0obs=True,
        alpha_r_fixed=0.0,
    ),
)


PROFILE_SETTINGS = {
    "production": {
        "max_samples": 50000,
        "Rminus1_stop": 0.01,
        "Rminus1_cl_stop": 0.15,
        "learn_proposal_Rminus1_max": 30,
    },
    "medium": {
        "max_samples": 30000,
        "Rminus1_stop": 0.02,
        "Rminus1_cl_stop": 0.20,
        "learn_proposal_Rminus1_max": 30,
    },
    "quick": {
        "max_samples": 10000,
        "Rminus1_stop": 0.05,
        "Rminus1_cl_stop": 0.30,
        "learn_proposal_Rminus1_max": 20,
    },
}


def render_likelihood_block(ablation: Ablation) -> str:
    lines: List[str] = ["likelihood:"]
    if ablation.use_bao:
        lines.append(f"  {BAO_KEY}: null")
    if ablation.use_sn:
        lines.append(f"  {SN_KEY}: null")
    if ablation.use_h0obs:
        lines.extend(
            [
                "  H0_edcl:",
                (
                    "    external: \"lambda H0, alpha_R: -0.5 * "
                    f"((H0 * (1.0 + alpha_R * {F_NORM}) - {H0_LOCAL}) / {SIGMA_H0_LOCAL}) ** 2\""
                ),
            ]
        )
    if len(lines) == 1:
        raise ValueError(f"Ablation {ablation.key} has no likelihoods enabled.")
    return "\n".join(lines)


def render_theory_block(class_path: str) -> str:
    extra = [f"      {key}: {value}" for key, value in EDCL_EXTRA_ARGS.items()]
    return "\n".join(
        [
            "theory:",
            "  classy:",
            f"    path: {class_path}",
            "    extra_args:",
            *extra,
        ]
    )


def render_params_block(ablation: Ablation) -> str:
    sampled_alpha = ablation.alpha_r_fixed is None
    alpha_block = (
        "\n".join(
            [
                "  alpha_R:",
                "    prior:",
                "      min: 0.0",
                "      max: 0.25",
                "    ref: 0.08",
                "    proposal: 0.015",
                "    latex: \\alpha_R",
            ]
        )
        if sampled_alpha
        else "\n".join(
            [
                "  alpha_R:",
                f"    value: {ablation.alpha_r_fixed}",
                "    latex: \\alpha_R",
            ]
        )
    )

    return "\n".join(
        [
            "params:",
            "  omega_b:",
            "    prior:",
            "      min: 0.018",
            "      max: 0.026",
            "    ref:",
            "      dist: norm",
            "      loc: 0.02237",
            "      scale: 0.00015",
            "    proposal: 0.0001",
            "    latex: \\omega_b",
            "",
            "  omega_cdm:",
            "    prior:",
            "      min: 0.08",
            "      max: 0.16",
            "    ref:",
            "      dist: norm",
            "      loc: 0.1200",
            "      scale: 0.0012",
            "    proposal: 0.001",
            "    latex: \\omega_{cdm}",
            "",
            "  H0:",
            "    prior:",
            "      min: 60.0",
            "      max: 80.0",
            "    ref: 67.5",
            "    proposal: 0.5",
            "    latex: H_0^{\\rm theory}",
            "",
            alpha_block,
            "",
            "  H0_obs:",
            f"    derived: 'lambda H0, alpha_R: H0 * (1.0 + alpha_R * {F_NORM})'",
            "    latex: H_0^{\\rm obs}",
            "",
            "  delta0:",
            f"    derived: 'lambda alpha_R: alpha_R * {F_NORM}'",
            "    latex: \\delta_0",
        ]
    )


def render_sampler_block(profile: str, seed: int) -> str:
    settings = PROFILE_SETTINGS[profile]
    return "\n".join(
        [
            "sampler:",
            "  mcmc:",
            f"    max_samples: {settings['max_samples']}",
            f"    Rminus1_stop: {settings['Rminus1_stop']}",
            f"    Rminus1_cl_stop: {settings['Rminus1_cl_stop']}",
            "    learn_proposal: true",
            f"    learn_proposal_Rminus1_max: {settings['learn_proposal_Rminus1_max']}",
            "    measure_speeds: true",
            "    oversample_power: 0.4",
            "    drag: true",
            f"    seed: {seed}",
        ]
    )


def render_yaml(ablation: Ablation, class_path: str, output_dir: Path, profile: str, seed: int) -> str:
    return "\n\n".join(
        [
            f"# {ablation.output_prefix}.yaml",
            f"# {ablation.description}",
            "# Generated by cosmology/scripts/run_tiera1_ablations.py",
            render_likelihood_block(ablation),
            render_theory_block(class_path),
            render_params_block(ablation),
            f"output: {output_dir / ablation.output_prefix}",
            render_sampler_block(profile, seed),
            "",
        ]
    )


def write_text(path: Path, content: str, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file without --overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def selected_ablations(selection: List[str]) -> List[Ablation]:
    available = {a.key: a for a in ABLATIONS}
    if not selection or selection == ["all"]:
        return list(ABLATIONS)
    missing = [key for key in selection if key not in available]
    if missing:
        raise ValueError(
            "Unknown ablation(s): "
            + ", ".join(missing)
            + ". Available: "
            + ", ".join(sorted(available))
        )
    return [available[key] for key in selection]


def write_configs(
    ablations: List[Ablation],
    class_path: str,
    output_dir: Path,
    profile: str,
    seed: int,
    overwrite: bool,
) -> Dict[str, object]:
    yaml_dir = output_dir / "yaml"
    yaml_dir.mkdir(parents=True, exist_ok=True)
    generated = []
    for ablation in ablations:
        yaml_path = yaml_dir / f"{ablation.output_prefix}.yaml"
        yaml_text = render_yaml(ablation, class_path, output_dir, profile, seed)
        write_text(yaml_path, yaml_text, overwrite=overwrite)
        generated.append(
            {
                "key": ablation.key,
                "description": ablation.description,
                "yaml": str(yaml_path),
                "output_prefix": str(output_dir / ablation.output_prefix),
                "likelihoods": {
                    "bao": ablation.use_bao,
                    "pantheonplus": ablation.use_sn,
                    "h0obs": ablation.use_h0obs,
                },
                "alpha_R_fixed": ablation.alpha_r_fixed,
            }
        )

    manifest = {
        "artifact_type": "tierA1_ablation_manifest",
        "profile": profile,
        "seed": seed,
        "class_path": class_path,
        "output_dir": str(output_dir),
        "generated_configs": generated,
        "claim_boundary": (
            "Ablations test the H0_obs mechanism driver. They do not by themselves "
            "establish decisive full Hubble-tension resolution."
        ),
    }
    manifest_path = output_dir / "tierA1_ablation_manifest.json"
    write_text(manifest_path, json.dumps(manifest, indent=2) + "\n", overwrite=True)
    return manifest


def validate_run_environment(class_path: str) -> None:
    if not Path(class_path).is_dir():
        raise SystemExit(f"ERROR: CLASS path not found: {class_path}")
    if shutil.which("cobaya-run") is None:
        raise SystemExit("ERROR: cobaya-run not found on PATH. Install Cobaya first.")
    packages_path = os.environ.get("COBAYA_PACKAGES_PATH", "")
    if not packages_path:
        raise SystemExit("ERROR: COBAYA_PACKAGES_PATH is not set.")
    if not Path(packages_path).exists():
        raise SystemExit(f"ERROR: COBAYA_PACKAGES_PATH does not exist: {packages_path}")


def run_configs(manifest: Dict[str, object]) -> None:
    configs = manifest["generated_configs"]
    assert isinstance(configs, list)
    for item in configs:
        yaml_path = item["yaml"]
        print(f"\nRunning Cobaya: {yaml_path}")
        subprocess.run(["cobaya-run", str(yaml_path), "-f"], check=True)


def load_chain(path: Path) -> Tuple[np.ndarray, List[str]]:
    with path.open("r", encoding="utf-8") as f:
        header_line = f.readline()
    header = header_line.strip().lstrip("#").split()
    data = np.loadtxt(path)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    return data, header


def weighted_stats(values: np.ndarray, weights: np.ndarray) -> Dict[str, float]:
    mean = float(np.average(values, weights=weights))
    variance = float(np.average((values - mean) ** 2, weights=weights))
    std = float(np.sqrt(variance))

    order = np.argsort(values)
    sorted_values = values[order]
    sorted_weights = weights[order]
    cumsum = np.cumsum(sorted_weights)
    cumsum /= cumsum[-1]

    def q(prob: float) -> float:
        return float(sorted_values[np.searchsorted(cumsum, prob)])

    return {
        "mean": mean,
        "std": std,
        "q16": q(0.16),
        "median": q(0.50),
        "q84": q(0.84),
    }


def preferred_component_columns(header: List[str]) -> List[str]:
    # Avoid double-counting duplicate compact and fully-qualified chi2 columns.
    preferred = []
    for name in ("chi2__BAO", "chi2__SN", "chi2__H0_edcl", "chi2__H0.riess2020"):
        if name in header:
            preferred.append(name)

    # Fallbacks for Cobaya names if compact aliases are absent.
    if "chi2__BAO" not in header:
        preferred.extend([h for h in header if h.startswith("chi2__bao.")])
    if "chi2__SN" not in header:
        preferred.extend([h for h in header if h.startswith("chi2__sn.")])
    if "chi2__H0_edcl" not in header and "chi2__H0.riess2020" not in header:
        preferred.extend([h for h in header if h.startswith("chi2__H0")])

    seen = set()
    unique = []
    for name in preferred:
        if name not in seen:
            unique.append(name)
            seen.add(name)
    return unique


def find_chain_file(output_dir: Path, ablation: Ablation) -> Optional[Path]:
    candidates = [
        output_dir / f"{ablation.output_prefix}.1.txt",
        output_dir / ablation.output_prefix / f"{ablation.output_prefix}.1.txt",
    ]
    candidates.extend(sorted(output_dir.glob(f"{ablation.output_prefix}*.1.txt")))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def analyze_ablation_chain(chain_path: Path, ablation: Ablation) -> Dict[str, object]:
    data, header = load_chain(chain_path)
    if "weight" not in header:
        raise ValueError(f"Missing weight column in {chain_path}")
    weights = data[:, header.index("weight")]

    out: Dict[str, object] = {
        "key": ablation.key,
        "description": ablation.description,
        "chain": str(chain_path),
        "n_rows": int(data.shape[0]),
        "effective_samples": float(np.sum(weights)),
        "parameters": {},
    }

    params = ["omega_b", "omega_cdm", "H0", "alpha_R", "H0_obs", "delta0"]
    for param in params:
        if param in header:
            out["parameters"][param] = weighted_stats(data[:, header.index(param)], weights)

    if "chi2" in header:
        chi2 = data[:, header.index("chi2")]
        best_idx = int(np.argmin(chi2))
        out["chi2_best"] = float(chi2[best_idx])
        out["best_row_index"] = best_idx

        components = {}
        for column in preferred_component_columns(header):
            components[column] = float(data[best_idx, header.index(column)])
        out["best_fit_components"] = components
        out["best_fit_component_sum"] = float(sum(components.values())) if components else None
        if components:
            out["best_fit_component_sum_minus_total"] = float(sum(components.values()) - chi2[best_idx])

    return out


def analyze_outputs(output_dir: Path, ablations: List[Ablation], summary_json: Path, overwrite: bool) -> Dict[str, object]:
    results = []
    missing = []
    for ablation in ablations:
        chain_path = find_chain_file(output_dir, ablation)
        if chain_path is None:
            missing.append(ablation.key)
            continue
        results.append(analyze_ablation_chain(chain_path, ablation))

    summary = {
        "artifact_type": "tierA1_ablation_summary",
        "output_dir": str(output_dir),
        "available_results": results,
        "missing_chain_outputs": missing,
        "interpretation_guardrail": (
            "Use these ablations to assess whether alpha_R activation is driven by "
            "the local H0_obs likelihood. Do not use them alone for decisive "
            "Hubble-resolution language."
        ),
    }
    write_text(summary_json, json.dumps(summary, indent=2) + "\n", overwrite=overwrite)
    return summary


def print_manifest(manifest: Dict[str, object]) -> None:
    print("\nGenerated Tier-A1 ablation YAMLs:")
    for item in manifest["generated_configs"]:
        print(f"  - {item['key']}: {item['yaml']}")
    print(f"\nManifest: {Path(manifest['output_dir']) / 'tierA1_ablation_manifest.json'}")
    print("\nTo run manually:")
    for item in manifest["generated_configs"]:
        print(f"  cobaya-run {item['yaml']} -f")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate, optionally run, and summarize Tier-A1 EDCL likelihood ablations."
    )
    parser.add_argument(
        "--class-path",
        default=os.environ.get("CLASS_PATH", "/path/to/class_public"),
        help="Path to CLASS with EDCL patch. Required to actually run Cobaya; used literally in generated YAMLs.",
    )
    parser.add_argument(
        "--output-dir",
        default="./chains/tierA1_ablations",
        help="Output directory for generated YAMLs and Cobaya chains.",
    )
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILE_SETTINGS),
        default="production",
        help="Sampler profile for generated YAMLs.",
    )
    parser.add_argument("--seed", type=int, default=42, help="MCMC seed.")
    parser.add_argument(
        "--ablation",
        action="append",
        default=None,
        help="Ablation key to generate/analyze. Repeat for multiple, or omit/use 'all'.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate YAMLs and print commands without running Cobaya. This is also the default unless --run is set.",
    )
    parser.add_argument("--run", action="store_true", help="Run cobaya-run for each generated YAML.")
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze available ablation chain files in --output-dir and write a summary JSON.",
    )
    parser.add_argument(
        "--summary-json",
        default="tierA1_ablation_summary.json",
        help="Path for ablation summary JSON when --analyze is used.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite generated YAMLs/summary files.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    ablations = selected_ablations(args.ablation or ["all"])

    manifest = write_configs(
        ablations=ablations,
        class_path=args.class_path,
        output_dir=output_dir,
        profile=args.profile,
        seed=args.seed,
        overwrite=args.overwrite,
    )
    print_manifest(manifest)

    if args.run:
        validate_run_environment(args.class_path)
        run_configs(manifest)
    else:
        print("\nCobaya was not run. Use --run to launch MCMC after checking the YAMLs.")

    if args.analyze:
        summary_path = Path(args.summary_json)
        summary = analyze_outputs(output_dir, ablations, summary_path, overwrite=True)
        print(f"\nWrote ablation summary: {summary_path}")
        if summary["missing_chain_outputs"]:
            print("Missing chain outputs for: " + ", ".join(summary["missing_chain_outputs"]))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
