"""Cierre C/CQ y prueba de solapamiento; ninguna fila ni llave sale de RAM."""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
import secrets
import shutil
import time

import numpy as np
import pandas as pd
from scipy import sparse
from threadpoolctl import threadpool_limits

import engineering_model_c as base
import engineering_model_c_qvoice as cq
import engineering_c_group_selection as groups
import compare_engineering_bc_priority as prior
import qvoice_calibrated_model as qm
import qvoice_horizon_calibration as horizon
from qvoice_model_data import load_config, favorable_band

ROOT = base.ROOT
write = groups.write
LABELS = {
    'C': 'C', 'CQ': 'C + Q archivado',
    'C_availability': 'C + disponibilidad',
    'overlap': 'Preguntas + promedio completo',
    'disjoint': 'Preguntas + promedio sin duplicación',
    'items_only': 'Sólo preguntas',
    'selected': 'Selección interna ampliada',
}
MEAN_ITEMS = [f'qv_M{i:02d}' for i in range(1, 34)]


def now():
    return datetime.now(timezone.utc).isoformat()


def load_frame(config, cconfig, original_config, salt, out):
    """Misma consulta CQ; una conexión por año y reintentos acotados."""
    authorization = base.read(ROOT/original_config['authorization'])
    if authorization['status'] != 'approved' or authorization['non_negotiable_controls']['disk_cache_of_rows']:
        raise RuntimeError('Autorización RAM no vigente.')
    source_query = ROOT/original_config['query']
    query = ROOT/config['query']
    if base.sha(query) != base.sha(source_query):
        raise RuntimeError('La copia SQL no coincide con CQ.')
    for name in ['metadata', 'region', 'comp_ratio_band', 'grade_family',
                 'acquisition_recorded', 'transfer_12m', 'transfer_history']:
        evidence = base.read(ROOT/original_config['source_c']/'input-evidence'/f'{name}.json')
        if evidence['outcome'] != 'pass' or base.sha(ROOT/evidence['query']) != evidence['sql_sha256']:
            raise RuntimeError('Cambió un contrato de entrada C.')
    expected = {'snapshot_date', 'person_key', 'label_end', 'y_next', 'y_6m',
                'company_tenure_band', 'tenure_julia_band', 'same_episode_2024',
                'same_episode_2025', 'same_episode_2026'} | set(base.raw_features(cconfig))
    template = query.read_text(encoding='utf-8')
    parts, executions = [], []
    for year in [2025, 2026]:
        tick = time.perf_counter()
        sql = base.db.validate_readonly(template.replace('__PERIOD_START__', f'{year}-01-01')
            .replace('__PERIOD_END__', min(f'{year}-12-31', config['knowledge_boundary']))
            .replace('__RUN_SALT__', salt))
        for attempt in range(3):
            conn, year_parts = None, []
            try:
                conn = base.db.connect()
                conn.set_session(readonly=True, autocommit=True)
                with conn.cursor() as cursor:
                    cursor.execute(sql)
                    cols = [x[0] for x in cursor.description]
                    if set(cols) != expected or set(cols) & base.db.SENSITIVE_OUTPUT_COLUMNS:
                        raise RuntimeError('Columnas fuera del contrato RAM.')
                    while True:
                        rows = cursor.fetchmany(50000)
                        if not rows:
                            break
                        part = pd.DataFrame(rows, columns=cols).drop(columns=['company_tenure_band', 'tenure_julia_band'])
                        for name in base.raw_features(cconfig):
                            part[name] = part[name].astype('category')
                        year_parts.append(part)
                parts.extend(year_parts)
                executions.append({'year': year, 'attempts': attempt+1, 'seconds': time.perf_counter()-tick,
                    'query': config['query'], 'sql_sha256': base.sha(query), 'completed_at': now()})
                write(out/'query-executions.json', executions)
                break
            except (base.db.psycopg2.OperationalError, base.db.psycopg2.InterfaceError) as error:
                failure = {'year': year, 'attempt': attempt+1, 'date': now(), 'error_type': type(error).__name__,
                    'categories': [key for key in ['timeout', 'ssl', 'refused', 'translate host', 'permission', 'network']
                                   if key in str(error).lower()]}
                fail_path = out/'connection-retries.json'
                write(fail_path, (base.read(fail_path) if fail_path.exists() else [])+[failure])
                if attempt == 2 or 'permission' in str(error).lower() or 'refused' in str(error).lower():
                    raise RuntimeError(f'Conexión read-only incompleta: {type(error).__name__}; consultar connection-retries.json.') from None
                base.log(f'Reintento de carga {year}; años completos permanecen en RAM.')
                time.sleep(3)
            finally:
                if conn is not None:
                    conn.close()
        base.log(f'Carga {year} terminada en {time.perf_counter()-tick:.1f} s.')
    frame = pd.concat(parts, ignore_index=True)
    del parts, sql
    for name in ['snapshot_date', 'label_end']:
        frame[name] = pd.to_datetime(frame[name])
    for name in base.raw_features(cconfig):
        frame[name] = frame[name].astype('category')
    frame['calendar_month'] = frame.snapshot_date.dt.month.astype(str).astype('category')
    frame['r6_end'] = frame.snapshot_date + pd.DateOffset(months=6)
    if frame.duplicated(['person_key', 'snapshot_date']).any():
        raise RuntimeError('Duplicados persona-snapshot.')
    for label in ['y_next', 'y_6m']:
        if not frame[label].dropna().isin([0, 1]).all():
            raise RuntimeError('Etiqueta fuera del dominio.')
    if frame.loc[frame.r6_end > pd.Timestamp(config['knowledge_boundary']), 'y_6m'].notna().any():
        raise RuntimeError('Seguimiento R6 incompleto.')
    population = frame.groupby('snapshot_date').agg(exposures=('person_key', 'size'), people=('person_key', 'nunique'),
        monthly_labeled=('y_next', 'count'), six_month_labeled=('y_6m', 'count')).reset_index()
    expected_pop = pd.DataFrame(base.read(ROOT/original_config['source_c']/'population.json'))
    expected_pop['snapshot_date'] = pd.to_datetime(expected_pop.snapshot_date)
    expected_pop = expected_pop.loc[expected_pop.snapshot_date >= '2025-01-01'].reset_index(drop=True)
    if not population.equals(expected_pop):
        raise RuntimeError('Población o etiquetas diferentes de C archivado.')
    write(out/'population.json', population.to_dict('records'))
    return frame


def mappings(metadata):
    maps = {}
    for wave in metadata['waves']:
        if wave['year'] not in [2024, 2025]:
            continue
        by_text = {v['base']: k for k, v in wave['mapping'].items() if k.startswith('M') and k[1:].isdigit()}
        maps[wave['year']] = {'qv_'+k: 'qv_'+by_text[v['base']] for k, v in wave['mapping'].items()
            if not k.startswith('M') and v['base'] in by_text}
    for feature in set(maps[2024]) | set(maps[2025]):
        if maps[2024].get(feature) != maps[2025].get(feature):
            raise RuntimeError('El mapping de un ítem duplicado no es estable entre waves.')
    return maps[2025]


def add_remaining(frame, features, mapping, target, out):
    duplicate = {f: mapping[f] for f in features if f != 'qv_mean33' and f in mapping}
    excluded = sorted(set(duplicate.values()))
    remaining = [f for f in MEAN_ITEMS if f not in excluded]
    if not remaining:
        raise RuntimeError('Promedio sin componentes.')
    raw = np.column_stack([frame[f].astype(object).map({'v0': 0., 'v1': 1.}).to_numpy(float) for f in MEAN_ITEMS])
    complete = np.isfinite(raw).all(axis=1)
    original_valid = frame.qv_mean33.astype(str).isin(cq.VALID).to_numpy()
    if not np.array_equal(complete, original_valid):
        raise RuntimeError('Elegibilidad de media no reproduce los 33 ítems.')
    columns = [MEAN_ITEMS.index(f) for f in remaining]
    sums = raw[complete][:, columns].sum(axis=1).astype(int)
    n = len(remaining)
    bands = np.select([100*sums < n*k for k in [50, 70, 80, 90, 100]],
                      ['<50', '50–69', '70–79', '80–89', '90–99'], default='100')
    # Recálculo escalar independiente sobre todas las configuraciones observadas.
    unique, counts = np.unique(raw[complete][:, columns].astype(np.int8), axis=0, return_counts=True)
    mismatches = 0
    for row, count in zip(unique, counts):
        expected = favorable_band(row.tolist(), required_count=n)
        total = int(row.sum())
        actual = next((label for upper, label in zip([50, 70, 80, 90, 100],
                        ['<50', '50–69', '70–79', '80–89', '90–99']) if 100*total < upper*n), '100')
        mismatches += int(count) * int(expected != actual)
    values = frame.qv_mean33.astype(object).to_numpy().copy()
    values[complete] = bands
    frame[target] = pd.Categorical(values)
    frame['av_'+target] = pd.Categorical(np.where(complete, 'available', values))
    # Reconciliación original independiente, sin confiar sólo en la máscara.
    totals = raw[complete].sum(axis=1).astype(int)
    original_bands = np.select([100*totals < 33*k for k in [50, 70, 80, 90, 100]],
        ['<50', '50–69', '70–79', '80–89', '90–99'], default='100')
    original_mismatches = int((original_bands != frame.loc[complete, 'qv_mean33'].astype(str).to_numpy()).sum())
    if mismatches or original_mismatches:
        raise RuntimeError('Recálculo de media inconsistente.')
    evidence = {'feature': target, 'semantic_type': 'derived_feature', 'formula': 'sum(favorable remaining)/count(remaining)',
        'individual_items_mapping': duplicate, 'excluded_items': excluded, 'remaining_items': remaining,
        'denominator': n, 'required_valid_original_items': 33, 'comparable_count': int(complete.sum()),
        'matched_count': int(complete.sum())-mismatches, 'mismatch_count': mismatches,
        'original_mean_mismatch_count': original_mismatches, 'match_rate_percent': 100.,
        'eligibility_changed_count': 0, 'date': now(), 'outcome': 'pass', 'score_changes': False,
        'method': 'Mapping por texto exacto y reconciliación de todas las combinaciones observadas en RAM.',
        'acceptance_rule': 'Cero discrepancias de mapping, bandas o elegibilidad.',
        'bands': ['<50', '50–69', '70–79', '80–89', '90–99', '100']}
    write(out/f'{target}-derivation.json', evidence)
    return evidence


def matrix_diagnostics(frame, features):
    encoder = qm.CategoryEncoder.fit(frame, features)
    x = horizon.category_matrix(encoder, frame)[:, 1:]
    n = len(frame)
    mean = np.asarray(x.mean(axis=0)).ravel()
    cov = (x.T@x).toarray()/n - np.outer(mean, mean)
    var = np.maximum(np.diag(cov), 0)
    keep = var > 1e-12
    labels = np.asarray(encoder.columns[1:])[keep]
    if not len(labels):
        return {'rows': n, 'columns': 0, 'status': 'constant'}
    corr = cov[np.ix_(keep, keep)]/np.sqrt(np.outer(var[keep], var[keep]))
    eigen = np.linalg.eigvalsh(corr)
    tol = max(1e-10, float(eigen[-1])*1e-10)
    rank = int((eigen > tol).sum())
    full = rank == len(labels)
    pairs = []
    for a, b in zip(*np.triu_indices(len(labels), 1)):
        if labels[a].split('=')[0] != labels[b].split('=')[0] and abs(corr[a, b]) >= .8:
            pairs.append({'left': labels[a], 'right': labels[b], 'correlation': float(corr[a, b])})
    vif = np.diag(np.linalg.inv(corr)) if full else None
    return {'rows': n, 'columns': len(labels), 'rank': rank, 'rank_deficiency': len(labels)-rank,
        'constant_columns': int((~keep).sum()), 'condition_number': float(np.sqrt(eigen[-1]/eigen[0])) if full else None,
        'condition_status': 'finite' if full else 'singular', 'vif_max': float(vif.max()) if full else None,
        'vif_status': 'identifiable' if full else 'not_identifiable',
        'vif_by_column': dict(zip(labels.tolist(), vif.tolist())) if full else None,
        'cross_feature_pairs_abs_ge_0_8': sorted(pairs, key=lambda x: -abs(x['correlation'])),
        'limitation': 'Diagnóstico de columnas indicadoras QVoice; no es importancia ni causalidad.'}


def diagnostics(frame, features, evidence=None):
    complete = np.ones(len(frame), dtype=bool)
    for f in features:
        complete &= frame[f].astype(str).isin(cq.VALID).to_numpy()
    result = {'features': features, 'all_rows': matrix_diagnostics(frame, features)}
    clean = frame.loc[complete].drop_duplicates(['person_key', 'qvoice_wave'])
    if len(clean) >= 30:
        result['complete_person_wave'] = matrix_diagnostics(clean, features)
        qitems = [f for f in features if f != 'qv_mean33' and not f.startswith('qv_remaining_')]
        raw = {f: clean[f].astype(object).map({'v0': 0., 'v1': 1.}).to_numpy(float) for f in qitems}
        if 'qv_mean33' in features or evidence:
            raw['mean33_continuous'] = np.column_stack([clean[f].astype(object).map({'v0': 0., 'v1': 1.}) for f in MEAN_ITEMS]).mean(axis=1)
        if evidence:
            raw['remaining_continuous'] = np.column_stack([clean[f].astype(object).map({'v0': 0., 'v1': 1.}) for f in evidence['remaining_items']]).mean(axis=1)
        values = pd.DataFrame(raw)
        correlations = values.corr()
        result['raw_correlations'] = [{'left': a, 'right': b, 'correlation': float(correlations.loc[a, b])}
            for i, a in enumerate(values.columns) for b in values.columns[i+1:] if pd.notna(correlations.loc[a, b])]
        result['complete_person_wave_count'] = len(clean)
    return result


def evaluate(frame, predictions, config, dims):
    keys = groups.encode(groups.cut_keys(frame, ['acquisition_recorded']))
    codes, count, names = groups.combined(keys, tuple(dims), True)
    entries, allocations = {}, {str(int(f*100)): {} for f in config['capacity_fractions']}
    for name, p in predictions.items():
        ctx = groups.Grouped(frame, p, codes, count, config, names)
        entry = {'global': base.metrics(frame, p), 'scenarios': {},
            'groups_minimum': int(ctx.eligible.sum(axis=1).min()), 'groups_maximum': int(ctx.eligible.sum(axis=1).max())}
        for fraction in config['capacity_fractions']:
            cap = str(int(100*fraction))
            w, low, high = ctx.allocation(fraction)
            m, rows = ctx.detail(w)
            if m.get('suppressed'):
                raise RuntimeError('Cohorte agregada no publicable.')
            allocations[cap][name] = w.ravel()[ctx.cells]
            entry['scenarios'][cap] = {'metrics': m, 'selected_groups': rows}
        entries[name] = entry
    common = prior.context(frame)
    for name, p in predictions.items():
        entries[name]['on_C_selection'], _ = prior.describe(common, p, allocations['30']['C'], codes)
    return entries, allocations


def verify_archived(evaluation, previous, tolerance):
    checks = []
    for name in ['C', 'CQ', 'C_availability']:
        for k, value in previous[name]['global'].items():
            if isinstance(value, (float, int)) and isinstance(evaluation[name]['global'].get(k), (float, int)):
                diff = abs(evaluation[name]['global'][k]-value)
                checks.append({'model': name, 'metric': k, 'difference': diff, 'pass': diff <= tolerance})
        for cap in ['20', '30', '40']:
            for k, value in previous[name]['scenarios'][cap]['metrics'].items():
                actual = evaluation[name]['scenarios'][cap]['metrics'].get(k)
                if isinstance(value, (float, int)) and isinstance(actual, (float, int)):
                    diff = abs(actual-value)
                    checks.append({'model': name, 'metric': cap+'/'+k, 'difference': diff, 'pass': diff <= tolerance})
    if not all(c['pass'] for c in checks):
        failures = [c for c in checks if not c['pass']]
        raise RuntimeError('No reproduce métricas archivadas: '+str(failures[:3]))
    return checks


def correction(encoder, beta, frame):
    return horizon.category_matrix(encoder, frame)@beta


def fit_representations(frame, monthly, origin, bank, selection, config, target, mapping):
    mean_trials = [r for r in selection['trials'] if r['converged'] and r['kind'] == 'blocks'
                   and 'qv_mean33' in r['features'] and len(r['features']) > 1]
    chosen = min(mean_trials, key=lambda r: (r['monthly_brier'], r['parameters'], -r['l2'], r['id']))
    derived_name = 'qv_remaining_'+str(origin).replace('-', '')
    derivation = add_remaining(frame, chosen['features'], mapping, derived_name, target)
    # Actualizar sólo los nuevos predictores en el frame mensual derivado.
    monthly[derived_name] = frame.loc[monthly.index, derived_name]
    monthly['av_'+derived_name] = frame.loc[monthly.index, 'av_'+derived_name]
    dates = pd.to_datetime(selection['selection_snapshots'])
    core = monthly.loc[monthly.label_end <= dates[0]]
    valid = monthly.loc[monthly.snapshot_date.isin(dates)]
    auxiliary_origin, auxiliary, _ = cq.model_before(bank, dates[0])
    if str(auxiliary_origin.date()) != selection['C_origin']:
        raise RuntimeError('Origen C de selección diferente.')
    train = monthly.loc[monthly.label_end <= pd.Timestamp(origin)]
    c_origin, model, reference = cq.model_before(bank, origin)
    offsets = {name: cq.eta(m, part) for name, m, part in
               [('core', auxiliary, core), ('valid', auxiliary, valid), ('train', model, train)]}
    features = {
        'overlap': chosen['features'],
        'disjoint': [derived_name if f == 'qv_mean33' else f for f in chosen['features']],
        'items_only': [f for f in chosen['features'] if f != 'qv_mean33'],
    }
    records, fitted = {}, {}
    for name, fs in features.items():
        tick = time.perf_counter()
        encoder = qm.CategoryEncoder.fit(core, fs)
        x, xv = horizon.category_matrix(encoder, core), horizon.category_matrix(encoder, valid)
        trials = []
        for l2 in config['l2_grid']:
            beta, converged, iterations = qm.fit_offset(x, core.y_next.to_numpy(float), offsets['core'], l2)
            if not converged:
                raise RuntimeError('No converge la prueba de representación.')
            score = float(np.mean((valid.y_next.to_numpy(float)-qm.hazard(offsets['valid']+xv@beta))**2))
            trials.append({'l2': l2, 'monthly_brier': score, 'iterations': iterations, 'converged': converged})
        winner = min(trials, key=lambda r: (r['monthly_brier'], -r['l2']))
        if name == 'overlap' and abs(winner['monthly_brier']-chosen['monthly_brier']) > 1e-10:
            raise RuntimeError('No reproduce selección interna archivada de la media.')
        encoder = qm.CategoryEncoder.fit(train, fs)
        x = horizon.category_matrix(encoder, train)
        beta, converged, iterations = qm.fit_offset(x, train.y_next.to_numpy(float), offsets['train'], winner['l2'])
        if not converged:
            raise RuntimeError('No converge corrección final de representación.')
        spec = {'name': name, 'features': fs, 'l2': winner['l2'], 'monthly_brier': winner['monthly_brier'],
            'source_candidate': chosen, 'trials': trials, 'iterations': iterations,
            'encoder': asdict(encoder), 'beta': beta, 'base_model_reference': reference,
            'base_model_origin': str(c_origin.date()), 'cutoff': str(origin),
            'fit_maximum_label_end': str(train.label_end.max().date()),
            'selection_snapshots': selection['selection_snapshots'],
            'formula': 'cloglog(eta_C + correccion_Q); R6 = 1-product(1-h)',
            'derivation': derivation if name == 'disjoint' else None,
            'parameters': len(beta), 'employee_level_rows_persisted': False}
        records[name] = spec
        fitted[name] = (encoder, beta)
        write(target/name/'model.json', spec)
        write(target/name/'collinearity.json', diagnostics(train, fs, derivation if name != 'items_only' else None))
        base.log(f'{origin}: {name}, L2 {winner["l2"]}; selección y ajuste {time.perf_counter()-tick:.1f} s.')
    options = [(selection['winner']['monthly_brier'], selection['winner']['parameters'], 'CQ')]
    options += [(r['monthly_brier'], r['parameters'], name) for name, r in records.items()]
    selected = min(options)[2]
    write(target/'selection.json', {'selected_representation': selected, 'original_winner': selection['winner'],
        'best_archived_mean_candidate': chosen, 'candidates': [{'representation': n, 'monthly_brier': b, 'parameters': p} for b, p, n in options],
        'selection_uses_outer_outcomes': False, 'scope': 'Subconjunto de media condicionado a selección previa, sin búsqueda exhaustiva nueva.'})
    return model, fitted, records, selected


def intervals(held, config):
    pairs = [(n, 'C') for n in ['CQ', 'overlap', 'disjoint', 'items_only', 'selected']]
    pairs += [('disjoint', 'overlap'), ('items_only', 'overlap'), ('selected', 'CQ'), ('CQ', 'C_availability')]
    metrics = ['capture20', 'capture30', 'capture40', 'log_loss', 'brier_score']
    keys = np.concatenate([h['keys'] for h in held])
    person, unique = pd.factorize(keys, sort=False)
    columns = [(a, b, m) for a, b in pairs for m in metrics]
    sums = np.zeros((len(unique), len(held), 2+len(columns)))
    offset = 0
    for j, h in enumerate(held):
        idx = person[offset:offset+len(h['y'])]
        offset += len(idx)
        sums[:, j, 0] = np.bincount(idx, weights=h['y'], minlength=len(unique))
        sums[:, j, 1] = np.bincount(idx, minlength=len(unique))
        losses = {n: horizon.binary_losses(h['y'], p) for n, p in h['predictions'].items()}
        for i, (a, b, m) in enumerate(columns, 2):
            value = (h['y']*(h['allocations'][m[7:]][a]-h['allocations'][m[7:]][b])*100
                     if m.startswith('capture') else losses[a][m]-losses[b][m])
            sums[:, j, i] = np.bincount(idx, weights=value, minlength=len(unique))
    den = [0 if m.startswith('capture') else 1 for _, _, m in columns]
    point_sum = sums.sum(axis=0)
    point = (point_sum[:, 2:]/point_sum[:, den]).mean(axis=0)
    flat = sums.reshape(len(unique), -1)
    rng = np.random.default_rng(config['seed'])
    draws = []
    for _ in range(config['bootstrap_repetitions']):
        weights = np.bincount(rng.integers(len(unique), size=len(unique)), minlength=len(unique))
        total = (weights@flat).reshape(len(held), -1)
        draws.append((total[:, 2:]/total[:, den]).mean(axis=0))
    ci = np.quantile(draws, [.025, .975], axis=0)
    return [{'left': a, 'right': b, 'metric': m, 'difference': float(point[i]), 'ci95': ci[:, i].tolist()}
            for i, (a, b, m) in enumerate(columns)]


def summary(periods, field='evaluation'):
    result = {}
    for name in periods[0][field]:
        rows = [p[field][name] for p in periods]
        def means(data):
            return {k: float(np.mean([d[k] for d in data])) for k in data[0]
                    if all(isinstance(d.get(k), (int, float, np.number)) for d in data)}
        result[name] = {'global': means([r['global'] for r in rows]),
            'scenarios': {cap: means([r['scenarios'][cap]['metrics'] for r in rows]) for cap in ['20', '30', '40']}}
    return result


def decisions(periods, stats, ci, original):
    output = {}
    guard = original['preference']
    for name in ['CQ', 'overlap', 'disjoint', 'items_only', 'selected']:
        a, b = stats[name], stats['C']
        wins = [p['evaluation'][name]['scenarios']['30']['metrics']['capture_percent'] >
                p['evaluation']['C']['scenarios']['30']['metrics']['capture_percent']+1e-9 for p in periods]
        interval = next(r for r in ci if r['left'] == name and r['right'] == 'C' and r['metric'] == 'capture30')
        checks = {'capture_wins_both_periods': all(wins), 'capture_ci_lower_positive': interval['ci95'][0] > 0,
            'group_error': a['scenarios']['30']['group_mae_pp'] <= b['scenarios']['30']['group_mae_pp']+.1,
            'group_snapshot_error': a['scenarios']['30']['group_snapshot_mae_pp'] <= b['scenarios']['30']['group_snapshot_mae_pp']+.1,
            'log_loss': a['global']['log_loss'] <= b['global']['log_loss']*1.005,
            'brier': a['global']['brier_score'] <= b['global']['brier_score']*1.005}
        if name == 'CQ':
            available = stats['C_availability']
            checks['incremental_capture_vs_availability'] = a['scenarios']['30']['capture_percent'] > available['scenarios']['30']['capture_percent']
            checks['incremental_loss_vs_availability'] = a['global']['log_loss'] <= available['global']['log_loss']
        output[name] = {'checks': checks, 'passes_comparable_checks': all(checks.values()), 'winning_periods': sum(wins),
            'capture_difference_pp': interval['difference'], 'capture_ci95_pp': interval['ci95'],
            'full_original_rule_evaluated': name == 'CQ',
            'automatic_replacement': False}
    return output


def run(config_path, resume=False):
    started = time.perf_counter()
    config = base.read(config_path)
    out = ROOT/config['output']
    if (out/'results.json').exists():
        raise RuntimeError('Run completo existente: usar otra carpeta.')
    if (out/'started.json').exists() and not resume:
        raise RuntimeError('Run iniciado: revisar interrupción y usar --resume.')
    original = base.read(ROOT/config['source_cq']/'frozen-config.json')
    cconfig = base.read(ROOT/original['source_c']/'frozen-config.json')
    qconfig = load_config(ROOT/original['source_qvoice_config'])
    metadata = base.read(ROOT/original['source_qvoice']/'preflight/source-metadata.json')
    mapping = mappings(metadata)
    preserved_dirs = [original['source_c'], config['source_cq'], config['source_bq'],
        'output/analysis/engineering/20261008/qvoice-horizon-calibration-v1',
        'output/analysis/engineering/20261008/c-fourway-groups-v1',
        'output/analysis/engineering/20261008/random-survival-forest-v1']
    before = {str(p.relative_to(ROOT)): base.sha(p) for folder in preserved_dirs for p in (ROOT/folder).rglob('*') if p.is_file()}
    if (out/'preservation-before.json').exists():
        if base.read(out/'preservation-before.json') != before:
            raise RuntimeError('Cambió una fuente durante la reanudación.')
    else:
        write(out/'preservation-before.json', before)
    files = [config_path, Path(__file__), ROOT/config['plan'], ROOT/config['query'], ROOT/original['authorization'],
        ROOT/original['source_qvoice_config'], ROOT/'config/qvoice_annual_lag_policy_20261008.json']
    files += [ROOT/'tools'/f for f in ['engineering_model_c.py', 'engineering_model_c_qvoice.py',
        'engineering_c_group_selection.py', 'compare_engineering_bc_priority.py', 'qvoice_calibrated_model.py',
        'qvoice_horizon_calibration.py', 'qvoice_model_data.py', 'qvoice_model_experiment.py']]
    for file in files:
        dest = out/'source'/file.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, dest)
    write(out/'frozen-config.json', config)
    write(out/'started.json', {'date': now(), 'status': 'running', 'resume': resume})
    write(out/'overlap-mapping.json', mapping)
    base.db.psycopg2.connect = partial(base.db.psycopg2.connect, keepalives=1,
        keepalives_idle=30, keepalives_interval=10, keepalives_count=3)
    salt = secrets.token_hex(32)
    frame = load_frame(config, cconfig, original, salt, out)
    features = list(dict.fromkeys([f for fs in qconfig['search']['blocks'].values() for f in fs]+MEAN_ITEMS))
    timings = {}
    frame = horizon.attach_selected(frame, qconfig, metadata, salt, features, timings)
    del salt
    if not (frame.qvoice_wave.astype(str).to_numpy() == (frame.snapshot_date.dt.year-1).astype(str).to_numpy()).all():
        raise RuntimeError('Wave fuera de la política anual.')
    for f in features:
        frame['av_'+f] = pd.Categorical(np.where(frame[f].astype(str).isin(cq.VALID), 'available', frame[f].astype(str)))
    monthly = frame.loc[frame.y_next.notna()].copy()
    bank = cq.catalog(original)
    periods, held, checks = [], [], []
    for period in original['periods']:
        target = out/'folds'/period['id']
        source = ROOT/config['source_cq']/'folds'/period['id']
        artifact = base.read(source/'model.json')
        selection = base.read(source/'selection.json')
        train = monthly.loc[monthly.label_end <= pd.Timestamp(period['origin'])]
        write(target/'archived-collinearity.json', diagnostics(train, artifact['selected']['features']))
        model, fitted, records, selected = fit_representations(frame, monthly, period['origin'], bank,
            selection, config, target, mapping)
        test = frame.loc[frame.y_6m.notna() & frame.snapshot_date.between(period['origin'], period['end'])].copy()
        if test.snapshot_date.nunique() != period['snapshots']:
            raise RuntimeError('Ventana externa incompleta.')
        archived_corr = horizon.categorical_eta(artifact['correction']['encoder'], artifact['correction']['beta'], test)
        archived_av = horizon.categorical_eta(artifact['availability_control']['encoder'], artifact['availability_control']['beta'], test)
        predictions = {'C': model.risk(test), 'CQ': cq.risk(model, test, archived_corr),
                       'C_availability': cq.risk(model, test, archived_av)}
        for name, (encoder, beta) in fitted.items():
            predictions[name] = cq.risk(model, test, correction(encoder, beta, test))
        predictions['selected'] = predictions[selected]
        evaluations, allocations = evaluate(test, predictions, original, original['groups'])
        previous = base.read(source/'evaluation.json')['evaluation']
        reconciled = verify_archived(evaluations, previous, config['reconciliation_absolute_tolerance'])
        checks += reconciled
        write(target/'reconciliation.json', {'outcome': 'pass', 'checks': reconciled})
        extra, _ = evaluate(test, predictions, original, original['groups']+['acquisition_recorded'])
        snapshot_rows = []
        for d, sub in test.groupby('snapshot_date', observed=True):
            positions = np.flatnonzero(test.snapshot_date.to_numpy() == d)
            ev, _ = evaluate(sub, {n: p[positions] for n, p in predictions.items()}, original, original['groups'])
            snapshot_rows.append({'snapshot': str(pd.Timestamp(d).date()), 'evaluation': ev})
        record = {**period, 'evaluation': evaluations, 'four_cuts_evaluation': extra,
            'monthly_evaluations': snapshot_rows, 'selected_representation': selected,
            'archived_mean_included': 'qv_mean33' in artifact['selected']['features'],
            'exposures': len(test), 'people': int(test.person_key.nunique()),
            'latest_outcome': str(test.r6_end.max().date())}
        write(target/'evaluation.json', record)
        periods.append(record)
        held.append({'keys': test.person_key.to_numpy(), 'y': test.y_6m.to_numpy(float),
                     'predictions': predictions, 'allocations': allocations})
        base.log(f'Periodo {period["id"]} reconciliado; selección interna: {selected}.')
    final_source = ROOT/config['source_cq']/'trained-model'
    final_artifact = base.read(final_source/'model.json')
    final_target = out/'trained-model'
    final_model, fitted, records, selected = fit_representations(frame, monthly, config['knowledge_boundary'], bank,
        base.read(final_source/'selection.json'), config, final_target, mapping)
    final_train = monthly.loc[monthly.label_end <= pd.Timestamp(config['knowledge_boundary'])]
    write(final_target/'archived-CQ-collinearity.json', diagnostics(final_train, final_artifact['selected']['features']))
    bq_artifact = base.read(ROOT/config['source_bq']/'trained-model/model.json')
    write(final_target/'archived-BQ-collinearity.json', diagnostics(final_train, bq_artifact['selected']['features']))
    # El artefacto de inferencia elegido puede apuntar al original; siempre se conserva como copia independiente.
    if selected == 'CQ':
        chosen_artifact = deepcopy(final_artifact)
        chosen_artifact['review_note'] = 'La selección interna ampliada conserva el CQ archivado; sin validación posterior nueva.'
    else:
        chosen_artifact = {**records[selected], 'base_model': final_model.artifact(),
            'name': 'C + QVoice revisión de solapamiento', 'status': 'experimental_retrospective',
            'post_fit_validation': False}
    write(final_target/'selected-model.json', chosen_artifact)
    base.log('Cálculo de incertidumbre por persona sobre resultados externos.')
    ci = intervals(held, config)
    stats = summary(periods)
    verdict = decisions(periods, stats, ci, original)
    result = {'date': now(), 'reporting_mode': 'presentation', 'periods': periods, 'summary': stats,
        'four_cuts_summary': summary(periods, 'four_cuts_evaluation'), 'intervals': ci, 'decisions': verdict,
        'final_selected_representation': selected, 'final_model_has_post_fit_validation': False,
        'new_independent_periods': 0, 'source_query': config['query'], 'source_query_sha256': base.sha(ROOT/config['query']),
        'authorization': original['authorization'], 'elapsed_seconds': time.perf_counter()-started,
        'survey_timings': timings, 'base_refits': 0, 'representation_fit_count': 36,
        'employee_level_rows_persisted': False, 'individual_scores_published': False, 'score_changes': False}
    after = {p: base.sha(ROOT/p) for p in before}
    if before != after:
        raise RuntimeError('Cambió un archivo de los modelos anteriores.')
    write(out/'preservation.json', {'outcome': 'pass', 'files': len(before), 'before_equals_after': True})
    write(out/'analysis-checks.json', {'outcome': 'pass', 'reconciliation_checks': len(checks),
        'all_reconciliations_pass': all(c['pass'] for c in checks), 'population_matches_C': True,
        'annual_policy_verified': True, 'source_models_preserved': True})
    write(out/'results.json', result)
    write(out/'verdict.json', verdict)
    write(out/'completed.json', {'date': now(), 'status': 'calculations_complete', 'seconds': time.perf_counter()-started})
    base.log(f'Cálculos terminados en {(time.perf_counter()-started)/60:.1f} minutos.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config/engineering_c_qvoice_overlap_20261009.json')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    with threadpool_limits(limits=2):
        run(ROOT/args.config, args.resume)
