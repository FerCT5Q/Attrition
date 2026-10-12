"""C + QVoice: corrección con offset C archivado; ninguna fila sale de RAM."""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import itertools
from pathlib import Path
import secrets
import shutil
import time

import numpy as np
import pandas as pd
from scipy import sparse
from threadpoolctl import threadpool_limits

import engineering_model_c as base
import engineering_c_group_selection as groups
import compare_engineering_bc_priority as prior
import qvoice_calibrated_model as qmodel
import qvoice_horizon_calibration as horizon
from qvoice_model_data import load_config

ROOT = base.ROOT
DEFAULT = ROOT / 'config/engineering_model_c_qvoice_20261008.json'
write = groups.write
VALID = ['v0', 'v1', '<50', '50–69', '70–79', '80–89', '90–99', '100']
NAMES = {'C': 'C', 'C_refresh': 'C con intercepto actualizado', 'C_availability': 'C con disponibilidad QVoice',
         'CQ': 'C + QVoice sin calibración', 'C_scalar': 'C con escalar R6',
         'C_refresh_scalar': 'C con intercepto y escalar',
         'C_availability_scalar': 'C con disponibilidad y escalar', 'CQ_scalar': 'C + QVoice con escalar R6'}


def load_frame(config, source_config, salt):
    authorization = base.read(ROOT / config['authorization'])
    if authorization['status'] != 'approved' or authorization['non_negotiable_controls']['disk_cache_of_rows']:
        raise RuntimeError('No está vigente la autorización de memoria.')
    for name in ['metadata', 'region', 'comp_ratio_band', 'grade_family', 'acquisition_recorded', 'transfer_12m', 'transfer_history']:
        evidence = base.read(ROOT / config['source_c'] / 'input-evidence' / f'{name}.json')
        if evidence['outcome'] != 'pass' or base.sha(ROOT / evidence['query']) != evidence['sql_sha256']:
            raise RuntimeError('Cambió un contrato de entrada de C.')
    original = (ROOT / source_config['query']).read_text(encoding='utf-8')
    template = (ROOT / config['query']).read_text(encoding='utf-8')
    start = template.index("  CASE WHEN f.service_date IS NOT NULL AND f.service_date <= DATE '2024-01-01'")
    end = template.index("  COALESCE(f.level_grouped, '(unknown)') AS level_grouped,", start)
    if template[:start] + template[end:] != original:
        raise RuntimeError('La consulta cambió fuera de los indicadores de episodio.')
    expected = {'snapshot_date', 'person_key', 'label_end', 'y_next', 'y_6m',
        'company_tenure_band', 'tenure_julia_band', 'same_episode_2024', 'same_episode_2025', 'same_episode_2026'}
    expected |= set(base.raw_features(source_config))
    parts = []
    with base.db.connect() as conn:
        conn.set_session(readonly=True, autocommit=True)
        for year in [2025, 2026]:
            tick = time.perf_counter()
            end_date = min(f'{year}-12-31', config['knowledge_boundary'])
            sql = base.db.validate_readonly(template.replace('__PERIOD_START__', f'{year}-01-01')
                    .replace('__PERIOD_END__', end_date).replace('__RUN_SALT__', salt))
            with conn.cursor() as cursor:
                try:
                    cursor.execute(sql)
                except base.db.psycopg2.Error as error:
                    raise RuntimeError(f'Consulta autorizada incompleta ({type(error).__name__}).') from None
                cols = [c[0] for c in cursor.description]
                if set(cols) != expected or set(cols) & base.db.SENSITIVE_OUTPUT_COLUMNS:
                    raise RuntimeError('Columnas fuera del contrato autorizado.')
                while True:
                    rows = cursor.fetchmany(50000)
                    if not rows:
                        break
                    part = pd.DataFrame(rows, columns=cols).drop(columns=['company_tenure_band', 'tenure_julia_band'])
                    for f in base.raw_features(source_config):
                        part[f] = part[f].astype('category')
                    parts.append(part)
            base.log(f'Carga {year} en RAM: {time.perf_counter()-tick:.1f} s.')
    frame = pd.concat(parts, ignore_index=True)
    del parts, sql
    for field in ['snapshot_date', 'label_end']:
        frame[field] = pd.to_datetime(frame[field])
    for f in base.raw_features(source_config):
        frame[f] = frame[f].astype('category')
    frame['calendar_month'] = frame.snapshot_date.dt.month.astype(str).astype('category')
    frame['r6_end'] = frame.snapshot_date + pd.DateOffset(months=6)
    if frame.duplicated(['person_key', 'snapshot_date']).any():
        raise RuntimeError('Frame con duplicados persona-snapshot.')
    for label in ['y_next', 'y_6m']:
        if not frame[label].dropna().isin([0, 1]).all():
            raise RuntimeError('Etiqueta no binaria.')
    if frame.loc[frame.r6_end > pd.Timestamp(config['knowledge_boundary']), 'y_6m'].notna().any():
        raise RuntimeError('Etiqueta R6 sin madurez.')
    if frame.loc[frame.label_end.isna(), 'y_next'].notna().any():
        raise RuntimeError('Última foto con etiqueta mensual sin seguimiento.')
    for year in [2024, 2025, 2026]:
        if not frame[f'same_episode_{year}'].isin([0, 1]).all():
            raise RuntimeError('Indicador de episodio no binario.')
    return frame


def eta(model, frame):
    return model.design.matrix(frame) @ model.beta


def risk(model, frame, correction):
    coefficients = dict(zip(model.design.columns, model.beta))
    calendar = np.zeros(13)
    for col, coef in coefficients.items():
        if col.startswith('calendar_month='):
            calendar[int(col.split('=')[1])] = coef
    months = frame.snapshot_date.dt.month.to_numpy()
    fixed = eta(model, frame) - calendar[months] + correction
    future = (months[:, None] - 1 + np.arange(6)) % 12 + 1
    # Mismo recorte por intervalo que el C archivado.
    cumulative = np.exp(np.clip(fixed[:, None] + calendar[future], -30, 5)).sum(axis=1)
    return np.clip(-np.expm1(-cumulative), 1e-8, 1-1e-8)


def catalog(config):
    source = ROOT / config['source_c']
    original = base.read(source / 'results.json')
    return [(pd.Timestamp(row['origin']), prior.restore_model(base.read(source / 'folds' / f'fold-{row["fold"]}-C-model.json')),
             str((source / 'folds' / f'fold-{row["fold"]}-C-model.json').relative_to(ROOT))) for row in original['folds']]


def model_before(bank, cutoff):
    return max((item for item in bank if item[0] <= pd.Timestamp(cutoff)), key=lambda x: x[0])


def search(monthly, cutoff, bank, config, qconfig, out):
    dates = sorted(monthly.loc[monthly.label_end <= pd.Timestamp(cutoff), 'snapshot_date'].unique())
    if len(dates) < config['search']['selection_intervals'] + 1:
        raise RuntimeError('Historia insuficiente para seleccionar QVoice.')
    selected_dates = dates[-config['search']['selection_intervals']:]
    core = monthly.loc[monthly.label_end <= selected_dates[0]]
    valid = monthly.loc[monthly.snapshot_date.isin(selected_dates)]
    origin, model, reference = model_before(bank, selected_dates[0])
    if core.empty or core.y_next.sum() < 30 or valid.y_next.sum() < 30:
        raise RuntimeError('Eventos insuficientes para selección temporal.')
    blocks = qconfig['search']['blocks']
    features = list(dict.fromkeys(f for fs in blocks.values() for f in fs))
    for f in features + qconfig['search']['pca_items']:
        if any(part[f].astype(str).isin(VALID).sum() < 30 for part in [core, valid]):
            raise RuntimeError(f'Historia insuficiente de {f} para selección.')
    encoder = qmodel.CategoryEncoder.fit(core, features)
    x, xv = horizon.category_matrix(encoder, core), horizon.category_matrix(encoder, valid)
    offset, ov = eta(model, core), eta(model, valid)
    y, yv = core.y_next.to_numpy(float), valid.y_next.to_numpy(float)
    trials = []
    names = list(blocks)
    for mask in range(1, 1 << len(names)):
        chosen = [name for i, name in enumerate(names) if mask & (1 << i)]
        fs = list(dict.fromkeys(f for name in chosen for f in blocks[name]))
        indices = encoder.indices(fs)
        tx, vx = x[:, indices], xv[:, indices]
        for penalty in config['search']['l2_grid']:
            beta, okay, iterations = qmodel.fit_offset(tx, y, offset, penalty)
            score = float(np.mean((yv-qmodel.hazard(ov+vx@beta))**2)) if okay else None
            trials.append({'id': '+'.join(chosen), 'kind': 'blocks', 'blocks': chosen, 'features': fs,
                'l2': penalty, 'parameters': len(beta), 'converged': bool(okay), 'iterations': iterations,
                'monthly_brier': score})
        if mask % 64 == 0:
            base.log(f'{cutoff}: {mask}/255 subconjuntos terminados.')
    pca = qmodel.PCAEncoder.fit(core, qconfig['search']['pca_items'])
    full_train, full_valid = pca.transform(core), pca.transform(valid)
    maximum = pca.components
    for k in qconfig['search']['pca_components']:
        indices = [0] + list(range(1, k+1)) + list(range(1+maximum, full_train.shape[1]))
        tx, vx = full_train[:, indices], full_valid[:, indices]
        for penalty in config['search']['l2_grid']:
            beta, okay, iterations = qmodel.fit_offset(tx, y, offset, penalty)
            score = float(np.mean((yv-qmodel.hazard(ov+vx@beta))**2)) if okay else None
            trials.append({'id': f'pca_{k}', 'kind': 'pca', 'features': pca.features, 'components': k,
                'l2': penalty, 'parameters': len(beta), 'converged': bool(okay), 'iterations': iterations,
                'monthly_brier': score})
    eligible = [r for r in trials if r['converged']]
    if not eligible:
        raise RuntimeError('Ninguna corrección converge.')
    winner = min(eligible, key=lambda r: (r['monthly_brier'], r['parameters'], -r['l2'], r['id']))
    record = {'winner': winner, 'trials': trials, 'C_origin': str(origin.date()), 'C_model': reference,
        'core_last_label_end': str(core.label_end.max().date()),
        'selection_snapshots': [str(pd.Timestamp(d).date()) for d in selected_dates],
        'selection_latest_label': str(valid.label_end.max().date()),
        'baseline_monthly_brier': float(np.mean((yv-qmodel.hazard(ov))**2)),
        'pca_explained_variance_ratio': pca.explained_variance_ratio}
    write(out / 'selection.json', record)
    base.log(f'{cutoff}: elegido {winner["id"]}, L2={winner["l2"]}; {len(eligible)}/{len(trials)} ajustes convergentes.')
    return winner, record


def fit_corrections(train, model, spec):
    if train.y_next.sum() < 30:
        raise RuntimeError('Historia insuficiente de eventos para corrección.')
    encoder = (qmodel.CategoryEncoder.fit(train, spec['features']) if spec['kind'] == 'blocks'
               else qmodel.PCAEncoder.fit(train, spec['features'], spec['components']))
    x = horizon.category_matrix(encoder, train) if spec['kind'] == 'blocks' else encoder.transform(train)
    offset, y = eta(model, train), train.y_next.to_numpy(float)
    beta, okay, iterations = qmodel.fit_offset(x, y, offset, spec['l2'])
    av = qmodel.CategoryEncoder.fit(train, ['av_'+f for f in spec['features']])
    av_beta, av_ok, av_iter = qmodel.fit_offset(horizon.category_matrix(av, train), y, offset, spec['l2'])
    intercept, intercept_ok, intercept_iter = qmodel.fit_offset(sparse.csr_matrix(np.ones((len(train), 1))), y, offset, spec['l2'])
    if not (okay and av_ok and intercept_ok):
        raise RuntimeError('No converge una corrección o su control.')
    return {'Q': (encoder, beta), 'availability': (av, av_beta), 'intercept': float(intercept[0]),
        'iterations': {'Q': iterations, 'availability': av_iter, 'intercept': intercept_iter}}


def predictions(model, frame, fitted, spec):
    en, be = fitted['Q']
    corr = (horizon.category_matrix(en, frame) if spec['kind'] == 'blocks' else en.transform(frame)) @ be
    av, ab = fitted['availability']
    return {'C': model.risk(frame), 'C_refresh': risk(model, frame, fitted['intercept']),
            'C_availability': risk(model, frame, horizon.category_matrix(av, frame) @ ab),
            'CQ': risk(model, frame, corr)}


def export(model, reference, origin, fitted, spec, cutoff, train, calibrators):
    en, be = fitted['Q']
    av, ab = fitted['availability']
    return {'name': 'C + QVoice', 'status': 'experimental_retrospective', 'cutoff': str(cutoff),
        'base_model_reference': reference, 'base_model_origin': str(origin.date()), 'base_model': model.artifact(),
        'selected': spec, 'correction': {'kind': spec['kind'], 'encoder': asdict(en) if spec['kind'] == 'blocks' else en.export(),
            'beta': be, 'l2': spec['l2'], 'iterations': fitted['iterations']['Q']},
        'availability_control': {'encoder': asdict(av), 'beta': ab}, 'monthly_intercept_control': fitted['intercept'],
        'calibrators': calibrators, 'fit_maximum_label_end': str(train.label_end.max().date()),
        'groups': {'dimensions': ['antiguedad', 'salidas_equipo', 'nivel'], 'minimum_people_each_snapshot': 300},
        'formula': 'R6 = 1-product(1-h_m); cloglog(eta_C + correccion_Q), calendario avanza, otras covariables fijas',
        'annual_policy': 'Encuesta Y sólo para snapshots Y+1; continuidad del episodio laboral.',
        'qvoice_included': True, 'employee_level_rows_persisted': False, 'individual_scores_published': False}


def calibrate(monthly, direct, cutoff, bank, spec, config, cache, out):
    origins = []
    for value in sorted(direct.snapshot_date.unique()):
        value = pd.Timestamp(value)
        if value + pd.DateOffset(months=6) > pd.Timestamp(cutoff):
            continue
        train = monthly.loc[monthly.label_end <= value]
        if train.snapshot_date.nunique() >= 1 and train.y_next.sum() >= 30:
            origins.append(value)
    origins = origins[-config['calibration']['maximum_origins']:]
    names = ['C', 'C_refresh', 'C_availability', 'CQ']
    details, chunks = [], []
    if len(origins) >= config['calibration']['minimum_origins']:
        for value in origins:
            key = (str(value), spec['id'], spec['l2'])
            if key not in cache:
                origin, model, reference = model_before(bank, value)
                train = monthly.loc[monthly.label_end <= value]
                fit = fit_corrections(train, model, spec)
                test = direct.loc[direct.snapshot_date == value]
                pred = predictions(model, test, fit, spec)
                cache[key] = (test.y_6m.to_numpy(float), pred,
                    {'snapshot': str(value.date()), 'latest_label': str((value+pd.DateOffset(months=6)).date()),
                     'C_origin': str(origin.date()), 'C_reference': reference,
                     'fit_latest_label': str(train.label_end.max().date()), 'monthly_intervals': train.snapshot_date.nunique()})
            y, pred, detail = cache[key]
            details.append(detail)
            chunks.append((y, pred))
    result = {}
    for name in names:
        if not chunks:
            result[name] = {'status': 'identity_insufficient_history', 'log_multiplier': 0., 'multiplier': 1.}
        else:
            y = np.concatenate([x[0] for x in chunks])
            p = np.concatenate([x[1][name] for x in chunks])
            result[name] = {'status': 'fitted', **horizon.fit_scalar(y, p, config['calibration']['log_multiplier_bounds'])}
    write(out / 'calibration.json', {'cutoff': cutoff, 'eligible_origins': [str(x.date()) for x in origins],
        'used_origins': details, 'calibrators': result,
        'limitation': config['calibration']['scope']})
    return result


def evaluate(frame, pred, config):
    encoded = groups.encode(groups.cut_keys(frame, []))
    codes, count, names = groups.combined(encoded, tuple(config['groups']), True)
    evaluations, allocations = {}, {str(int(f*100)): {} for f in config['capacity_fractions']}
    for name, p in pred.items():
        global_metrics = base.metrics(frame, p)
        g = groups.Grouped(frame, p, codes, count, config, names)
        entry = {'global': global_metrics, 'scenarios': {},
                 'groups_minimum': int(g.eligible.sum(axis=1).min()), 'groups_maximum': int(g.eligible.sum(axis=1).max())}
        for frac in config['capacity_fractions']:
            cap = str(int(frac*100))
            w, low, high = g.allocation(frac)
            m, rows = g.detail(w)
            if m.get('suppressed'):
                raise RuntimeError('Cohorte principal no publicable.')
            lm, _ = g.detail(low, False)
            hm, _ = g.detail(high, False)
            allocations[cap][name] = w.ravel()[g.cells]
            entry['scenarios'][cap] = {'metrics': m, 'selected_groups': rows,
                'whole_groups_excluding_boundary': lm, 'whole_groups_including_boundary': hm}
        evaluations[name] = entry
    # Misma selección y mismos grupos: aislar el estimador de la composición priorizada.
    main = str(int(config['primary_capacity_fraction']*100))
    ctx = prior.context(frame)
    for name, p in pred.items():
        evaluations[name]['on_C_selection'], _ = prior.describe(ctx, p, allocations[main]['C'], codes)
    return evaluations, allocations


def uncertainty(held, config):
    all_keys = np.concatenate([h['keys'] for h in held])
    codes, people = pd.factorize(all_keys, sort=False)
    pairs = [('CQ', 'C'), ('CQ_scalar', 'C'), ('CQ_scalar', 'C_scalar'),
             ('CQ', 'C_availability'), ('CQ_scalar', 'C_availability_scalar'), ('CQ', 'C_refresh'),
             ('CQ_scalar', 'CQ')]
    metrics = ['capture20', 'capture30', 'capture40', 'log_loss', 'brier_score']
    width = 2 + len(pairs)*len(metrics)
    sums = np.zeros((len(people), len(held), width))
    offset = 0
    for i, h in enumerate(held):
        idx = codes[offset:offset+len(h['y'])]
        offset += len(idx)
        sums[:, i, 0] = np.bincount(idx, weights=h['y'], minlength=len(people))
        sums[:, i, 1] = np.bincount(idx, minlength=len(people))
        losses = {n: horizon.binary_losses(h['y'], p) for n, p in h['predictions'].items()}
        for j, ((left, right), metric) in enumerate(itertools.product(pairs, metrics), 2):
            if metric.startswith('capture'):
                cap = metric.replace('capture', '')
                v = h['y'] * (h['allocations'][cap][left]-h['allocations'][cap][right]) * 100
            else:
                v = losses[left][metric]-losses[right][metric]
            sums[:, i, j] = np.bincount(idx, weights=v, minlength=len(people))
    denom_columns = [0 if m.startswith('capture') else 1 for _, m in itertools.product(pairs, metrics)]
    rng = np.random.default_rng(config['seed'])
    flat = sums.reshape(len(people), -1)
    draws = []
    for _ in range(config['bootstrap_repetitions']):
        w = np.bincount(rng.integers(len(people), size=len(people)), minlength=len(people))
        total = (w @ flat).reshape(len(held), width)
        draws.append(np.mean(total[:, 2:] / total[:, denom_columns], axis=0))
    total = sums.sum(axis=0)
    point = np.mean(total[:, 2:] / total[:, denom_columns], axis=0)
    ci = np.quantile(np.array(draws), [.025, .975], axis=0)
    return [{'left': pair[0], 'right': pair[1], 'metric': metric, 'difference': point[j],
             'ci95': ci[:, j]} for j, (pair, metric) in enumerate(itertools.product(pairs, metrics))]


def summarize(periods, intervals, config):
    summary = {}
    for name in NAMES:
        rows = [p['evaluation'][name] for p in periods]
        global_metrics = {k: float(np.mean([r['global'][k] for r in rows])) for k in rows[0]['global']
                          if all(isinstance(r['global'][k], (float, int, np.number)) for r in rows)}
        summary[name] = {'label': NAMES[name], 'global': global_metrics, 'scenarios': {}}
        for fraction in config['capacity_fractions']:
            cap = str(int(fraction*100))
            metrics = [r['scenarios'][cap]['metrics'] for r in rows]
            summary[name]['scenarios'][cap] = {k: float(np.mean([m[k] for m in metrics])) for k in metrics[0]
                if all(isinstance(m[k], (float, int, np.number)) for m in metrics)}
    decisions = {}
    guard = config['preference']
    for name in ['CQ', 'CQ_scalar']:
        caps = {}
        for frac in config['capacity_fractions']:
            cap = str(int(frac*100))
            baseline = summary['C']['scenarios'][cap]
            metric = summary[name]['scenarios'][cap]
            win = [p['evaluation'][name]['scenarios'][cap]['metrics']['capture_percent'] >
                   p['evaluation']['C']['scenarios'][cap]['metrics']['capture_percent'] + 1e-9 for p in periods]
            ci = next(r for r in intervals if r['left'] == name and r['right'] == 'C' and r['metric'] == 'capture'+cap)
            available = 'C_availability_scalar' if name.endswith('scalar') else 'C_availability'
            checks = {'capture_wins_both_periods': all(win), 'capture_ci_lower_positive': ci['ci95'][0] > 0,
                'group_error': metric['group_mae_pp'] <= baseline['group_mae_pp'] + guard['maximum_group_error_worsening_pp'],
                'group_snapshot_error': metric['group_snapshot_mae_pp'] <= baseline['group_snapshot_mae_pp'] + guard['maximum_group_error_worsening_pp'],
                'log_loss': summary[name]['global']['log_loss'] <= summary['C']['global']['log_loss']*(1+guard['maximum_relative_log_loss_worsening']),
                'brier': summary[name]['global']['brier_score'] <= summary['C']['global']['brier_score']*(1+guard['maximum_relative_brier_worsening']),
                'incremental_capture_vs_availability': metric['capture_percent'] > summary[available]['scenarios'][cap]['capture_percent'],
                'incremental_loss_vs_availability': summary[name]['global']['log_loss'] <= summary[available]['global']['log_loss']}
            caps[cap] = {'checks': checks, 'meets_rule': all(checks.values()), 'winning_periods': sum(win),
                         'capture_difference_pp': ci['difference'], 'capture_ci95_pp': ci['ci95']}
        decisions[name] = caps
    return summary, decisions


def run(path):
    started = time.perf_counter()
    config = base.read(path)
    out = ROOT / config['output']
    if (out / 'started.json').exists() or (out / 'results.json').exists():
        raise RuntimeError('Run existente; utilizar nueva carpeta para repetir.')
    source_config = base.read(ROOT / config['source_c'] / 'frozen-config.json')
    qconfig = load_config(ROOT / config['source_qvoice_config'])
    metadata = base.read(ROOT / config['source_qvoice'] / 'preflight/source-metadata.json')
    bank = catalog(config)
    preserved_dirs = [config['source_c'], config['source_grouping'], config['source_qvoice'],
        'output/analysis/engineering/20261008/qvoice-horizon-calibration-v1',
        'output/analysis/engineering/20261003/playbook-group-selection-v1',
        'output/analysis/engineering/20261008/bc-priority-comparison-v1']
    before = {str(p.relative_to(ROOT)): base.sha(p) for folder in preserved_dirs
              for p in (ROOT/folder).rglob('*') if p.is_file()}
    with base.db.connect() as conn:
        conn.set_session(readonly=True, autocommit=True)
    write(out / 'started.json', {'started_at': datetime.now(timezone.utc), 'status': 'running'})
    write(out / 'frozen-config.json', config)
    files = [path, Path(__file__), ROOT/config['query'], ROOT/config['authorization'], ROOT/config['source_qvoice_config'],
        ROOT/'config/qvoice_annual_lag_policy_20261008.json', ROOT/'docs/plans/attrition-model-c-plus-qvoice-20261008.md',
        ROOT/'tools/engineering_model_c.py', ROOT/'tools/engineering_c_group_selection.py',
        ROOT/'tools/compare_engineering_bc_priority.py', ROOT/'tools/qvoice_calibrated_model.py',
        ROOT/'tools/qvoice_horizon_calibration.py', ROOT/'tools/qvoice_model_data.py',
        ROOT/'tools/qvoice_model_experiment.py', ROOT/'tools/qvoice_model_validation.py']
    for file in files:
        target = out/'source'/file.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, target)
    write(out/'frozen-sources.json', {str(f.relative_to(ROOT)): base.sha(f) for f in files})
    salt = secrets.token_hex(32)
    base.log('Carga única 2025–2026; cuatro C archivados, cero ajustes del hazard base.')
    frame = load_frame(config, source_config, salt)
    population = frame.groupby('snapshot_date').agg(exposures=('person_key', 'size'), people=('person_key', 'nunique'),
        monthly_labeled=('y_next', 'count'), six_month_labeled=('y_6m', 'count')).reset_index()
    previous = pd.DataFrame(base.read(ROOT/config['source_c']/'population.json'))
    previous['snapshot_date'] = pd.to_datetime(previous.snapshot_date)
    previous = previous.loc[previous.snapshot_date >= config['training_start']].reset_index(drop=True)
    if not population.equals(previous):
        raise RuntimeError('La población o madurez cambió respecto de C.')
    write(out/'population.json', population.to_dict('records'))
    blocks = qconfig['search']['blocks']
    features = list(dict.fromkeys([f for fs in blocks.values() for f in fs]+qconfig['search']['pca_items']))
    timing = {}
    frame = horizon.attach_selected(frame, qconfig, metadata, salt, features, timing)
    del salt
    for f in features:
        frame['av_'+f] = pd.Series(np.where(frame[f].astype(str).isin(VALID), 'available', frame[f].astype(str)),
                                   index=frame.index).astype('category')
    wave_correct = (frame.qvoice_wave.astype(str).to_numpy() == (frame.snapshot_date.dt.year-1).astype(str).to_numpy()).all()
    if not wave_correct:
        raise RuntimeError('No se cumple la regla anual de QVoice.')
    coverage = []
    for wave, part in frame.groupby('qvoice_wave', observed=True):
        for f in features:
            counts = part[f].value_counts()
            valid = int(part[f].astype(str).isin(VALID).sum())
            coverage.append({'wave': str(wave), 'feature': f, 'exposures': len(part), 'valid_exposures': valid,
                'valid_percent': 100*valid/len(part),
                'states': {str(k): int(v) if v >= 30 or v == 0 else None for k, v in counts.items()}})
    write(out/'qvoice-input-checks.json', {'source_metadata': str((ROOT/config['source_qvoice']/'preflight/source-metadata.json').relative_to(ROOT)),
        'source_hashes_reconciled': True, 'annual_assignment_correct': bool(wave_correct),
        'population_reconciled': True, 'duplicate_person_snapshots': 0,
        'coverage_person_snapshot': coverage, 'score_changes': False})
    monthly = frame.loc[frame.y_next.notna()]
    direct = frame.loc[frame.y_6m.notna()]
    load_seconds = time.perf_counter()-started
    base.log(f'Datos y QVoice listos en {load_seconds:.1f} s; población reconciliada con C.')
    # Comparación global idéntica al último fold C y a la extensión ya archivada.
    original = base.read(ROOT/config['source_c']/'results.json')['folds'][-1]
    check_frame = base.evaluation(frame, original['origin'], 6, config['knowledge_boundary'])
    final_C = bank[-1][1]
    reproduction = prior.compare_metrics(base.metrics(check_frame, final_C.risk(check_frame)), original['C'], 1e-8, 'C archivado')
    if np.max(np.abs(risk(final_C, check_frame, 0.)-final_C.risk(check_frame))) > 1e-12:
        raise RuntimeError('El riesgo con corrección cero no reproduce C.')
    del check_frame
    periods, held, cache = [], [], {}
    for period in config['periods']:
        tick = time.perf_counter()
        target = out/'folds'/period['id']
        spec, selection = search(monthly, period['origin'], bank, config, qconfig, target)
        origin, model, reference = model_before(bank, period['origin'])
        train = monthly.loc[monthly.label_end <= pd.Timestamp(period['origin'])]
        fitted = fit_corrections(train, model, spec)
        calibrators = calibrate(monthly, direct, period['origin'], bank, spec, config, cache, target)
        test = direct.loc[(direct.snapshot_date >= period['origin']) & (direct.snapshot_date <= period['end'])]
        if test.snapshot_date.nunique() != period['snapshots']:
            raise RuntimeError('Periodo externo incompleto.')
        pred = predictions(model, test, fitted, spec)
        rank_checks = {}
        for name, p in list(pred.items()):
            pred[name+'_scalar'] = horizon.transform_risk(p, calibrators[name]['log_multiplier'])
            rank_checks[name] = bool(np.array_equal(np.argsort(p, kind='stable'), np.argsort(pred[name+'_scalar'], kind='stable')))
        if not all(rank_checks.values()):
            raise RuntimeError('El escalar cambió el ranking individual.')
        ev, allocations = evaluate(test, pred, config)
        record = {**period, 'first_snapshot': str(test.snapshot_date.min().date()), 'last_snapshot': str(test.snapshot_date.max().date()),
            'latest_outcome': str(test.r6_end.max().date()), 'exposures': len(test), 'people': test.person_key.nunique(),
            'selected': spec, 'C_origin': str(origin.date()), 'calibrators': calibrators,
            'evaluation': ev, 'individual_rank_preserved_by_scalar': rank_checks, 'seconds': time.perf_counter()-tick}
        write(target/'model.json', export(model, reference, origin, fitted, spec, period['origin'], train, calibrators))
        write(target/'evaluation.json', record)
        periods.append(record)
        held.append({'keys': test.person_key.to_numpy(), 'y': test.y_6m.to_numpy(float), 'predictions': pred, 'allocations': allocations})
        base.log(f'Periodo {period["id"]} terminado: {record["seconds"]:.1f} s.')
    intervals = uncertainty(held, config)
    aggregate, decisions = summarize(periods, intervals, config)
    write(out/'retrospective-results.json', {'periods': periods, 'summary': aggregate, 'decisions': decisions, 'intervals': intervals})
    base.log('Evaluación completa; selección y archivo de C + Q al corte final de conocimiento.')
    target = out/'trained-model'
    spec, selection = search(monthly, config['knowledge_boundary'], bank, config, qconfig, target)
    origin, model, reference = model_before(bank, config['knowledge_boundary'])
    train = monthly.loc[monthly.label_end <= pd.Timestamp(config['knowledge_boundary'])]
    fitted = fit_corrections(train, model, spec)
    calibrators = calibrate(monthly, direct, config['knowledge_boundary'], bank, spec, config, cache, target)
    write(target/'model.json', export(model, reference, origin, fitted, spec, config['knowledge_boundary'], train, calibrators))
    unchanged = all(base.sha(ROOT/path) == digest for path, digest in before.items())
    if not unchanged:
        raise RuntimeError('Cambió un artefacto anterior.')
    result = {'run_id': config['run_id'], 'created_at': datetime.now(timezone.utc), 'reporting_mode': 'presentation',
        'query': config['query'], 'knowledge_boundary': config['knowledge_boundary'], 'periods': periods,
        'summary': aggregate, 'decisions': decisions, 'intervals': intervals, 'final_selected': spec,
        'load_seconds': load_seconds, 'elapsed_seconds': time.perf_counter()-started,
        'base_refits': 0, 'employee_level_rows_persisted': False, 'individual_scores_published': False}
    write(out/'results.json', result)
    write(out/'preservation.json', {'unchanged': unchanged, 'sha256_before_after': before})
    write(out/'analysis-checks.json', {'C_reproduction': reproduction, 'population_reproduced': True,
        'query_C_unchanged_except_episode_flags': True, 'annual_wave_assignment': True, 'zero_correction_reproduces_C': True,
        'capacity_conserved_each_snapshot': True, 'capture_reconciled_to_direct_arrays': True,
        'scalar_individual_ranking_preserved': True, 'prior_artifacts_unchanged': unchanged,
        'employee_rows_persisted': False, 'base_refits': 0})
    write(out/'completed.json', {'status': 'completed_analysis', 'seconds': result['elapsed_seconds']})
    write(out/'manifest.json', {'status': 'completed_analysis', 'run_id': config['run_id'], 'reporting_mode': 'presentation',
        'authorization': config['authorization'], 'employee_level_rows_persisted': False, 'individual_scores_published': False,
        'salt_persisted': False, 'files': {str(p.relative_to(out)): base.sha(p) for p in out.rglob('*') if p.is_file() and p.name != 'manifest.json'}})
    base.log(f'C + QVoice terminado en {result["elapsed_seconds"]:.1f} s; cero reajustes del hazard C.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        run(args.config.resolve())
