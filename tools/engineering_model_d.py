"""Modelo D: correcciones HR y QVoice conjuntas sobre C archivado.

Las filas persona-snapshot, llaves efímeras y predicciones sólo existen en RAM.
El script persiste parámetros y resultados agregados bajo modo ``presentation``.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import itertools
from pathlib import Path
import secrets
import shutil
import sys
import time

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.special import expit
from sklearn.metrics import average_precision_score
from sklearn.preprocessing import OneHotEncoder
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

import engineering_model_c as base
import engineering_model_c_qvoice as cq
import engineering_c_group_selection as groups
import compare_engineering_bc_priority as prior
import qvoice_calibrated_model as qmodel
import qvoice_horizon_calibration as horizon
from qvoice_model_data import load_config

write = groups.write
DEFAULT = ROOT / 'config/engineering_model_d_20261010.json'
VALID_Q = {'v0', 'v1', '<50', '50–69', '70–79', '80–89', '90–99', '100'}


def log(message):
    base.log(message)


def directory_hashes(paths):
    return {str(p.relative_to(ROOT)): base.sha(p) for folder in paths
            for p in (ROOT / folder).rglob('*') if p.is_file()}


def load_frame(config, cconfig, salt):
    authorization = base.read(ROOT / config['authorization'])
    if authorization['status'] != 'approved' or authorization['non_negotiable_controls']['disk_cache_of_rows']:
        raise RuntimeError('La autorización de entrenamiento en RAM no está vigente.')
    template = (ROOT / config['base_query']).read_text(encoding='utf-8')
    expected = {'snapshot_date', 'person_key', 'label_end', 'y_next', 'y_6m',
                'company_tenure_band', 'tenure_julia_band', 'same_episode_2024',
                'same_episode_2025', 'same_episode_2026', 'voluntary_event_days'} | set(base.raw_features(cconfig))
    parts = []
    with base.db.connect() as conn:
        conn.set_session(readonly=True, autocommit=True)
        for year in (2025, 2026):
            tick = time.perf_counter()
            start = max(f'{year}-01-01', config['training_start'])
            end = min(f'{year}-12-31', config['knowledge_boundary'])
            sql = base.db.validate_readonly(template.replace('__PERIOD_START__', start)
                .replace('__PERIOD_END__', end).replace('__RUN_SALT__', salt))
            with conn.cursor() as cursor:
                cursor.execute(sql)
                columns = [c[0] for c in cursor.description]
                if set(columns) != expected or set(columns) & base.db.SENSITIVE_OUTPUT_COLUMNS:
                    raise RuntimeError('La consulta base de D no cumple el contrato de columnas.')
                while True:
                    rows = cursor.fetchmany(50000)
                    if not rows:
                        break
                    part = pd.DataFrame(rows, columns=columns).drop(columns=['company_tenure_band', 'tenure_julia_band'])
                    parts.append(part)
            log(f'D: carga base {year} en RAM: {time.perf_counter()-tick:.1f} s.')
    frame = pd.concat(parts, ignore_index=True)
    del parts, sql
    for field in ('snapshot_date', 'label_end'):
        frame[field] = pd.to_datetime(frame[field])
    for field in base.raw_features(cconfig):
        frame[field] = frame[field].astype('category')
    frame['calendar_month'] = frame.snapshot_date.dt.month.astype(str).astype('category')
    frame['r6_end'] = frame.snapshot_date + pd.DateOffset(months=6)
    frame['voluntary_event_days'] = pd.to_numeric(frame.voluntary_event_days)
    event_bin = np.full(len(frame), 7, dtype=np.int8)
    event_days = frame.voluntary_event_days.to_numpy(float)
    for month in range(6, 0, -1):
        limit = ((frame.snapshot_date + pd.DateOffset(months=month)) - frame.snapshot_date).dt.days.to_numpy()
        event_bin[(event_days > 0) & (event_days <= limit)] = month
    frame['event_bin'] = event_bin
    mature = frame.y_6m.notna()
    if not np.array_equal((event_bin[mature] <= 6).astype(int), frame.loc[mature, 'y_6m'].to_numpy(int)):
        raise RuntimeError('La etiqueta de supervivencia no reproduce y_6m.')
    if frame.duplicated(['person_key', 'snapshot_date']).any():
        raise RuntimeError('La consulta base contiene duplicados persona-snapshot.')
    return frame


def attach_history(frame, config, salt):
    template = (ROOT / config['history_query']).read_text(encoding='utf-8')
    expected = {'snapshot_date', 'person_key'} | {f for values in config['history_blocks'].values() for f in values}
    parts = []
    with base.db.connect() as conn:
        conn.set_session(readonly=True, autocommit=True)
        for year in (2025, 2026):
            start = max(f'{year}-01-01', config['training_start'])
            end = min(f'{year}-12-31', config['knowledge_boundary'])
            sql = base.db.validate_readonly(template.replace('__PERIOD_START__', start)
                .replace('__PERIOD_END__', end).replace('__RUN_SALT__', salt))
            with conn.cursor() as cursor:
                cursor.execute(sql)
                columns = [c[0] for c in cursor.description]
                if set(columns) != expected or set(columns) & base.db.SENSITIVE_OUTPUT_COLUMNS:
                    raise RuntimeError('La consulta histórica de D no cumple el contrato.')
                while True:
                    rows = cursor.fetchmany(50000)
                    if not rows:
                        break
                    parts.append(pd.DataFrame(rows, columns=columns))
    history = pd.concat(parts, ignore_index=True)
    history['snapshot_date'] = pd.to_datetime(history.snapshot_date)
    if history.duplicated(['person_key', 'snapshot_date']).any():
        raise RuntimeError('La consulta histórica no es 1:1 por persona-snapshot.')
    before = len(frame)
    frame = frame.merge(history, on=['person_key', 'snapshot_date'], how='left', validate='one_to_one', indicator=True)
    if len(frame) != before or not frame._merge.eq('both').all():
        raise RuntimeError('La consulta histórica no reconcilia con la población base.')
    frame = frame.drop(columns='_merge')
    for field in expected - {'snapshot_date', 'person_key'}:
        frame[field] = frame[field].astype('category')
    return frame, {'outcome': 'pass', 'base_rows': before, 'history_rows': len(history),
                   'merged_rows': len(frame), 'duplicate_keys': 0, 'missing_matches': 0}


def add_interactions(frame, config):
    result = frame.copy()
    for block in config['interaction_blocks'].values():
        for name, parents in block.items():
            a, b = parents
            result[name] = (result[a].astype(str) + ' | ' + result[b].astype(str)).astype('category')
    return result


def eta_c(model, frame):
    return np.asarray(model.design.matrix(frame) @ model.beta).ravel()


def restore_cq(path):
    artifact = base.read(path)
    model = prior.restore_model(artifact['base_model'])
    encoder = qmodel.CategoryEncoder(**artifact['correction']['encoder'])
    beta = np.asarray(artifact['correction']['beta'], float)
    return artifact, model, encoder, beta


def cq_prediction(model, encoder, beta, frame):
    return cq.risk(model, frame, horizon.category_matrix(encoder, frame) @ beta)


def collapse_offset(x, y, offset):
    if x.nnz and not np.all(x.data == 1):
        raise ValueError('La compresión exacta requiere diseño binario.')
    packed = np.packbits(x.astype(np.uint8).toarray(), axis=1)
    raw = np.ascontiguousarray(np.column_stack([packed, np.asarray(offset, np.float64).view(np.uint8).reshape(-1, 8)]))
    keys = raw.view(np.dtype((np.void, raw.shape[1]))).ravel()
    _, first, inverse = np.unique(keys, return_index=True, return_inverse=True)
    n = np.bincount(inverse).astype(float)
    success = np.bincount(inverse, weights=np.asarray(y, float))
    return x[first].tocsr(), success / n, n, np.asarray(offset, float)[first]


def penalized_fit(x, y, offset, penalty, link='cloglog', max_iter=100):
    x, y, n, offset = collapse_offset(sparse.csr_matrix(x), y, offset)
    beta = np.zeros(x.shape[1])
    penalty = np.asarray(penalty, float)
    if len(penalty) != x.shape[1] or penalty[0] != 0:
        raise ValueError('Vector de penalización inválido.')
    for iteration in range(1, max_iter + 1):
        eta = offset + x @ beta
        if link == 'cloglog':
            z = np.exp(np.clip(eta, -30, 5))
            p = np.clip(-np.expm1(-z), 1e-10, 1-1e-10)
            derivative = np.maximum(z * np.exp(-z), 1e-10)
        elif link == 'logit':
            p = np.clip(expit(np.clip(eta, -30, 30)), 1e-10, 1-1e-10)
            derivative = np.maximum(p * (1-p), 1e-10)
        else:
            raise ValueError(link)
        weight = n * derivative**2 / np.maximum(p * (1-p), 1e-10)
        working = x @ beta + (y-p) / derivative
        normal = (x.T @ x.multiply(weight[:, None])).toarray()
        normal.flat[::normal.shape[0]+1] += penalty + 1e-10
        rhs = np.asarray(x.T @ (weight * working)).ravel()
        try:
            updated = np.linalg.solve(normal, rhs)
        except np.linalg.LinAlgError:
            updated = np.linalg.lstsq(normal, rhs, rcond=None)[0]
        if not np.isfinite(updated).all():
            raise RuntimeError('El ajuste penalizado produjo coeficientes no finitos.')
        delta = float(np.max(np.abs(updated-beta)))
        beta = updated
        if delta < 1e-7:
            return beta, iteration, len(y)
    raise RuntimeError(f'IRLS {link} no convergió.')


def penalty_vector(columns, hr_features, l2_hr, l2_q, scale):
    result = np.zeros(len(columns))
    for i, column in enumerate(columns[1:], 1):
        feature = column.split('=', 1)[0]
        result[i] = scale * (l2_hr if feature in hr_features else l2_q)
    return result


def monthly_metrics(y, p):
    loss = base.losses(y, p)
    return {'log_loss': float(loss['log_loss'].mean()), 'brier_score': float(loss['brier_score'].mean()),
            'pr_auc': float(average_precision_score(y, p)), 'events': int(np.sum(y)), 'rows': len(y)}


def active_columns(encoder, features):
    return np.asarray(encoder.indices(features), dtype=int)


def candidate_fit(model, train, valid, encoder, features, hr_features, l2_hr, l2_q, scale, mode, link='cloglog'):
    indices = active_columns(encoder, features)
    x = encoder.transform(train)[:, indices]
    xv = encoder.transform(valid)[:, indices]
    columns = [encoder.columns[i] for i in indices]
    penalty = penalty_vector(columns, hr_features, l2_hr, l2_q, scale)
    offset = eta_c(model, train)
    if link == 'logit':
        offset = np.log(np.clip(base.hazard(offset), 1e-8, 1-1e-8) / np.clip(1-base.hazard(offset), 1e-8, 1))
    beta, iterations, unique_rows = penalized_fit(x, train.y_next.to_numpy(float), offset, penalty, link)
    correction = np.asarray(xv @ beta).ravel()
    if mode == 'r6':
        if link == 'cloglog':
            p = cq.risk(model, valid, correction)
        else:
            p = logit_risk(model, valid, correction)
        metrics = base.metrics(valid, p)
    else:
        raw = eta_c(model, valid)
        p = base.hazard(raw+correction) if link == 'cloglog' else expit(np.log(base.hazard(raw)/(1-base.hazard(raw)))+correction)
        metrics = monthly_metrics(valid.y_next.to_numpy(float), p)
    return {'beta': beta, 'iterations': iterations, 'unique_design_offset_rows': unique_rows,
            'metrics': metrics, 'columns': columns, 'indices': indices}


def selection_split(frame, origin, config):
    origin = pd.Timestamp(origin)
    direct_dates = sorted(frame.loc[frame.y_6m.notna() & (frame.r6_end <= origin), 'snapshot_date'].unique())
    n = config['selection']['r6_snapshots']
    if len(direct_dates) >= n:
        dates = direct_dates[-n:]
        valid = frame.loc[frame.snapshot_date.isin(dates) & frame.y_6m.notna()].copy()
        core = frame.loc[frame.y_next.notna() & (frame.label_end <= pd.Timestamp(dates[0]))].copy()
        mode = 'r6'
    else:
        monthly_dates = sorted(frame.loc[frame.y_next.notna() & (frame.label_end <= origin), 'snapshot_date'].unique())
        n = config['selection']['monthly_fallback_snapshots']
        if len(monthly_dates) < n + 1:
            raise RuntimeError('Historia insuficiente incluso para fallback mensual.')
        dates = monthly_dates[-n:]
        valid = frame.loc[frame.snapshot_date.isin(dates) & frame.y_next.notna()].copy()
        core = frame.loc[frame.y_next.notna() & (frame.label_end <= pd.Timestamp(dates[0]))].copy()
        mode = 'monthly_fallback'
    if core.y_next.sum() < 30 or (valid.y_6m.sum() if mode == 'r6' else valid.y_next.sum()) < 30:
        raise RuntimeError('El split de selección no alcanza 30 eventos.')
    return core, valid, mode, [str(pd.Timestamp(d).date()) for d in dates]


def select_best(trials, config, mode):
    valid = [r for r in trials if r.get('status') == 'ok']
    if not valid:
        raise RuntimeError('Ningún candidato de D convergió.')
    min_brier = min(r['metrics']['brier_score'] for r in valid)
    eligible = [r for r in valid if r['metrics']['brier_score'] <= min_brier *
                (1+config['selection']['maximum_relative_brier_from_best'])]
    if mode == 'r6':
        max_pr = max(r['metrics']['pr_auc'] for r in valid)
        eligible = [r for r in eligible if r['metrics']['pr_auc'] >=
                    max_pr*config['selection']['minimum_relative_pr_auc']]
    best_loss = min(r['metrics']['log_loss'] for r in eligible)
    near = [r for r in eligible if r['metrics']['log_loss'] <= best_loss *
            (1+config['selection']['log_loss_parsimony_tolerance'])]
    return min(near, key=lambda r: (r['parameters'], r['metrics']['log_loss'],
                                    -r['l2_hr'], -r['l2_q'], r['id']))


def search_d(frame, origin, model, config, out):
    core, valid, mode, dates = selection_split(frame, origin, config)
    all_hr = list(dict.fromkeys(f for values in config['history_blocks'].values() for f in values))
    all_q = list(dict.fromkeys(f for values in config['q_representations'].values() for f in values))
    all_interactions = list(dict.fromkeys(f for block in config['interaction_blocks'].values() for f in block))
    full_features = all_hr + all_q + all_interactions
    encoder = qmodel.CategoryEncoder.fit(core, full_features)
    trials = []

    def fit_one(identifier, features, l2_hr, l2_q, stage, link='cloglog'):
        row = {'id': identifier, 'features': list(features), 'l2_hr': float(l2_hr), 'l2_q': float(l2_q),
               'stage': stage, 'link': link, 'parameters': len(active_columns(encoder, features))}
        try:
            fitted = candidate_fit(model, core, valid, encoder, features, set(all_hr), l2_hr, l2_q,
                                   config['penalty_cell_scale'], 'r6' if mode == 'r6' else 'monthly', link)
            row.update(status='ok', metrics=fitted['metrics'], iterations=fitted['iterations'],
                       unique_design_offset_rows=fitted['unique_design_offset_rows'])
        except (RuntimeError, np.linalg.LinAlgError, ValueError) as error:
            row.update(status='failed', reason=str(error))
        trials.append(row)
        return row

    # Control HR y rejilla conjunta principal.
    for l2_hr in config['l2_hr_grid']:
        fit_one(f'C_updated_hr{l2_hr:g}', all_hr, l2_hr, max(config['l2_q_grid']), 'hr_control')
    for rep, qfeatures in config['q_representations'].items():
        for l2_hr, l2_q in itertools.product(config['l2_hr_grid'], config['l2_q_grid']):
            fit_one(f'D_{rep}_hr{l2_hr:g}_q{l2_q:g}', all_hr+qfeatures, l2_hr, l2_q, 'joint_grid')
    preliminary = select_best([r for r in trials if r['stage'] == 'joint_grid'], config, mode)
    rep_name = preliminary['id'].split('_hr', 1)[0].replace('D_', '')
    chosen_q = config['q_representations'][rep_name]
    lh, lq = preliminary['l2_hr'], preliminary['l2_q']
    fit_one(f'D_{rep_name}_q_only', chosen_q, lh, lq, 'history_ablation')
    for block, features in config['history_blocks'].items():
        fit_one(f'D_{rep_name}_{block}', chosen_q+features, lh, lq, 'history_block')
    for block, mapping in config['interaction_blocks'].items():
        fit_one(f'D_{rep_name}_allhr_{block}', all_hr+chosen_q+list(mapping), lh, lq, 'interaction_block')
    fit_one(f'D_{rep_name}_allhr_all_interactions', all_hr+chosen_q+all_interactions, lh, lq, 'interaction_all')
    winner = select_best([r for r in trials if r['stage'] != 'hr_control'], config, mode)
    hr_winner = select_best([r for r in trials if r['stage'] == 'hr_control'], config, mode)
    record = {'origin': str(pd.Timestamp(origin).date()), 'selection_mode': mode,
              'selection_snapshots': dates, 'core_last_label_end': str(core.label_end.max().date()),
              'winner': winner, 'hr_control_winner': hr_winner, 'trials': trials}
    write(out / 'selection.json', record)
    return winner, hr_winner, record


def fit_artifact(model, train, spec, config, link='cloglog'):
    all_hr = set(f for values in config['history_blocks'].values() for f in values)
    encoder = qmodel.CategoryEncoder.fit(train, spec['features'])
    x = encoder.transform(train)
    columns = encoder.columns
    penalty = penalty_vector(columns, all_hr, spec['l2_hr'], spec['l2_q'], config['penalty_cell_scale'])
    offset = eta_c(model, train)
    if link == 'logit':
        h = base.hazard(offset)
        offset = np.log(h/(1-h))
    beta, iterations, unique_rows = penalized_fit(x, train.y_next.to_numpy(float), offset, penalty, link)
    return {'link': link, 'encoder': encoder, 'beta': beta, 'iterations': iterations,
            'unique_design_offset_rows': unique_rows, 'l2_hr': spec['l2_hr'], 'l2_q': spec['l2_q'],
            'features': spec['features']}


def correction(fitted, frame):
    return np.asarray(fitted['encoder'].transform(frame) @ fitted['beta']).ravel()


def logit_risk(model, frame, corr):
    coefficients = dict(zip(model.design.columns, model.beta))
    calendar = np.zeros(13)
    for name, value in coefficients.items():
        if name.startswith('calendar_month='):
            calendar[int(name.split('=')[1])] = value
    months = frame.snapshot_date.dt.month.to_numpy()
    fixed = eta_c(model, frame) - calendar[months]
    future = (months[:, None]-1+np.arange(6)) % 12 + 1
    clog_eta = fixed[:, None] + calendar[future]
    h0 = base.hazard(clog_eta)
    logit_eta = np.log(h0/(1-h0)) + np.asarray(corr)[:, None]
    hazards = expit(np.clip(logit_eta, -30, 30))
    return np.clip(1-np.prod(1-hazards, axis=1), 1e-8, 1-1e-8)


def artifact_json(base_artifact, fitted, spec, cutoff):
    return {'name': 'Modelo D', 'family': f'monthly_{fitted["link"]}_offset', 'cutoff': str(cutoff),
            'base_model': base_artifact, 'selected': spec,
            'correction': {'encoder': asdict(fitted['encoder']), 'beta': fitted['beta'],
                'features': fitted['features'], 'l2_hr': fitted['l2_hr'], 'l2_q': fitted['l2_q'],
                'iterations': fitted['iterations'], 'unique_design_offset_rows': fitted['unique_design_offset_rows']},
            'formula': ('R6 = 1-product(1-h_m); cloglog(eta_C + delta_HR + beta_Q + interacciones)'
                        if fitted['link'] == 'cloglog' else
                        'R6 = 1-product(1-h_m); logit(h_C) + corrección'),
            'calibration': {'status': 'identity_insufficient_out_of_fit_history'},
            'qvoice_included': True, 'employee_level_rows_persisted': False,
            'individual_scores_published': False}


def reproduce_artifact(artifact, frame):
    model = prior.restore_model(artifact['base_model'])
    enc = qmodel.CategoryEncoder(**artifact['correction']['encoder'])
    corr = enc.transform(frame) @ np.asarray(artifact['correction']['beta'], float)
    return cq.risk(model, frame, corr) if artifact['family'].startswith('monthly_cloglog') else logit_risk(model, frame, corr)


def rsf_select_and_fit(frame, origin, features, config, target, period_index):
    import engineering_random_survival_forest as rsf
    rsf_config = base.read(ROOT / 'config/engineering_rsf_20261008.json')
    rsf_config.update(config['rsf'])
    rsf_config.update({k: config[k] for k in ['capacity_fractions', 'primary_capacity_fraction',
        'minimum_group_people_each_snapshot', 'minimum_public_people_each_snapshot', 'minimum_distinct_events']})
    rsf_config['capture_relative_tolerance'] = 0.02
    dates = sorted(frame.loc[frame.y_6m.notna() & (frame.r6_end <= pd.Timestamp(origin)), 'snapshot_date'].unique())
    candidates = []
    transferred = period_index == 0 or len(dates) < 3
    if transferred:
        chosen = {**config['rsf']['transferred_default'], 'features': features,
                  'id': 'transferred_default', 'selection_status': 'transferred'}
    else:
        valid_dates = dates[-3:]
        validation = frame.loc[frame.snapshot_date.isin(valid_dates)]
        train, y, _ = rsf.training(frame, valid_dates[0])
        encoder, x = rsf.encoder_fit(train, features)
        for leaf, mf in itertools.product(config['rsf']['minimum_leaf_grid'], config['rsf']['max_features_grid']):
            spec = {'id': f'leaf{leaf}_features{mf}', 'features': features,
                    'min_samples_leaf': leaf, 'max_features': mf}
            forest = rsf.forest_fit(x, y, spec, rsf_config, config['rsf']['selection_trees'],
                                    config['seed']+period_index)
            p = np.clip(1-rsf.survival(forest, encoder, features, validation)[:, -1], 1e-8, 1-1e-8)
            ev, _ = rsf.grouped(validation, p, rsf_config, details=False)
            candidates.append({**spec, 'global': ev['global'],
                'priority': ev['scenarios']['30']['metrics']})
        maximum = max(r['priority']['capture_percent'] for r in candidates)
        near = [r for r in candidates if r['priority']['capture_percent'] >= maximum*0.98]
        chosen = min(near, key=lambda r: (r['global']['log_loss'], r['priority']['group_snapshot_mae_pp'],
                                          -r['min_samples_leaf'], r['id']))
    train, y, info = rsf.training(frame, origin)
    encoder, x = rsf.encoder_fit(train, features)
    forest = rsf.forest_fit(x, y, chosen, rsf_config, config['rsf']['final_trees'], config['seed']+period_index)
    grouping = {'role': 'diagnóstico; la promoción usa los grupos comunes', 'rules': []}
    cal = {'status': 'identity_insufficient_out_of_fit_history', 'log_multiplier': 0., 'multiplier': 1.}
    rsf.export_forest(forest, encoder, chosen, cal, info, grouping, target, train.iloc[:1000])
    write(target / 'selection.json', {'origin': origin, 'transferred': transferred,
        'validation_snapshots': [] if transferred else [str(pd.Timestamp(d).date()) for d in valid_dates],
        'candidates': candidates, 'winner': chosen})
    return forest, encoder, chosen, rsf_config


def paired_intervals(held, config, left='D', right='CQ'):
    keys = np.concatenate([h['keys'] for h in held])
    codes, people = pd.factorize(keys, sort=False)
    width = 5
    sums = np.zeros((len(people), len(held), width+2))
    offset = 0
    for i, item in enumerate(held):
        idx = codes[offset:offset+len(item['y'])]
        offset += len(idx)
        y = item['y']
        sums[:, i, 0] = np.bincount(idx, weights=y, minlength=len(people))
        sums[:, i, 1] = np.bincount(idx, minlength=len(people))
        for j, cap in enumerate(('20', '30', '40'), 2):
            delta = item['allocations'][cap][left] - item['allocations'][cap][right]
            sums[:, i, j] = np.bincount(idx, weights=100*y*delta, minlength=len(people))
        ll = base.losses(y, item['predictions'][left])
        rr = base.losses(y, item['predictions'][right])
        sums[:, i, 5] = np.bincount(idx, weights=ll['log_loss']-rr['log_loss'], minlength=len(people))
        sums[:, i, 6] = np.bincount(idx, weights=ll['brier_score']-rr['brier_score'], minlength=len(people))
    denominators = [0, 0, 0, 1, 1]
    flat = sums.reshape(len(people), -1)
    rng = np.random.default_rng(config['seed'])
    draws = []
    for _ in range(config['bootstrap_repetitions']):
        w = np.bincount(rng.integers(len(people), size=len(people)), minlength=len(people))
        total = (w @ flat).reshape(len(held), width+2)
        draws.append(np.mean(total[:, 2:] / total[:, denominators], axis=0))
    total = sums.sum(axis=0)
    point = np.mean(total[:, 2:] / total[:, denominators], axis=0)
    ci = np.quantile(np.asarray(draws), [.025, .975], axis=0)
    names = ['capture20_pp', 'capture30_pp', 'capture40_pp', 'log_loss', 'brier_score']
    return {name: {'difference_D_minus_CQ': float(point[i]), 'ci95': ci[:, i].tolist()}
            for i, name in enumerate(names)}


def mean_summary(periods, model):
    rows = [p['evaluation'][model] for p in periods]
    result = {'global': {k: float(np.mean([r['global'][k] for r in rows])) for k in rows[0]['global']
                         if all(isinstance(r['global'][k], (int, float, np.number)) for r in rows)}}
    result['scenarios'] = {}
    for cap in ('20', '30', '40'):
        ms = [r['scenarios'][cap]['metrics'] for r in rows]
        result['scenarios'][cap] = {k: float(np.mean([m[k] for m in ms])) for k in ms[0]
                                    if all(isinstance(m[k], (int, float, np.number)) for m in ms)}
    return result


def promotion_decision(periods, intervals, config):
    d, q = mean_summary(periods, 'D'), mean_summary(periods, 'CQ')
    rule = config['promotion']
    gain = intervals['capture30_pp']
    d30, q30 = d['scenarios']['30'], q['scenarios']['30']
    relative_precision = ((q30['group_snapshot_mae_pp']-d30['group_snapshot_mae_pp']) /
                          q30['group_snapshot_mae_pp']) if q30['group_snapshot_mae_pp'] else 0.
    common = {
        'log_loss_guard': d['global']['log_loss'] <= q['global']['log_loss']*(1+rule['maximum_relative_loss_worsening']),
        'brier_guard': d['global']['brier_score'] <= q['global']['brier_score']*(1+rule['maximum_relative_loss_worsening']),
        'worst_group_guard': d30['worst_publishable_group_error_pp'] <= q30['worst_publishable_group_error_pp'] + rule['maximum_worst_group_error_worsening_pp'],
        'period_floor': all(p['evaluation']['D']['scenarios']['30']['metrics']['capture_percent'] >=
                            p['evaluation']['CQ']['scenarios']['30']['metrics']['capture_percent']-
                            rule['maximum_period_capture_loss_pp'] for p in periods)}
    capture = {'gain': gain['difference_D_minus_CQ'] >= rule['capture_gain_pp'],
               'ci_lower_positive': gain['ci95'][0] > 0,
               'group_error_guard': d30['group_snapshot_mae_pp'] <= q30['group_snapshot_mae_pp']+
                                    rule['maximum_group_error_worsening_pp']}
    precision = {'capture_noninferior': gain['difference_D_minus_CQ'] >= -rule['capture_noninferiority_pp'],
                 'ci_noninferior': gain['ci95'][0] >= -rule['capture_noninferiority_pp'],
                 'relative_group_error_reduction': relative_precision >= rule['precision_relative_improvement']}
    capture_pass = all(capture.values()) and all(common.values())
    precision_pass = all(precision.values()) and all(common.values())
    return {'promote_D': bool(capture_pass or precision_pass),
            'route': 'capture' if capture_pass else ('precision' if precision_pass else None),
            'capture_route': capture, 'precision_route': precision, 'common_guards': common,
            'relative_group_snapshot_error_reduction': relative_precision,
            'D': d, 'CQ': q,
            'decision': ('D sustituye a CQ bajo la regla congelada.' if capture_pass or precision_pass
                         else 'CQ permanece elegido; D no supera la regla congelada.')}


def report_markdown(result):
    s = result['decision']
    rows = []
    for name in ['C', 'CQ', 'C_updated', 'D', 'monthly_logit', 'RSF_Q']:
        m = result['summary'][name]
        rows.append(f"| {name} | {m['scenarios']['30']['capture_percent']:.1f} | "
                    f"{m['scenarios']['30']['group_snapshot_mae_pp']:.1f} | "
                    f"{m['global']['log_loss']*1000:.1f} | {m['global']['pr_auc']*100:.1f} |")
    return '\n'.join([
        '# Modelo D: comparación final', '', '**Modo:** `presentation`. Evaluación retrospectiva; etapa de selección.', '',
        s['decision'], '',
        '| Modelo | Captura al 30% | Error grupo-mes pp | Log-loss ×1000 | PR-AUC % |',
        '|---|---:|---:|---:|---:|', *rows, '',
        'La promoción se decidió con los mismos cortes interpretables de antigüedad, salidas del equipo y nivel. '
        'Las filas persona-snapshot y las puntuaciones individuales no se persistieron.', '',
        f"Ruta cumplida: {s['route'] or 'ninguna'}. Diferencia D−CQ en captura al 30%: "
        f"{result['intervals']['capture30_pp']['difference_D_minus_CQ']:.1f} pp; IC95 "
        f"[{result['intervals']['capture30_pp']['ci95'][0]:.1f}, {result['intervals']['capture30_pp']['ci95'][1]:.1f}].", '',
        '## Límites', '',
        '- QVoice sólo aporta dos waves anuales; las interacciones siguen siendo evidencia retrospectiva.',
        '- La calibración por grupo quedó en identidad porque no existen tres series temporales fuera de ajuste del nuevo D.',
        '- El bosque se comparó sin calibración adicional y su explicación usa los mismos grupos comunes.', ''
    ])


def run(path):
    started = time.perf_counter()
    config = base.read(path)
    out = ROOT / config['output']
    if (out / 'started.json').exists() or (out / 'results.json').exists():
        raise RuntimeError('La carpeta de D ya contiene una ejecución.')
    cconfig = base.read(ROOT / config['source_c'] / 'frozen-config.json')
    qconfig = load_config(ROOT / config['source_qvoice_config'])
    metadata = base.read(ROOT / config['source_qvoice'] / 'preflight/source-metadata.json')
    preserved = [config['source_c'], config['source_cq'], 'output/analysis/engineering/20261008/random-survival-forest-v1']
    before = directory_hashes(preserved)
    write(out / 'started.json', {'status': 'running', 'started_at': datetime.now(timezone.utc)})
    write(out / 'frozen-config.json', config)
    source_files = [path, Path(__file__), ROOT/config['plan'], ROOT/config['base_query'], ROOT/config['history_query'],
                    ROOT/config['authorization']] + [ROOT/q for q in config.get('audit_queries', [])]
    source_files = [p for p in source_files if p.exists()]
    for source in source_files:
        target = out / 'source' / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    write(out / 'frozen-sources.json', {str(p.relative_to(ROOT)): base.sha(p) for p in source_files})
    salt = secrets.token_hex(32)
    frame = load_frame(config, cconfig, salt)
    frame, history_check = attach_history(frame, config, salt)
    all_q = list(dict.fromkeys(f for values in config['q_representations'].values() for f in values))
    timing = {}
    frame = horizon.attach_selected(frame, qconfig, metadata, salt, all_q, timing)
    del salt
    expected_wave = (frame.snapshot_date.dt.year-1).astype(str).to_numpy()
    if not np.array_equal(frame.qvoice_wave.astype(str).to_numpy(), expected_wave):
        raise RuntimeError('La asignación anual de QVoice no coincide con Y-1.')
    frame = add_interactions(frame, config)
    population = frame.groupby('snapshot_date').agg(exposures=('person_key', 'size'),
        people=('person_key', 'nunique'), monthly_labeled=('y_next', 'count'),
        six_month_labeled=('y_6m', 'count')).reset_index()
    write(out / 'population.json', population.to_dict('records'))
    write(out / 'input-checks.json', {'history_reconciliation': history_check,
        'annual_qvoice_assignment': True, 'duplicate_person_snapshots': 0,
        'qvoice_timing_seconds': timing, 'employee_rows_persisted': False})
    periods, held = [], []
    for index, period in enumerate(config['periods']):
        tick = time.perf_counter()
        target = out / 'folds' / period['id']
        cq_path = ROOT / config['source_cq'] / 'folds' / period['id'] / 'model.json'
        cq_artifact, model, qencoder, qbeta = restore_cq(cq_path)
        winner, hr_winner, selection = search_d(frame, period['origin'], model, config, target)
        train = frame.loc[frame.y_next.notna() & (frame.label_end <= pd.Timestamp(period['origin']))].copy()
        test = frame.loc[frame.snapshot_date.between(period['origin'], period['end']) & frame.y_6m.notna()].copy()
        if test.snapshot_date.nunique() != period['snapshots']:
            raise RuntimeError(f'Periodo externo incompleto: {period["id"]}.')
        dfit = fit_artifact(model, train, winner, config)
        hfit = fit_artifact(model, train, hr_winner, config)
        lfit = fit_artifact(model, train, winner, config, 'logit')
        predictions = {'C': model.risk(test), 'CQ': cq_prediction(model, qencoder, qbeta, test),
            'C_updated': cq.risk(model, test, correction(hfit, test)),
            'D': cq.risk(model, test, correction(dfit, test)),
            'monthly_logit': logit_risk(model, test, correction(lfit, test))}
        rsf_features = list(dict.fromkeys(base.raw_features(cconfig)+winner['features']))
        forest, rencoder, rspec, rsf_config = rsf_select_and_fit(frame, period['origin'], rsf_features,
            config, target/'rsf-qvoice', index)
        import engineering_random_survival_forest as rsf
        predictions['RSF_Q'] = np.clip(1-rsf.survival(forest, rencoder, rsf_features, test)[:, -1], 1e-8, 1-1e-8)
        evaluation, allocations = cq.evaluate(test, predictions, config)
        d_artifact = artifact_json(model.artifact(), dfit, winner, period['origin'])
        logit_artifact = artifact_json(model.artifact(), lfit, winner, period['origin'])
        write(target / 'model.json', d_artifact)
        write(target / 'monthly-logit-model.json', logit_artifact)
        max_reproduction = float(np.max(np.abs(reproduce_artifact(d_artifact, test)-predictions['D'])))
        if max_reproduction > 1e-10:
            raise RuntimeError('El artefacto D no reproduce sus predicciones.')
        archived_eval = base.read(ROOT/config['source_cq']/'folds'/period['id']/'evaluation.json')['evaluation']['CQ']['global']
        current_eval = evaluation['CQ']['global']
        cq_diff = max(abs(current_eval[k]-archived_eval[k]) for k in ['pr_auc','brier_score','log_loss','predicted_percent'])
        if cq_diff > 1e-8:
            raise RuntimeError(f'CQ archivado no se reproduce: {cq_diff:.3g}.')
        record = {**period, 'first_snapshot': str(test.snapshot_date.min().date()),
            'last_snapshot': str(test.snapshot_date.max().date()), 'exposures': len(test),
            'people': test.person_key.nunique(), 'selected': winner,
            'calibration': {'status': 'identity_insufficient_out_of_fit_history'},
            'evaluation': evaluation, 'artifact_reproduction_max_error': max_reproduction,
            'CQ_reproduction_max_metric_difference': cq_diff, 'seconds': time.perf_counter()-tick}
        write(target / 'evaluation.json', record)
        periods.append(record)
        held.append({'keys': test.person_key.to_numpy(), 'y': test.y_6m.to_numpy(float),
                     'predictions': predictions, 'allocations': allocations})
        log(f'D: periodo {period["id"]} terminado en {record["seconds"]:.1f} s.')
    intervals = paired_intervals(held, config)
    decision = promotion_decision(periods, intervals, config)
    names = ['C', 'CQ', 'C_updated', 'D', 'monthly_logit', 'RSF_Q']
    summary = {name: mean_summary(periods, name) for name in names}
    # Modelo final D al corte de conocimiento, independientemente del resultado de promoción.
    final_target = out / 'trained-model'
    final_cq, final_model, _, _ = restore_cq(ROOT/config['source_cq']/'trained-model'/'model.json')
    final_winner, _, final_selection = search_d(frame, config['knowledge_boundary'], final_model, config, final_target)
    final_train = frame.loc[frame.y_next.notna() & (frame.label_end <= pd.Timestamp(config['knowledge_boundary']))]
    final_fit = fit_artifact(final_model, final_train, final_winner, config)
    final_artifact = artifact_json(final_model.artifact(), final_fit, final_winner, config['knowledge_boundary'])
    write(final_target / 'model.json', final_artifact)
    sample = final_train.iloc[:min(2000, len(final_train))]
    final_error = float(np.max(np.abs(reproduce_artifact(final_artifact, sample)-
                                      cq.risk(final_model, sample, correction(final_fit, sample)))))
    if final_error > 1e-10:
        raise RuntimeError('El modelo final D no se serializó de forma reproducible.')
    after = directory_hashes(preserved)
    unchanged = before == after
    if not unchanged:
        raise RuntimeError('Cambió un modelo histórico durante la ejecución de D.')
    result = {'run_id': config['run_id'], 'created_at': datetime.now(timezone.utc),
        'reporting_mode': 'presentation', 'periods': periods, 'summary': summary,
        'intervals': intervals, 'decision': decision, 'final_selected': final_winner,
        'final_artifact_reproduction_max_error': final_error,
        'elapsed_seconds': time.perf_counter()-started, 'employee_level_rows_persisted': False,
        'individual_scores_published': False}
    write(out / 'results.json', result)
    write(out / 'selection-decision.json', decision)
    write(out / 'preservation.json', {'unchanged': unchanged, 'sha256_before': before, 'sha256_after': after})
    checks = {'history_audits_required': True, 'history_query_reconciled_one_to_one': True,
        'annual_qvoice_policy': True, 'CQ_reproduced_at_1e8': True,
        'D_serialization_reproduced': True, 'monthly_logit_control_run': True,
        'RSF_Q_control_run': True, 'group_calibration': 'identity_insufficient_out_of_fit_history',
        'prior_artifacts_unchanged': unchanged, 'employee_rows_persisted': False,
        'individual_scores_published': False}
    write(out / 'analysis-checks.json', checks)
    (out / 'informe.md').write_text(report_markdown(result), encoding='utf-8')
    table = ['# Tabla comparativa', '', '| Modelo | Captura 30% | Error grupo-mes pp | Log-loss ×1000 | Brier ×1000 |',
             '|---|---:|---:|---:|---:|']
    for name in names:
        m = summary[name]
        table.append(f"| {name} | {m['scenarios']['30']['capture_percent']:.1f} | "
                     f"{m['scenarios']['30']['group_snapshot_mae_pp']:.1f} | "
                     f"{m['global']['log_loss']*1000:.1f} | {m['global']['brier_score']*1000:.1f} |")
    (out / 'tabla-comparativa.md').write_text('\n'.join(table)+'\n', encoding='utf-8')
    write(out / 'completed.json', {'status': 'completed_analysis', 'seconds': result['elapsed_seconds']})
    write(out / 'manifest.json', {'status': 'completed_analysis', 'run_id': config['run_id'],
        'reporting_mode': 'presentation', 'authorization': config['authorization'],
        'employee_level_rows_persisted': False, 'individual_scores_published': False,
        'salt_persisted': False, 'files': {str(p.relative_to(out)): base.sha(p) for p in out.rglob('*')
                                          if p.is_file() and p.name != 'manifest.json'}})
    log(f'Modelo D terminado en {result["elapsed_seconds"]:.1f} s. {decision["decision"]}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        run(args.config.resolve())
