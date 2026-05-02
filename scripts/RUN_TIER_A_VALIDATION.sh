#!/usr/bin/env bash
#
# scripts/RUN_TIER_A_VALIDATION.sh
#
# Compatibility wrapper for the legacy scripts/ Tier-A entry point.
#
# This file intentionally does not maintain a separate YAML-generation or
# cobaya-run workflow. It delegates to the canonical Tier-A1 suite runner:
#
#   cosmology/scripts/run_tiera1_lateonly_suite.py
#
# Keeping this file as a thin wrapper prevents drift between:
#   - README / Colab instructions
#   - root RUN_TIER_A_VALIDATION.sh
#   - scripts/RUN_TIER_A_VALIDATION.sh
#   - the Python suite runner
#
# Usage:
#   bash scripts/RUN_TIER_A_VALIDATION.sh
#       Clone, patch, build CLASS, render YAMLs under the workdir, run Cobaya,
#       validate, and bundle.
#
#   bash scripts/RUN_TIER_A_VALIDATION.sh /path/to/class_public
#       Use an existing EDCL-patched CLASS build.
#
# Environment variables:
#   PROFILE=iterate|smoke|referee     Default: iterate
#   WORK_DIR=/path/to/workdir         Default: timestamped workdir chosen by Python runner
#   OUTPUT_DIR=/path/to/workdir       Legacy alias for WORK_DIR if WORK_DIR is unset
#   CLASS_PATH=/path/to/class_public  Optional existing patched CLASS path
#   SKIP_APT=1                        Forward --skip-apt
#   SKIP_PIP=1                        Forward --skip-pip
#   SKIP_COBAYA_INSTALL=1             Forward --skip-cobaya-install
#   SKIP_MCMC=1                       Forward --skip-mcmc
#   NO_VALIDATE=1                     Forward --no-validate
#   MCMC_MAX_SAMPLES=N                Forward --mcmc-max-samples N
#
# Legacy note:
#   COBAYA_PACKAGES_PATH is not required by this wrapper. The canonical Python
#   runner uses a workdir-local cobaya_packages directory.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

RUNNER="$REPO_ROOT/cosmology/scripts/run_tiera1_lateonly_suite.py"

if [[ ! -f "$RUNNER" ]]; then
    echo "ERROR: canonical Tier-A1 suite runner not found: $RUNNER" >&2
    exit 1
fi

if [[ -n "${1:-}" ]]; then
    CLASS_PATH="$1"
fi

PROFILE="${PROFILE:-iterate}"
WORK_DIR="${WORK_DIR:-${OUTPUT_DIR:-}}"

case "$PROFILE" in
    iterate|smoke|referee)
        ;;
    *)
        echo "ERROR: PROFILE must be one of: iterate, smoke, referee" >&2
        echo "Current PROFILE: $PROFILE" >&2
        exit 1
        ;;
esac

CMD=(python3 "$RUNNER" --profile "$PROFILE")

if [[ -n "$WORK_DIR" ]]; then
    CMD+=(--work-dir "$WORK_DIR")
fi

if [[ -n "${CLASS_PATH:-}" ]]; then
    if [[ ! -d "$CLASS_PATH" ]]; then
        echo "ERROR: CLASS_PATH directory not found: $CLASS_PATH" >&2
        exit 1
    fi
    CMD+=(--skip-class-build --class-path "$CLASS_PATH")
fi

if [[ "${SKIP_APT:-0}" == "1" ]]; then
    CMD+=(--skip-apt)
fi

if [[ "${SKIP_PIP:-0}" == "1" ]]; then
    CMD+=(--skip-pip)
fi

if [[ "${SKIP_COBAYA_INSTALL:-0}" == "1" ]]; then
    CMD+=(--skip-cobaya-install)
fi

if [[ "${SKIP_MCMC:-0}" == "1" ]]; then
    CMD+=(--skip-mcmc)
fi

if [[ "${NO_VALIDATE:-0}" == "1" ]]; then
    CMD+=(--no-validate)
fi

if [[ -n "${MCMC_MAX_SAMPLES:-}" ]]; then
    if ! [[ "$MCMC_MAX_SAMPLES" =~ ^[0-9]+$ ]]; then
        echo "ERROR: MCMC_MAX_SAMPLES must be a non-negative integer." >&2
        echo "Current MCMC_MAX_SAMPLES: $MCMC_MAX_SAMPLES" >&2
        exit 1
    fi
    CMD+=(--mcmc-max-samples "$MCMC_MAX_SAMPLES")
fi

echo "=================================================="
echo "EDCL TIER-A1 LATE-ONLY VALIDATION"
echo "=================================================="
echo ""
echo "Wrapper: scripts/RUN_TIER_A_VALIDATION.sh"
echo "Runner:  $RUNNER"
echo "Profile: $PROFILE"
if [[ -n "$WORK_DIR" ]]; then
    echo "Workdir: $WORK_DIR"
else
    echo "Workdir: Python runner default"
fi
if [[ -n "${CLASS_PATH:-}" ]]; then
    echo "CLASS:   existing patched CLASS at $CLASS_PATH"
else
    echo "CLASS:   Python runner will clone upstream CLASS, apply cosmology/patches/class_edcl.patch, and build classy"
fi
echo ""

if [[ -n "${COBAYA_PACKAGES_PATH:-}" ]]; then
    echo "NOTE: COBAYA_PACKAGES_PATH is set, but this wrapper does not require it."
    echo "      The canonical Python runner uses a workdir-local cobaya_packages directory."
    echo ""
fi

printf 'Command:'
printf ' %q' "${CMD[@]}"
printf '\n\n'

exec "${CMD[@]}"
