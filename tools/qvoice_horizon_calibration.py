"""Calibración retrospectiva de R6, sin repetir selección ni persistir filas."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import sys
import time

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.optimize import minimize_scalar
from threadpoolctl import threadpool_limits

import qvoice_calibrated_model as old
from qvoice_model_data import ROOT, load_config, sha256_file, utc_now, write_json, scan_wave, components_for, availability_date
from qvoice_model_experiment import read_model_frame, modeling_frames, wave_feature_values
from qvoice_model_validation import add_interactions, INTERACTIONS, frame_metrics, period_frame


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


@contextmanager
def timed(timings, name):
    start = time.perf_counter()
    old.log(name)
    yield
    timings[name] = time.perf_counter() - start
    old.log(f'{name}: {timings[name]:.1f} s.')


def category_matrix(encoder, frame):
    """Una columna no nula por feature; mismo orden y referencias que el encoder."""
    n = len(frame)
    rows, cols = [np.arange(n)], [np.zeros(n, dtype=int)]
    offset = 1
    for name in encoder.features:
        cats = [v for v in encoder.levels[name] if v != encoder.references[name]]
        codes = pd.Categorical(frame[name].astype(str), categories=cats).codes
        valid = codes >= 0
        rows.append(np.flatnonzero(valid))
        cols.append(codes[valid].astype(int) + offset)
        offset += len(cats)
    row, col = np.concatenate(rows), np.concatenate(cols)
    return sparse.csr_matrix((np.ones(len(row)), (row, col)), shape=(n, len(encoder.columns)))


def categorical_eta(encoder, beta, frame):
    """Suma directa: categorías desconocidas contribuyen cero, igual al original."""
    coefficients = dict(zip(encoder['columns'], beta))
    result = np.full(len(frame), coefficients['intercept'], dtype=float)
    for name in encoder['features']:
        mapping = {col.split('=', 1)[1]: value for col, value in coefficients.items()
                   if col.startswith(name + '=')}
        values = frame[name].astype(object).fillna('(unknown)').astype(str)
        result += values.map(mapping).fillna(0).to_numpy(float)
    return result


def base_eta_fast(base, frame):
    encoder = base['encoder']
    if encoder.get('mode') != 'none' or 'time_index' in encoder['columns']:
        raise ValueError('El predictor optimizado sólo admite B sin tendencia.')
    raw = set(encoder['features']) - set(INTERACTIONS) - {'calendar_month'}
    raw |= {name for pair in INTERACTIONS.values() for name in pair}
    prepared = add_interactions(frame[['snapshot_date'] + sorted(raw)], base['interaction_references'])
    return categorical_eta(encoder, base['beta'], prepared)


def risk_fast(base, frame, correction, calibration=None):
    cal = calibration or {'intercept': 0., 'slope': 1.}
    a, b = cal['intercept'], cal['slope']
    calendar = np.zeros(13)
    for name, value in zip(base['encoder']['columns'], base['beta']):
        if name.startswith('calendar_month='):
            calendar[int(name.split('=')[1])] = value
    month = frame.snapshot_date.dt.month.to_numpy()
    fixed = base_eta_fast(base, frame) - calendar[month] + correction
    future = (month[:, None] - 1 + np.arange(6)) % 12 + 1
    cumulative = np.exp(np.clip(a + b * fixed, -30, 5)) * np.exp(b * calendar[future]).sum(axis=1)
    return np.clip(-np.expm1(-cumulative), 1e-8, 1 - 1e-8)


def predict_saved(artifact, frame, previous_calibration=False):
    correction = artifact['correction']
    if correction['kind'] != 'blocks':
        raise ValueError('Este experimento reutiliza las selecciones categóricas guardadas.')
    residual = categorical_eta(correction['encoder'], correction['beta'], frame)
    cal = artifact['calibration'] if previous_calibration else None
    return risk_fast(artifact['base'], frame, residual, cal)


def transform_risk(p, a):
    p = np.asarray(p, float)
    if not np.isfinite(p).all() or ((p <= 0) | (p >= 1)).any():
        raise ValueError('Riesgo fuera del dominio abierto (0,1).')
    return -np.expm1(np.exp(float(a)) * np.log1p(-p))


def binary_losses(y, p):
    p = np.clip(np.asarray(p, float), 1e-15, 1-1e-15)
    y = np.asarray(y, float)
    return {'log_loss': -y*np.log(p)-(1-y)*np.log1p(-p), 'brier_score': (y-p)**2}


def fit_scalar(y, p, bounds):
    y, p = np.asarray(y, float), np.asarray(p, float)
    if y.shape != p.shape or not len(y) or not np.isin(y, [0., 1.]).all():
        raise ValueError('Etiquetas inválidas para calibración binaria.')
    objective = lambda a: float(binary_losses(y, transform_risk(p, a))['log_loss'].mean())
    fit = minimize_scalar(objective, bounds=tuple(bounds), method='bounded', options={'xatol': 1e-10})
    if not fit.success:
        raise ValueError('No convergió el escalar.')
    a = float(fit.x) if fit.fun < objective(0.) else 0.
    return {'log_multiplier': a, 'multiplier': float(np.exp(a)), 'converged': True,
            'identity_fit_log_loss': objective(0.), 'scalar_fit_log_loss': objective(a),
            'at_bound': bool(min(abs(a-bounds[0]), abs(a-bounds[1])) < 1e-5)}


def auxiliary_training(monthly, origin, settings):
    eligible = monthly.loc[monthly.label_end <= pd.Timestamp(origin)]
    dates = sorted(eligible.snapshot_date.unique())
    reserved = settings['reserved_monthly_intervals']
    if len(dates) <= reserved:
        return eligible.iloc[:0]
    # Coincide con el tramo final de split_months, sin repetir selección.
    fit_boundary = pd.Timestamp(dates[-reserved])
    return eligible.loc[eligible.label_end <= fit_boundary]


def eligible_origins(monthly, direct, cutoff, settings):
    result = []
    for origin in sorted(direct.snapshot_date.unique()):
        origin = pd.Timestamp(origin)
        if origin + pd.DateOffset(months=6) > pd.Timestamp(cutoff):
            continue
        train = auxiliary_training(monthly, origin, settings)
        q = train.loc[train.qvoice_wave.astype(str) != 'ninguna']
        if q.snapshot_date.nunique() >= settings['minimum_qvoice_training_intervals'] and q.event_count.sum() >= 30:
            result.append(origin)
    return result[-settings['maximum_calibration_origins']:]


def attach_selected(frame, config, metadata, salt, features, timing):
    """Mismo parser y regla de join; sólo calcula las columnas usadas por los JSON."""
    requested = {f[3:] for f in features if f != 'qv_mean33'}
    if 'qv_mean33' in features:
        requested |= {f'M{i:02d}' for i in range(1, 34)}
    local_config = deepcopy(config)
    local_config['candidates'] = [{'id': 'selected', 'components': sorted(requested)}]
    result = frame.copy()
    for name in features:
        result[name] = 'no_available_wave'
    result['qvoice_wave'] = 'ninguna'
    waves = sorted((availability_date(w), w) for w in config['sources']['waves'])
    if len({date for date, _ in waves}) != len(waves):
        raise ValueError('Waves con fechas ambiguas.')
    for i, (known, wave) in enumerate(waves):
        expiration = known + pd.DateOffset(months=config['temporal_rules']['maximum_age_months'])
        if i+1 < len(waves):
            expiration = min(expiration, waves[i+1][0])
        mask = (result.snapshot_date >= known) & (result.snapshot_date < expiration)
        if not mask.any():
            continue
        meta = deepcopy(next(m for m in metadata['waves'] if m['year'] == wave['year']))
        if sha256_file(ROOT / wave['file']) != meta['sha256']:
            raise ValueError('Cambió la fuente QVoice.')
        # Heartbeat está excluido; no modifica ningún valor binario solicitado.
        for entry in meta['mapping'].values():
            entry['scale_indices'] = []
        with timed(timing, f'Lectura y enlace wave {wave["year"]}'):
            source = scan_wave(wave, meta, requested)
            lookup = {hashlib.md5((str(key)+salt).encode()).hexdigest():
                      wave_feature_values(value, wave, local_config) for key, value in source.rows.items()}
            indices = result.index[mask]
            selected = result.loc[indices, 'person_key'].astype(object).map(lookup)
            same_episode = result.loc[indices, f'same_episode_{wave["year"]}'].eq(1)
            for name in features:
                values = selected.map(lambda x: x.get(name, 'question_absent') if isinstance(x, dict) else 'no_linked_row')
                values.loc[~same_episode] = 'different_employment_episode'
                result.loc[indices, name] = values
            result.loc[indices, 'qvoice_wave'] = str(wave['year'])
            del source, lookup, selected
    for name in features + ['qvoice_wave']:
        result[name] = result[name].astype('category')
    return result


def metrics(frame, p):
    result = frame_metrics(frame, p)
    result['log_loss'] = float(binary_losses(frame.event_count.to_numpy(float), p)['log_loss'].mean())
    return result


def paired_loss_intervals(frame, predictions, settings):
    """Bootstrap por persona; suma las pérdidas antes de remuestrear, sin reordenar scores."""
    codes, people = pd.factorize(frame.person_key, sort=False)
    n = len(people)
    count = np.bincount(codes, minlength=n)
    y = frame.event_count.to_numpy(float)
    losses = {name: binary_losses(y, p) for name, p in predictions.items()}
    pairs = [('scalar', 'uncalibrated'), ('uncalibrated', 'control'), ('previous', 'uncalibrated')]
    keys, sums = [], []
    for a, b in pairs:
        for metric in ('log_loss', 'brier_score'):
            keys.append((a, b, metric))
            sums.append(np.bincount(codes, weights=losses[a][metric]-losses[b][metric], minlength=n))
    summed = np.column_stack(sums)
    rng = np.random.default_rng(settings['bootstrap_seed'])
    results = []
    for _ in range(settings['bootstrap_repetitions']):
        weights = np.bincount(rng.integers(n, size=n), minlength=n)
        results.append((weights @ summed) / (weights @ count))
    values = np.asarray(results)
    return [{'left': a, 'right': b, 'metric': metric, 'difference': float(summed[:, i].sum()/len(frame)),
             'ci95': np.quantile(values[:, i], [.025, .975]).tolist()} for i, (a, b, metric) in enumerate(keys)]


def benchmark(artifact, frame):
    sample = frame.iloc[:min(20000, len(frame))]
    # Calentar ambas rutas y alternar el orden de las mediciones.
    old.predict_artifact(artifact, sample.iloc[:100])
    predict_saved(artifact, sample.iloc[:100], True)
    durations = {'original': [], 'optimized': []}
    predictions = {}
    for repeat in range(3):
        for name in (['original', 'optimized'] if repeat % 2 == 0 else ['optimized', 'original']):
            start = time.perf_counter()
            predictions[name] = (old.predict_artifact(artifact, sample) if name == 'original'
                                 else predict_saved(artifact, sample, True))
            durations[name].append(time.perf_counter()-start)
    error = float(np.max(np.abs(predictions['original']-predictions['optimized'])))
    if error > 1e-12:
        raise ValueError('La predicción optimizada no reproduce el modelo guardado.')
    medians = {key: float(np.median(value)) for key, value in durations.items()}
    return {'rows': len(sample), 'repetitions': 3, 'seconds_median': medians,
            'speedup': medians['original']/medians['optimized'], 'maximum_absolute_difference': error}


def render_report(result, destination):
    def fmt(value):
        return f'{value:.1f}'.removesuffix('.0')
    lines = ['# B + QVoice: prueba de calibración a seis meses', '',
             '**Modo:** presentation. Evaluación retrospectiva; artefactos experimentales.', '',
             result['recommendation'], '', '## Resultados en las mismas cohortes', '',
             'Riesgo de salida voluntaria durante los seis meses siguientes a cada snapshot. '
             'Engineering: empleados regulares activos, excluyendo RF360. '
             'Los registros son persona-snapshot; una persona puede aparecer en varios meses.', '',
             '| Snapshots | Variante | Riesgo observado % | Riesgo estimado % | Error general pp | Error top 20% pp | Log-loss × 1000 | Brier × 1000 |',
             '|---|---|---:|---:|---:|---:|---:|---:|']
    names = {'control': 'B', 'uncalibrated': 'B + Q sin corrección', 'previous': 'Calibración mensual previa', 'scalar': 'Escalar a seis meses'}
    periods = {'aug_dec_2025': 'Ago–dic 2025', 'jan_feb_2026': 'Ene–feb 2026'}
    for row in result['periods']:
        for name, label in names.items():
            m = row['metrics'][name]
            label += ' (identidad)' if name == 'scalar' and row['calibration']['status'] == 'identity_insufficient_history' else ''
            values = [m['observed_percent'], m['predicted_percent'], m['calibration_error_pp'], m['top_quintile_calibration_error_pp'], m['log_loss']*1000, m['brier_score']*1000]
            lines.append('| '+periods[row['period']]+' | '+label+' | '+' | '.join(fmt(v) for v in values)+' |')
    lines += ['', 'Log-loss y Brier: menor es mejor. Se multiplican por 1000 para hacer '
              'visibles las diferencias sin añadir decimales. Error de calibración: '
              'distancia absoluta entre riesgo medio observado y estimado, en puntos porcentuales.', '',
              '## Cómo se aprendió el escalar', '',
              '`R_ajustada = 1 - (1 - R_sin)^exp(a)`. Un solo parámetro modifica el nivel '
              'y conserva exactamente el orden de riesgo acumulado. El ajuste minimiza log-loss '
              'a seis meses; el candidato sin corrección equivale a a = 0.', '']
    for row in result['calibration_details']:
        lines.append(f'- **{row["target"]}**, corte {row["cutoff"]}: {row["status"]}; '
                     f'{len(row["origins"])} orígenes; multiplicador {fmt(row["multiplier"])}. '
                     f'Orígenes: {", ".join(row["origins"]) or "ninguno admisible"}.')
    lines += ['', 'Cada ajuste auxiliar conserva dos intervalos mensuales reservados como el modelo '
              'guardado. Los primeros ajustes QVoice tienen sólo un intervalo de entrenamiento; '
              'el detalle por origen registra esta limitación. El calibrador sólo usa resultados '
              'a seis meses que ya habían terminado a su fecha de corte.', '', '## Ranking y magnitud', '']
    for row in result['periods']:
        m, b = row['metrics']['uncalibrated'], row['metrics']['control']
        c = row['metrics']['scalar']
        lines.append(f'- {periods[row["period"]]}: {row["people"]} personas, {int(m["exposures"])} registros, '
                     f'{int(m["event_exposures"])} registros con salida posterior. '
                     f'PR-AUC sin corrección mejora {fmt(100*(m["pr_auc"]/b["pr_auc"]-1))}% frente a B; '
                     f'lift del 10% superior: {fmt(m["lift_at_10_percent"])}. '
                     f'El escalar cambia log-loss {fmt(100*(c["log_loss"]/m["log_loss"]-1))}% '
                     f'y Brier {fmt(100*(c["brier_score"]/m["brier_score"]-1))}% frente a no corregir.')
    lines += ['', '## Rendimiento', '',
              f'- Ejecución de datos y modelos: {fmt(result["total_seconds"]/60)} minutos. '
              f'{result["fit_counts"]["base"]} ajustes B y {result["fit_counts"]["qvoice"]} correcciones QVoice; '
              'cero búsquedas de subconjuntos.',
              f'- Predicción optimizada: {fmt(result["benchmark"]["speedup"])} veces la velocidad en la misma '
              f'cohorte de {result["benchmark"]["rows"]} registros, mediana de tres repeticiones. '
              'Equivalencia numérica comprobada con tolerancia de 1e-12.',
              '- La reducción frente a la búsqueda previa combina menos ajustes y optimización; '
              'no representa ejecutar la misma búsqueda completa más rápido.', '',
              '## Límites y artefactos', '',
              '- Los periodos ya fueron inspeccionados. La selección de variables y L2 se hereda '
              'de una exploración posterior a algunos orígenes auxiliares; la validación es '
              'condicional y retrospectiva. Agosto de 2025 no prueba el escalar por falta de historia.',
              '- Las ventanas se solapan. El bootstrap por persona conserva esa repetición, pero '
              'no estima toda la incertidumbre por calendario, selección o entrenamiento.',
              '- La wave cambia entre 2025 y 2026; transportar el nivel de riesgo y la redacción '
              'Career añade incertidumbre. Estos resultados no demuestran causalidad.',
              '- El modelo final escalar queda como candidato experimental; también se guarda '
              'la versión final sin corrección. No se reemplaza B ni la presentación.',
              '- `comparison-results.json`: métricas precisas, diferencias pareadas y sus intervalos. '
              '`calibration-history.json`: cortes y métricas agregadas de los ajustes auxiliares. '
              '`timings.json`: tiempos por etapa. `trained-model/`: los dos candidatos.',
              f'- Fuente SQL: `{result["query"]}`. Ejecución: {result["created_at"]}. '
              f'Corte de datos: {result["knowledge_boundary"]}. '
              'No se guardan filas, identificadores ni scores individuales.', '']
    destination.write_text('\n'.join(lines), encoding='utf-8')


def run(settings_path):
    started = time.perf_counter()
    settings = read_json(settings_path)
    root, source = ROOT/settings['run_root'], ROOT/settings['source_run']
    if root.exists():
        raise FileExistsError('La ejecución ya existe; use una ruta nueva.')
    root.mkdir(parents=True)
    timing, fits = {}, {'base': 0, 'qvoice': 0}
    config = load_config(ROOT/settings['source_config'])
    if config['knowledge_boundary'] != settings['knowledge_boundary']:
        raise ValueError('Cortes incompatibles.')
    config['paths']['model_query'] = settings['model_query']
    source_manifest = read_json(source/'manifest.json')
    if source_manifest['status'] != 'completed':
        raise ValueError('La búsqueda anterior no está completa.')
    artifacts = {p['id']: read_json(source/'folds'/p['id']/'model.json') for p in config['validation']['main_periods']}
    artifacts['final'] = read_json(source/'trained-model/model.json')
    previous = read_json(source/'comparison-results.json')
    controls = read_json(source/'inputs/baseline-control-reference.json')
    metadata = read_json(source/'preflight/source-metadata.json')
    features = sorted({f for model in artifacts.values() for f in model['selected']['features']})
    inputs = root/'inputs'
    inputs.mkdir()
    files = [settings_path, ROOT/settings['source_config'], Path(__file__),
             ROOT/'tools/qvoice_calibrated_model.py', ROOT/'tools/qvoice_model_data.py',
             ROOT/'tools/qvoice_model_experiment.py', ROOT/'tools/qvoice_model_validation.py',
             ROOT/'tools/critical_tech_discrete_hazard_model.py', ROOT/'tools/engineering_hazard_adjustment.py',
             ROOT/'tools/engineering_playbook_priority_model.py',
             ROOT/config['authorization'], ROOT/config['temporal_policy_reference'],
             ROOT/'docs/plans/attrition-qvoice-horizon-calibration-20261008.md']
    for path in files:
        shutil.copy2(path, inputs/path.name)
    source_hashes = {str(p.relative_to(ROOT)).replace('\\', '/'): sha256_file(p) for p in source.rglob('*') if p.is_file()}
    write_json(root/'execution-contract.json', {'created_at': utc_now(), 'inputs': {str(p.relative_to(ROOT)): sha256_file(p) for p in files}, 'source_artifacts': source_hashes})
    write_json(root/'manifest.json', {'status': 'running', 'reporting_mode': 'presentation', **settings['privacy']})
    salt = secrets.token_hex(32)
    with timed(timing, 'Consulta Redshift y carga en memoria'):
        frame = read_model_frame(config, salt)
    with timed(timing, 'QVoice completo'):
        frame = attach_selected(frame, config, metadata, salt, features, timing)
    del salt
    with timed(timing, 'Preparación de etiquetas'):
        monthly, direct = modeling_frames(frame)
    del frame
    base_cache, bank, history, details = {}, {}, [], []

    def calibrator(target, cutoff):
        artifact = artifacts[target]
        origins = eligible_origins(monthly, direct, cutoff, settings)
        info = {'target': target, 'cutoff': str(cutoff), 'origins': [str(d.date()) for d in origins]}
        if len(origins) < settings['minimum_calibration_origins']:
            info.update(status='identity_insufficient_history', log_multiplier=0., multiplier=1., converged=True)
        else:
            chunks = []
            for origin in origins:
                key = (origin, tuple(artifact['selected']['features']), artifact['selected']['l2'])
                if key not in bank:
                    with timed(timing, f'Ajuste auxiliar {target} / {origin.date()}'):
                        train = auxiliary_training(monthly, origin, settings)
                        if origin not in base_cache:
                            base_cache[origin] = old.export_base(old.fit_b(train, config))
                            fits['base'] += 1
                        base = base_cache[origin]
                        qtrain = old.survey_training(train)
                        encoder = old.CategoryEncoder.fit(qtrain, artifact['selected']['features'])
                        x = category_matrix(encoder, qtrain)
                        beta, ok, iterations = old.fit_offset(x, qtrain.event_count.to_numpy(float), base_eta_fast(base, qtrain), artifact['selected']['l2'])
                        fits['qvoice'] += 1
                        if not ok:
                            raise ValueError('No converge un ajuste auxiliar.')
                        test = direct.loc[direct.snapshot_date == origin]
                        if test.person_key.nunique() < 30 or test.loc[test.event_count > 0, 'person_key'].nunique() < 30:
                            raise ValueError('Cohorte auxiliar insuficiente.')
                        correction = categorical_eta(asdict(encoder), beta, test)
                        p = risk_fast(base, test, correction)
                        bank[key] = (test.event_count.to_numpy(float), p, test.person_key.to_numpy())
                        history.append({'target': target, 'origin': str(origin.date()),
                            'six_month_label_end': str((origin+pd.DateOffset(months=6)).date()),
                            'maximum_training_label_end': str(train.label_end.max().date()),
                            'qvoice_training_intervals': qtrain.snapshot_date.nunique(),
                            'training_people': qtrain.person_key.nunique(), 'training_event_exposures': int(qtrain.event_count.sum()),
                            'features': artifact['selected']['features'], 'qvoice_l2': artifact['selected']['l2'],
                            'converged': bool(ok), 'iterations': iterations, 'metrics': metrics(test, p)})
                        write_json(root/'calibration-history.json', {'reporting_mode': 'presentation', 'rows': history})
                chunks.append(bank[key])
            y = np.concatenate([v[0] for v in chunks])
            p = np.concatenate([v[1] for v in chunks])
            people = np.unique(np.concatenate([v[2] for v in chunks]))
            info.update(fit_scalar(y, p, settings['log_multiplier_bounds']))
            info.update(status='fitted', exposures=len(y), people=len(people), event_exposures=int(y.sum()))
        details.append(info)
        write_json(root/'calibration-details.json', details)
        return info

    periods, bench = [], None
    for period in config['validation']['main_periods']:
        target = period['id']
        cal = calibrator(target, period['start'])
        with timed(timing, f'Evaluación {target}'):
            test = period_frame(direct, period, config['knowledge_boundary'])
            if test.snapshot_date.nunique() != period['expected_snapshots'] or test.person_key.nunique() < 30:
                raise ValueError('Cohorte de prueba incompatible.')
            if bench is None:
                bench = benchmark(artifacts[target], test)
            eligible = monthly.loc[monthly.label_end <= pd.Timestamp(period['start'])]
            l2 = next(r['control']['l2'] for r in controls['periods'] if r['period'] == target)
            control = old.fit_b(eligible, config, l2)
            fits['base'] += 1
            p = predict_saved(artifacts[target], test)
            predictions = {'control': risk_fast(old.export_base(control), test, np.zeros(len(test))),
                           'uncalibrated': p, 'previous': predict_saved(artifacts[target], test, True),
                           'scalar': transform_risk(p, cal['log_multiplier'])}
            evaluated = {name: metrics(test, values) for name, values in predictions.items()}
            earlier = next(r for r in previous['periods'] if r['period'] == target)
            errors = {name: {metric: float(evaluated[name][metric]-earlier[old_name][metric])
                       for metric in earlier[old_name] if metric in evaluated[name]}
                      for name, old_name in [('control', 'control'), ('uncalibrated', 'uncalibrated'), ('previous', 'response')]}
            if any(abs(value) > 1e-8 for values in errors.values() for value in values.values()):
                raise ValueError('No se reconciliaron las métricas anteriores.')
            same_order = np.array_equal(np.argsort(p, kind='stable'), np.argsort(predictions['scalar'], kind='stable'))
            if not same_order:
                raise ValueError('La corrección alteró el orden de riesgo.')
            uncertainty = paired_loss_intervals(test, predictions, settings)
            periods.append({'period': target, 'first_snapshot': str(test.snapshot_date.min().date()),
                            'last_snapshot': str(test.snapshot_date.max().date()), 'people': test.person_key.nunique(),
                            'metrics': evaluated, 'calibration': cal, 'reconciliation_errors': errors,
                            'rank_order_identical': bool(same_order), 'paired_loss_intervals': uncertainty})
            write_json(root/'period-results.json', periods)
    final_cal = calibrator('final', config['knowledge_boundary'])
    release = root/'trained-model'
    release.mkdir()
    final_uncalibrated = deepcopy(artifacts['final'])
    final_uncalibrated.update(name='B + QVoice sin corrección posterior', calibration={'intercept': 0., 'slope': 1.},
                             source_run=settings['source_run'], validation_status='experimental_retrospective')
    final_uncalibrated.pop('base_only_calibration', None)
    final_uncalibrated['historical_monthly_calibration_removed'] = True
    write_json(release/'uncalibrated-model.json', final_uncalibrated)
    write_json(release/'scalar-model.json', {'schema_version': 1, 'name': 'B + QVoice con escalar de R6',
               'status': 'experimental', 'uncalibrated_model': 'uncalibrated-model.json',
               'uncalibrated_model_sha256': sha256_file(release/'uncalibrated-model.json'),
               'calibration': final_cal, 'formula': '1-(1-R6_uncalibrated)^exp(log_multiplier)',
               'knowledge_boundary': settings['knowledge_boundary'], 'reporting_mode': 'presentation', **settings['privacy']})
    checks = {r['period']: {m: r['metrics']['scalar'][m] <= r['metrics']['uncalibrated'][m] + 1e-14
                            for m in ['log_loss'] + settings['guardrails']}
              for r in periods if r['calibration']['status'] == 'fitted'}
    all_pass = bool(checks) and all(all(c.values()) for c in checks.values())
    recommendation = ('El escalar mejora o conserva los cuatro criterios frente a no corregir en el único periodo evaluable. '
                      'Conservarlo como candidato experimental y confirmar en nuevos periodos antes de sustituir B.' if all_pass else
                      'Conservar B + QVoice sin corrección posterior como candidato principal. '
                      'El nuevo escalar no mejora conjuntamente log-loss, Brier y calibración; no reemplazar B de la presentación.')
    result = {'experiment': settings['experiment_id'], 'created_at': utc_now(), 'reporting_mode': 'presentation',
              'knowledge_boundary': settings['knowledge_boundary'], 'query': settings['model_query'],
              'query_sha256': sha256_file(ROOT/settings['model_query']), 'periods': periods,
              'calibration_details': details, 'benchmark': bench, 'fit_counts': fits, 'checks': checks,
              'recommendation': recommendation, 'total_seconds': time.perf_counter()-started,
              'authorization': config['authorization'], **settings['privacy']}
    write_json(root/'comparison-results.json', result)
    write_json(root/'timings.json', {'stages_seconds': timing, 'total_seconds': result['total_seconds'], 'fit_counts': fits,
                                   'benchmark': bench, 'note': 'QVoice completo incluye sus dos subetapas; no sumar etapas anidadas.'})
    render_report(result, root/'informe.md')
    # Verificar inmutabilidad del run anterior y persistencia del escalar.
    unchanged = all(sha256_file(ROOT/path) == digest for path, digest in source_hashes.items())
    if not unchanged:
        raise ValueError('Cambió un artefacto del run anterior.')
    check_rows = [{'check': 'prior_run_unchanged', 'passed': unchanged},
                  {'check': 'all_previous_metrics_reconciled', 'passed': True},
                  {'check': 'rank_preserved_both_periods', 'passed': all(r['rank_order_identical'] for r in periods)},
                  {'check': 'prediction_equivalence_1e-12', 'passed': bench['maximum_absolute_difference'] <= 1e-12},
                  {'check': 'auxiliary_labels_before_origin', 'passed': all(r['maximum_training_label_end'] <= r['origin'] for r in history)},
                  {'check': 'calibration_labels_mature', 'passed': all(pd.Timestamp(d)+pd.DateOffset(months=6) <= pd.Timestamp(c['cutoff']) for c in details for d in c['origins'])}]
    if not all(c['passed'] for c in check_rows):
        raise ValueError('Falla en las comprobaciones finales.')
    write_json(root/'validation.json', {'checks': check_rows, 'status': 'passed'})
    shutil.copy2(ROOT/settings['model_query'], inputs/Path(settings['model_query']).name)
    write_json(root/'manifest.json', {'status': 'completed', 'created_at': utc_now(), 'reporting_mode': 'presentation',
               'authorization': config['authorization'], **settings['privacy'], 'validation': 'validation.json',
               'artifacts_sha256': {str(p.relative_to(root)).replace('\\', '/'): sha256_file(p) for p in root.rglob('*') if p.is_file() and p.name != 'manifest.json'}})
    old.log(f'Prueba terminada: {root.relative_to(ROOT)}; {result["total_seconds"]:.1f} s.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT/'config/qvoice_horizon_calibration_20261008.json')
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    with threadpool_limits(limits=2):
        run(args.config.resolve())
