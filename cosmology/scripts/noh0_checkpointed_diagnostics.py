#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import zipfile
from typing import Any, Iterable

import numpy as np
import pandas as pd
import yaml

MATRIX = pathlib.Path(os.environ.get('NOH0_MATRIX_DIR', '/content/noh0_matrix_v3'))
BASE_YAML_DIR = MATRIX / 'yamls'
PKG = MATRIX / 'cobaya_packages'
STRICT_Q95_THRESHOLD = 0.03
STRONG_Q95_THRESHOLD = 0.02

RUN_SPECS = {
    'C1_fixedDensity_BAO_only_noH0': {
        'likelihood_mode': 'BAO',
        'seed': 62001,
        'role': 'diagnostic_ablation_bao_only',
        'claim_scope': 'diagnostic_only_not_BAO_SN_pass_evidence',
    },
    'C2_fixedDensity_SN_only_noH0': {
        'likelihood_mode': 'SN',
        'seed': 62002,
        'role': 'diagnostic_ablation_sn_only',
        'claim_scope': 'diagnostic_only_not_BAO_SN_pass_evidence',
    },
    'P1_A1b_ultra_fixed_noH0_seed61001': {
        'likelihood_mode': 'BAO_SN',
        'seed': 61001,
        'role': 'same_model_repeat_member_P1',
        'claim_scope': 'candidate_BAO_SN_fixed_density_repeat_member',
    },
    'P2_A1b_ultra_fixed_noH0_seed61002': {
        'likelihood_mode': 'BAO_SN',
        'seed': 61002,
        'role': 'same_model_repeat_member_P2',
        'claim_scope': 'candidate_BAO_SN_fixed_density_repeat_member',
    },
}

ALLOWED_LIKELIHOODS = {
    'BAO_SN': {'bao.desi_dr2.desi_bao_all', 'sn.pantheonplus'},
    'BAO': {'bao.desi_dr2.desi_bao_all'},
    'SN': {'sn.pantheonplus'},
}

FORBIDDEN_LOCAL_H0_TOKENS = [
    'H0_edcl',
    'H0.riess2020',
    'riess2020',
    'SH0ES',
    'sh0es',
]


def now_utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def safe_rel(path: pathlib.Path, root: pathlib.Path) -> str:
    try:
        return str(path.relative_to(root))
    except Exception:
        return str(path)


def run_capture(cmd: list[str], cwd: pathlib.Path | None = None) -> str:
    try:
        return subprocess.check_output(cmd, cwd=str(cwd) if cwd else None, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as e:
        return f'UNAVAILABLE: {e}'


def ensure_dirs(root: pathlib.Path) -> dict[str, pathlib.Path]:
    dirs = {
        'root': root,
        'yamls': root / 'yamls',
        'chains': root / 'chains',
        'logs': root / 'logs',
        'analysis': root / 'analysis',
        'manifests': root / 'manifests',
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def run_to_log(cmd: Iterable[Any], log_path: pathlib.Path) -> int:
    cmd_s = [str(c) for c in cmd]
    print('$', ' '.join(cmd_s))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open('w', encoding='utf-8', errors='replace') as f:
        proc = subprocess.run(cmd_s, stdout=f, stderr=subprocess.STDOUT, text=True)
    text = log_path.read_text(encoding='utf-8', errors='replace')
    print(text[-8000:])
    return int(proc.returncode)


def load_base_a1b() -> dict[str, Any]:
    path = BASE_YAML_DIR / 'A1b_noH0_fixed_strict.yaml'
    if not path.exists():
        raise FileNotFoundError(f'Missing base fixed-density YAML: {path}. Run setup/generate cells first.')
    data = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise RuntimeError(f'Base YAML did not parse to dict: {path}')
    return data


def deep_copy_jsonable(x: Any) -> Any:
    return json.loads(json.dumps(x))


def remove_speed_options(data: dict[str, Any]) -> None:
    m = data.get('sampler', {}).get('mcmc', {})
    if isinstance(m, dict):
        for key in ['measure_speeds', 'oversample_power', 'drag']:
            m.pop(key, None)


def force_fixed_density_params(data: dict[str, Any]) -> None:
    params = data.setdefault('params', {})
    params['omega_b'] = 0.02237
    params['omega_cdm'] = 0.12
    params.setdefault('H0', {'prior': {'min': 55.0, 'max': 85.0}, 'ref': 70.0, 'proposal': 0.5})
    params.setdefault('alpha_R', {'prior': {'min': 0.0, 'max': 0.2}, 'ref': 0.02, 'proposal': 0.01})
    params['H0_obs'] = {
        'derived': 'lambda H0, alpha_R: H0 * (1.0 + alpha_R * 0.7542)',
        'latex': r'H_0^{\rm obs}',
    }
    params['delta0'] = {
        'derived': 'lambda alpha_R: alpha_R * 0.7542',
        'latex': r'\delta_0',
    }


def set_likelihood(data: dict[str, Any], mode: str) -> None:
    if mode not in ALLOWED_LIKELIHOODS:
        raise ValueError(f'Unknown likelihood mode: {mode}')
    data['likelihood'] = {k: None for k in sorted(ALLOWED_LIKELIHOODS[mode])}


def set_mcmc(data: dict[str, Any], seed: int, max_samples: int, rminus1: float, rminus1_cl: float) -> None:
    data.setdefault('sampler', {}).setdefault('mcmc', {})
    remove_speed_options(data)
    m = data['sampler']['mcmc']
    m['seed'] = int(seed)
    m['max_samples'] = int(max_samples)
    m['Rminus1_stop'] = float(rminus1)
    m['Rminus1_cl_stop'] = float(rminus1_cl)
    m['Rminus1_cl_level'] = 0.95
    m['learn_proposal'] = True
    m['learn_proposal_Rminus1_max'] = 30
    m.setdefault('covmat', 'auto')


def flattened_strings(obj: Any) -> list[str]:
    out: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.append(str(k))
            out.extend(flattened_strings(v))
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            out.extend(flattened_strings(v))
    elif isinstance(obj, str):
        out.append(obj)
    else:
        # Numeric constants are not scanned for tokens.
        pass
    return out


def safety_check_noh0(data: dict[str, Any], run_id: str, likelihood_mode: str) -> dict[str, bool]:
    likelihood = data.get('likelihood', {})
    if not isinstance(likelihood, dict):
        raise RuntimeError(f'{run_id}: likelihood block is not a dict')
    actual_likes = set(str(k) for k in likelihood.keys())
    expected_likes = ALLOWED_LIKELIHOODS[likelihood_mode]

    strings = flattened_strings(data)
    full_text = '\n'.join(strings)
    extra_args = data.get('theory', {}).get('classy', {}).get('extra_args', {})
    params = data.get('params', {})

    checks = {
        'likelihood_exactly_expected': actual_likes == expected_likes,
        'no_forbidden_local_H0_tokens': not any(tok in full_text for tok in FORBIDDEN_LOCAL_H0_TOKENS),
        'edcl_on_yes': str(extra_args.get('edcl_on', '')).lower() == 'yes',
        'omega_b_fixed_numeric': isinstance(params.get('omega_b'), (int, float)) and abs(float(params.get('omega_b')) - 0.02237) < 1e-12,
        'omega_cdm_fixed_numeric': isinstance(params.get('omega_cdm'), (int, float)) and abs(float(params.get('omega_cdm')) - 0.12) < 1e-12,
        'alpha_R_nonnegative_prior': isinstance(params.get('alpha_R'), dict) and float(params['alpha_R'].get('prior', {}).get('min', -1)) >= 0.0,
        'has_H0_obs_derived_only': isinstance(params.get('H0_obs'), dict) and 'derived' in params['H0_obs'],
        'has_delta0_derived_only': isinstance(params.get('delta0'), dict) and 'derived' in params['delta0'],
    }

    print(f'Structural no-H0 safety checks for {run_id}:')
    print('  expected_likelihoods:', sorted(expected_likes))
    print('  actual_likelihoods:  ', sorted(actual_likes))
    for k, ok in checks.items():
        print(f'  {k}: {"PASS" if ok else "FAIL"}')
    if not all(checks.values()):
        raise RuntimeError(f'{run_id} failed structural no-H0 safety checks: ' + json.dumps(checks, indent=2))
    return checks


def write_run_yaml(dirs: dict[str, pathlib.Path], run_id: str, likelihood_mode: str, seed: int, max_samples: int, rminus1: float, rminus1_cl: float) -> pathlib.Path:
    data = deep_copy_jsonable(load_base_a1b())
    set_likelihood(data, likelihood_mode)
    force_fixed_density_params(data)
    set_mcmc(data, seed, max_samples, rminus1, rminus1_cl)
    data['output'] = str(dirs['chains'] / run_id)
    data.setdefault('debug_notes', {})['diagnostic_role'] = RUN_SPECS.get(run_id, {}).get('role', 'unknown')
    data.setdefault('debug_notes', {})['claim_scope'] = RUN_SPECS.get(run_id, {}).get('claim_scope', 'unknown')
    checks = safety_check_noh0(data, run_id, likelihood_mode)
    out = dirs['yamls'] / f'{run_id}.yaml'
    out.write_text(yaml.safe_dump(data, sort_keys=False, width=1000), encoding='utf-8')
    (dirs['manifests'] / f'{run_id}.safety_checks.json').write_text(json.dumps(checks, indent=2), encoding='utf-8')
    return out


def chain_file_candidates(prefix: str, dirs: dict[str, pathlib.Path]) -> list[pathlib.Path]:
    files = sorted(dirs['chains'].glob(prefix + '*.txt'))
    # Cobaya MCMC chains are usually <prefix>.1.txt, <prefix>.2.txt, etc.; keep only nonempty text files.
    out = [p for p in files if p.is_file() and p.stat().st_size > 0]
    return out


def load_chain_file(path: pathlib.Path) -> pd.DataFrame:
    header: list[str] | None = None
    rows: list[list[float]] = []
    with path.open('r', encoding='utf-8', errors='replace') as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            if s.startswith('#'):
                parts = s.lstrip('#').strip().split()
                if 'weight' in parts or 'weights' in parts or 'alpha_R' in parts or 'chi2' in parts:
                    header = parts
                continue
            if header is None:
                continue
            vals = s.split()
            if len(vals) != len(header):
                continue
            try:
                rows.append([float(x) for x in vals])
            except ValueError:
                continue
    if header is None or not rows:
        raise RuntimeError(f'Could not parse chain: {path}')
    df = pd.DataFrame(rows, columns=header)
    df['__chain_file__'] = str(path)
    return df


def load_chains(files: list[pathlib.Path]) -> pd.DataFrame:
    if not files:
        raise RuntimeError('No chain files supplied')
    dfs = [load_chain_file(p) for p in files]
    # Keep common columns plus provenance. Cobaya columns should be identical across same-model chains.
    common = set(dfs[0].columns)
    for d in dfs[1:]:
        common &= set(d.columns)
    common.add('__chain_file__')
    ordered = [c for c in dfs[0].columns if c in common]
    return pd.concat([d[ordered].copy() for d in dfs], ignore_index=True)


def weights_from_df(df: pd.DataFrame) -> np.ndarray:
    for c in ['weight', 'weights']:
        if c in df.columns:
            w = df[c].to_numpy(float)
            w[~np.isfinite(w)] = 0.0
            w[w < 0] = 0.0
            return w
    return np.ones(len(df), dtype=float)


def weighted_quantile(x: np.ndarray, q: float, w: np.ndarray) -> float | None:
    x = np.asarray(x, float)
    w = np.asarray(w, float)
    ok = np.isfinite(x) & np.isfinite(w) & (w >= 0)
    x = x[ok]
    w = w[ok]
    if len(x) == 0:
        return None
    if float(np.sum(w)) <= 0.0:
        return float(np.quantile(x, q))
    order = np.argsort(x)
    xs = x[order]
    ws = w[order]
    cdf = np.cumsum(ws) / np.sum(ws)
    idx = int(np.searchsorted(cdf, q, side='left'))
    idx = min(max(idx, 0), len(xs) - 1)
    return float(xs[idx])


def ess(weights: np.ndarray) -> float:
    w = np.asarray(weights, float)
    w = w[np.isfinite(w) & (w > 0)]
    if len(w) == 0:
        return 0.0
    return float((np.sum(w) ** 2) / np.sum(w ** 2))


def chi2_column(df: pd.DataFrame) -> str | None:
    if 'chi2' in df.columns:
        return 'chi2'
    component_cols = [c for c in df.columns if c.startswith('chi2__')]
    if component_cols:
        df['chi2_total_reconstructed'] = df[component_cols].sum(axis=1)
        return 'chi2_total_reconstructed'
    return None


def summarize_dataframe(label: str, df: pd.DataFrame, chain_files: list[pathlib.Path], role: str = '') -> dict[str, Any]:
    out: dict[str, Any] = {
        'label': label,
        'status': 'parsed',
        'role': role,
        'n_chain_files': int(len(chain_files)),
        'chain_files': [str(p) for p in chain_files],
        'rows': int(len(df)),
    }
    w = weights_from_df(df)
    out['sum_weights'] = float(np.sum(w))
    out['ess'] = ess(w)
    out['ess_over_rows'] = float(out['ess'] / max(len(df), 1))

    if 'alpha_R' in df.columns:
        alpha = df['alpha_R'].to_numpy(float)
        finite = np.isfinite(alpha) & np.isfinite(w) & (w >= 0)
        alpha_f = alpha[finite]
        w_f = w[finite]
        out['q16_alpha_R'] = weighted_quantile(alpha_f, 0.16, w_f)
        out['q50_alpha_R'] = weighted_quantile(alpha_f, 0.50, w_f)
        out['q84_alpha_R'] = weighted_quantile(alpha_f, 0.84, w_f)
        out['q95_alpha_R'] = weighted_quantile(alpha_f, 0.95, w_f)
        out['unweighted_q95_alpha_R'] = float(np.quantile(alpha_f, 0.95)) if len(alpha_f) else None
        out['P_alpha_R_lt_0p03'] = float(np.sum(w_f[alpha_f < STRICT_Q95_THRESHOLD]) / np.sum(w_f)) if np.sum(w_f) > 0 else None
        out['P_alpha_R_gt_0p03'] = float(np.sum(w_f[alpha_f > STRICT_Q95_THRESHOLD]) / np.sum(w_f)) if np.sum(w_f) > 0 else None
        tail = alpha_f > STRICT_Q95_THRESHOLD
        out['tail_rows_alpha_R_gt_0p03'] = int(np.sum(tail))
        out['tail_sum_weights_alpha_R_gt_0p03'] = float(np.sum(w_f[tail]))
        out['tail_ess_alpha_R_gt_0p03'] = ess(w_f[tail]) if np.any(tail) else 0.0
        out['passes_strict_q95_0p03'] = bool(out['q95_alpha_R'] is not None and out['q95_alpha_R'] <= STRICT_Q95_THRESHOLD)
        out['passes_strong_q95_0p02'] = bool(out['q95_alpha_R'] is not None and out['q95_alpha_R'] <= STRONG_Q95_THRESHOLD)
        out['q95_minus_0p03'] = None if out['q95_alpha_R'] is None else float(out['q95_alpha_R'] - STRICT_Q95_THRESHOLD)

    ccol = chi2_column(df)
    if ccol:
        vals = df[ccol].to_numpy(float)
        if np.any(np.isfinite(vals)):
            idx = int(np.nanargmin(vals))
            best = df.iloc[idx]
            out['chi2_col'] = ccol
            out['best_chi2'] = float(best[ccol])
            for col in ['alpha_R', 'H0', 'omega_b', 'omega_cdm', 'H0_obs', 'delta0', 'chi2__BAO', 'chi2__SN', 'chi2__bao.desi_dr2.desi_bao_all', 'chi2__sn.pantheonplus']:
                if col in df.columns:
                    out['best_' + col.replace('.', '_')] = float(best[col])
    return out


def progress_tails(prefix: str, dirs: dict[str, pathlib.Path]) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted(dirs['chains'].glob(prefix + '*.progress')):
        lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
        out[str(p)] = '\n'.join(lines[-12:])
    return out


def summarize_prefix(prefix: str, dirs: dict[str, pathlib.Path], role: str = '') -> dict[str, Any]:
    files = chain_file_candidates(prefix, dirs)
    if not files:
        return {'label': prefix, 'status': 'no_chain_found', 'role': role, 'n_chain_files': 0}
    try:
        df = load_chains(files)
        out = summarize_dataframe(prefix, df, files, role=role)
        tails = progress_tails(prefix, dirs)
        if tails:
            out['progress_tails'] = tails
        return out
    except Exception as e:
        return {'label': prefix, 'status': 'parse_failed', 'error': str(e), 'role': role, 'chain_files': [str(p) for p in files]}


def summarize_combined_p1p2(dirs: dict[str, pathlib.Path]) -> dict[str, Any]:
    prefixes = ['P1_A1b_ultra_fixed_noH0_seed61001', 'P2_A1b_ultra_fixed_noH0_seed61002']
    files: list[pathlib.Path] = []
    found_prefixes: list[str] = []
    for prefix in prefixes:
        fs = chain_file_candidates(prefix, dirs)
        if fs:
            found_prefixes.append(prefix)
            files.extend(fs)
    if len(found_prefixes) < 2:
        return {
            'label': 'COMBINED_P1P2_A1b_ultra_fixed_noH0',
            'status': 'needs_both_P1_and_P2',
            'found_prefixes': found_prefixes,
            'n_chain_files': len(files),
            'interpretation': 'Do not claim a combined same-model pass unless both P1 and P2 are present and safety-checked.',
        }
    df = load_chains(files)
    out = summarize_dataframe('COMBINED_P1P2_A1b_ultra_fixed_noH0', df, files, role='same_model_combined_P1P2_candidate_gate')
    out['found_prefixes'] = found_prefixes
    out['interpretation'] = 'This is the only candidate combined fixed-density BAO+SN no-H0 q95 gate in this notebook. BAO-only/SN-only ablations remain diagnostic only.'
    return out


def write_environment_files(dirs: dict[str, pathlib.Path]) -> None:
    freeze = run_capture([sys.executable, '-m', 'pip', 'freeze'])
    (dirs['manifests'] / 'pip_freeze.txt').write_text(freeze + '\n', encoding='utf-8')
    env = {
        'created_utc': now_utc(),
        'python': sys.version,
        'executable': sys.executable,
        'platform': platform.platform(),
        'cwd': os.getcwd(),
        'cobaya_run': shutil.which('cobaya-run'),
        'cobaya_install': shutil.which('cobaya-install'),
        'repo_commit': run_capture(['git', 'rev-parse', 'HEAD']),
        'repo_status_short': run_capture(['git', 'status', '--short']),
    }
    (dirs['manifests'] / 'environment.json').write_text(json.dumps(env, indent=2), encoding='utf-8')


def validation_config_snapshot() -> dict[str, Any]:
    p = pathlib.Path('cosmology/config/validation_config.yaml')
    if p.exists():
        try:
            return yaml.safe_load(p.read_text(encoding='utf-8'))
        except Exception as e:
            return {'error': str(e), 'path': str(p)}
    return {'error': 'validation_config.yaml not found', 'path': str(p)}


def write_manifest(dirs: dict[str, pathlib.Path], status_rows: list[dict[str, Any]], planned_run_ids: list[str]) -> None:
    files_to_hash: dict[str, str | None] = {}
    for folder_key in ['yamls', 'analysis']:
        for p in sorted(dirs[folder_key].rglob('*')):
            if p.is_file():
                files_to_hash[f'{folder_key}/{p.relative_to(dirs[folder_key])}'] = sha256_file(p)
    script_self = pathlib.Path(__file__)
    manifest = {
        'created_utc': now_utc(),
        'purpose': 'NOH0 fixed-density BAO/SN ablations and optional same-model P1/P2 q95 repeat',
        'claim_discipline': {
            'BAO_SN_q95_gate': 'Only BAO+SN no-H0 same-model chains can be used for strict posterior-tail pass/fail.',
            'BAO_only_SN_only': 'Diagnostic only; cannot establish a BAO+SN no-H0 pass.',
            'threshold': STRICT_Q95_THRESHOLD,
            'strong_threshold': STRONG_Q95_THRESHOLD,
        },
        'planned_run_ids': planned_run_ids,
        'status_rows': status_rows,
        'repo_commit': run_capture(['git', 'rev-parse', 'HEAD']),
        'repo_remote': run_capture(['git', 'remote', 'get-url', 'origin']),
        'script_path': str(script_self),
        'script_sha256': sha256_file(script_self),
        'validation_config_snapshot': validation_config_snapshot(),
        'file_hashes': files_to_hash,
    }
    (dirs['manifests'] / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')


def analyze(dirs: dict[str, pathlib.Path], run_ids: list[str], status_rows: list[dict[str, Any]]) -> None:
    summaries: list[dict[str, Any]] = []
    for r in run_ids:
        summaries.append(summarize_prefix(r, dirs, role=RUN_SPECS.get(r, {}).get('role', 'unknown')))
    combined = summarize_combined_p1p2(dirs)
    summaries.append(combined)

    out = {
        'created_utc': now_utc(),
        'status_rows': status_rows,
        'summaries': summaries,
        'interpretation_rules': {
            'strict_q95_pass': 'q95_alpha_R <= 0.03 using weighted quantiles over all chain files for the same model.',
            'strong_q95_pass': 'q95_alpha_R <= 0.02 using weighted quantiles.',
            'weighted_quantile_required': True,
            'BAO_SN_required_for_gate': True,
            'ablation_role': 'BAO/SN ablations diagnose the residual tail driver; they are not pass evidence for the BAO+SN no-H0 gate.',
            'same_model_repeat_rule': 'A claimed fixed-density posterior-tail pass should use same-model P1+P2 combined or explain why a single chain is sufficient.',
        },
    }
    (dirs['analysis'] / 'NOH0_CHECKPOINT_SUMMARY.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    table = pd.DataFrame(summaries)
    table.to_csv(dirs['analysis'] / 'NOH0_CHECKPOINT_TABLE.csv', index=False)

    report: list[str] = []
    report.append('# NOH0 checkpointed diagnostics report')
    report.append('')
    report.append('## Interpretation guardrails')
    report.append('')
    report.append(f'- Strict posterior-tail pass requires weighted `q95_alpha_R <= {STRICT_Q95_THRESHOLD}` on the BAO+SN no-H0 model.')
    report.append('- BAO-only and SN-only are diagnostic ablations only; they cannot by themselves establish a BAO+SN no-H0 pass.')
    report.append('- A same-model P1/P2 combined result is reported when both repeat chains are present.')
    report.append('- A pass must not be obtained by changing the threshold, tightening the alpha prior after seeing results, or selecting a favourable seed.')
    report.append('')
    report.append('## Summary table')
    report.append('')
    try:
        report.append(table.to_markdown(index=False))
    except Exception:
        report.append(table.to_string(index=False))
    report.append('')
    report.append('## Current gate logic')
    report.append('')
    for s in summaries:
        label = s.get('label')
        status = s.get('status')
        q95 = s.get('q95_alpha_R')
        pass_gate = s.get('passes_strict_q95_0p03')
        role = s.get('role', '')
        report.append(f'- `{label}` [{role}]: status={status}, q95={q95}, strict_q95_pass={pass_gate}')
    (dirs['analysis'] / 'NOH0_CHECKPOINT_REPORT.md').write_text('\n'.join(report) + '\n', encoding='utf-8')

    write_manifest(dirs, status_rows, run_ids)


def bundle(dirs: dict[str, pathlib.Path]) -> pathlib.Path:
    out = dirs['root'] / 'NOH0_CHECKPOINT_UPLOAD.zip'
    if out.exists():
        out.unlink()
    include = [('yamls', 'yamls'), ('chains', 'chains'), ('logs', 'logs'), ('analysis', 'analysis'), ('manifests', 'manifests')]
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for folder_key, arc in include:
            for p in dirs[folder_key].rglob('*'):
                if p.is_file():
                    z.write(p, f'{arc}/{p.relative_to(dirs[folder_key])}')
    return out


def delete_existing_run_files(dirs: dict[str, pathlib.Path], run_id: str) -> None:
    # v3 hotfix: do NOT delete generated YAMLs here. write_run_yaml() writes
    # <run_id>.yaml before run_one() is called; deleting yamls at this point
    # caused cobaya-install to fail with FileNotFoundError. Chain/log/analysis
    # cleanup is still safe. The YAML is overwritten by write_run_yaml() for
    # each planned run, so preserving it here does not leave stale config.
    for folder_key in ['chains', 'logs', 'analysis']:
        for p in dirs[folder_key].glob(run_id + '*'):
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                shutil.rmtree(p)


def run_one(dirs: dict[str, pathlib.Path], run_id: str, ypath: pathlib.Path, skip_existing: bool) -> dict[str, Any]:
    existing = chain_file_candidates(run_id, dirs)
    if existing and skip_existing:
        print(f'Skipping existing {run_id}: {[str(p) for p in existing]}')
        return {'run_id': run_id, 'status': 'skipped_existing', 'chains': [str(p) for p in existing], 'yaml': str(ypath)}

    delete_existing_run_files(dirs, run_id)
    if not ypath.exists():
        raise FileNotFoundError(f'{run_id}: generated YAML disappeared before install: {ypath}')
    row: dict[str, Any] = {'run_id': run_id, 'yaml': str(ypath), 'started_utc': now_utc()}

    rc = run_to_log(['cobaya-install', ypath, '-p', PKG], dirs['logs'] / f'{run_id}.install.log')
    row['install_rc'] = rc
    if rc != 0:
        row['status'] = 'install_failed'
        row['finished_utc'] = now_utc()
        return row

    rc = run_to_log(['cobaya-run', ypath, '--test', '-p', PKG], dirs['logs'] / f'{run_id}.test.log')
    row['test_rc'] = rc
    if rc != 0:
        row['status'] = 'test_failed'
        row['finished_utc'] = now_utc()
        return row

    rc = run_to_log(['cobaya-run', ypath, '-p', PKG], dirs['logs'] / f'{run_id}.run.log')
    row['run_rc'] = rc
    row['status'] = 'passed' if rc == 0 else 'run_failed'
    chains = chain_file_candidates(run_id, dirs)
    if chains:
        row['chains'] = [str(p) for p in chains]
    row['finished_utc'] = now_utc()
    return row



def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['ablations_first', 'p2_only', 'p1p2', 'all'], default='ablations_first')
    parser.add_argument('--output-root', default='/content/noh0_checkpointed')
    parser.add_argument('--skip-existing', action='store_true')
    parser.add_argument('--ablation-max-samples', type=int, default=80000)
    parser.add_argument('--p-repeat-max-samples', type=int, default=150000)
    parser.add_argument('--p2-max-samples', type=int, default=None, help='Deprecated alias; overrides --p-repeat-max-samples if supplied.')
    args = parser.parse_args()
    if args.p2_max_samples is not None:
        args.p_repeat_max_samples = args.p2_max_samples

    dirs = ensure_dirs(pathlib.Path(args.output_root))
    write_environment_files(dirs)
    print('Output root:', dirs['root'])
    print('Mode:', args.mode)
    print('Repo commit:', run_capture(['git', 'rev-parse', 'HEAD']))

    planned_specs: list[tuple[str, str, int, int, float, float]] = []
    if args.mode in ['ablations_first', 'all']:
        planned_specs.append(('C1_fixedDensity_BAO_only_noH0', 'BAO', 62001, args.ablation_max_samples, 0.005, 0.05))
        planned_specs.append(('C2_fixedDensity_SN_only_noH0', 'SN', 62002, args.ablation_max_samples, 0.005, 0.05))
    if args.mode in ['p1p2', 'all']:
        planned_specs.append(('P1_A1b_ultra_fixed_noH0_seed61001', 'BAO_SN', 61001, args.p_repeat_max_samples, 0.0015, 0.02))
        planned_specs.append(('P2_A1b_ultra_fixed_noH0_seed61002', 'BAO_SN', 61002, args.p_repeat_max_samples, 0.0015, 0.02))
    if args.mode == 'p2_only':
        planned_specs.append(('P2_A1b_ultra_fixed_noH0_seed61002', 'BAO_SN', 61002, args.p_repeat_max_samples, 0.0015, 0.02))

    planned: list[tuple[str, pathlib.Path]] = []
    for run_id, like_mode, seed, max_samples, r1, r1cl in planned_specs:
        ypath = write_run_yaml(dirs, run_id, like_mode, seed, max_samples, r1, r1cl)
        planned.append((run_id, ypath))

    run_ids = [x[0] for x in planned]
    status_rows: list[dict[str, Any]] = []
    analyze(dirs, run_ids, status_rows)
    out = bundle(dirs)
    print('Initial manifest/checkpoint bundle:', out)

    for run_id, ypath in planned:
        print('\n' + '=' * 88)
        print('RUNNING', run_id)
        print('=' * 88)
        try:
            row = run_one(dirs, run_id, ypath, args.skip_existing)
        except Exception as e:
            row = {'run_id': run_id, 'status': 'exception', 'error': repr(e), 'yaml': str(ypath), 'finished_utc': now_utc()}
        status_rows.append(row)
        analyze(dirs, run_ids, status_rows)
        out = bundle(dirs)
        print('Checkpoint bundle:', out)
        print('Size MB:', out.stat().st_size / 1024 / 1024)

    analyze(dirs, run_ids, status_rows)
    out = bundle(dirs)
    print('\nFinal checkpoint bundle:')
    print(out)
    print('Size MB:', out.stat().st_size / 1024 / 1024)
    print('Upload this file here.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
