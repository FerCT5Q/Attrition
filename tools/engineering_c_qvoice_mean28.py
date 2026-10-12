"""Backtest de una combinación QVoice fija con media 28; sólo agregados y parámetros."""
from pathlib import Path
from copy import deepcopy
from dataclasses import asdict
from functools import partial
import argparse
import secrets
import shutil
import time
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

import engineering_c_qvoice_overlap as shared
import engineering_model_c as base
import engineering_model_c_qvoice as cq
import qvoice_calibrated_model as qm
import qvoice_horizon_calibration as horizon
from qvoice_model_data import load_config

ROOT, write = shared.ROOT, shared.write


def uncertainty(held, config):
    pairs = [('CQ', 'C'), ('disjoint', 'C'), ('disjoint', 'CQ'), ('disjoint', 'overlap'),
             ('disjoint', 'items_only'), ('disjoint', 'mean28_availability'), ('overlap', 'C'), ('items_only', 'C')]
    metrics = ['capture20', 'capture30', 'capture40', 'log_loss', 'brier_score']
    columns = [(a, b, m) for a, b in pairs for m in metrics]
    codes, people = pd.factorize(np.concatenate([h['keys'] for h in held]), sort=False)
    sums = np.zeros((len(people), len(held), len(columns)+2))
    cursor = 0
    for j, h in enumerate(held):
        ids = codes[cursor:cursor+len(h['y'])]
        cursor += len(ids)
        sums[:, j, 0] = np.bincount(ids, weights=h['y'], minlength=len(people))
        sums[:, j, 1] = np.bincount(ids, minlength=len(people))
        losses = {name: horizon.binary_losses(h['y'], p) for name, p in h['predictions'].items()}
        for i, (a, b, metric) in enumerate(columns, 2):
            if metric.startswith('capture'):
                v = h['y']*(h['allocations'][metric[7:]][a]-h['allocations'][metric[7:]][b])*100
            else:
                v = losses[a][metric]-losses[b][metric]
            sums[:, j, i] = np.bincount(ids, weights=v, minlength=len(people))
    den = [0 if m.startswith('capture') else 1 for _, _, m in columns]
    total = sums.sum(axis=0)
    point = (total[:, 2:]/total[:, den]).mean(axis=0)
    flat = sums.reshape(len(people), -1)
    rng = np.random.default_rng(config['seed'])
    draws = []
    for _ in range(config['bootstrap_repetitions']):
        weights = np.bincount(rng.integers(len(people), size=len(people)), minlength=len(people))
        t = (weights@flat).reshape(len(held), -1)
        draws.append((t[:, 2:]/t[:, den]).mean(axis=0))
    bounds = np.quantile(draws, [.025, .975], axis=0)
    return [{'left': a, 'right': b, 'metric': m, 'difference': float(point[i]), 'ci95': bounds[:, i].tolist()}
            for i, (a, b, m) in enumerate(columns)]


def compare(periods, stats, intervals):
    output = {}
    for reference in ['C', 'CQ']:
        a, b = stats['disjoint'], stats[reference]
        differences = [p['evaluation']['disjoint']['scenarios']['30']['metrics']['capture_percent']-
                       p['evaluation'][reference]['scenarios']['30']['metrics']['capture_percent'] for p in periods]
        ci = next(r for r in intervals if r['left'] == 'disjoint' and r['right'] == reference and r['metric'] == 'capture30')
        output[reference] = {'capture_difference_pp': ci['difference'], 'capture_ci95_pp': ci['ci95'],
            'wins': sum(v > 1e-9 for v in differences), 'ties': sum(abs(v) <= 1e-9 for v in differences),
            'losses': sum(v < -1e-9 for v in differences), 'period_capture_differences_pp': differences,
            'checks': {'positive_capture_both_periods': all(v > 1e-9 for v in differences),
                'positive_capture_ci': ci['ci95'][0] > 0,
                'group_error_within_tolerance': a['scenarios']['30']['group_mae_pp'] <= b['scenarios']['30']['group_mae_pp']+.1,
                'group_snapshot_error_within_tolerance': a['scenarios']['30']['group_snapshot_mae_pp'] <= b['scenarios']['30']['group_snapshot_mae_pp']+.1,
                'log_loss_within_tolerance': a['global']['log_loss'] <= b['global']['log_loss']*1.005,
                'brier_within_tolerance': a['global']['brier_score'] <= b['global']['brier_score']*1.005}}
    output['own_availability_control'] = {
        'capture_gain_pp': stats['disjoint']['scenarios']['30']['capture_percent']-stats['mean28_availability']['scenarios']['30']['capture_percent'],
        'log_loss_difference': stats['disjoint']['global']['log_loss']-stats['mean28_availability']['global']['log_loss']}
    return output


def run(path, resume=False):
    start = time.perf_counter()
    config = base.read(path)
    out = ROOT/config['output']
    if (out/'results.json').exists() or ((out/'started.json').exists() and not resume):
        raise RuntimeError('Ejecución existente: revisar antes de reanudar o usar carpeta nueva.')
    original = base.read(ROOT/config['source_cq']/'frozen-config.json')
    cconfig = base.read(ROOT/original['source_c']/'frozen-config.json')
    qconfig = load_config(ROOT/original['source_qvoice_config'])
    metadata = base.read(ROOT/config['source_bq']/'preflight/source-metadata.json')
    mapping = shared.mappings(metadata)
    folders = [original['source_c'], config['source_cq'], config['source_bq'], config['source_overlap'],
        'output/analysis/engineering/20261008/c-fourway-groups-v1',
        'output/analysis/engineering/20261008/random-survival-forest-v1',
        'output/analysis/engineering/20261008/qvoice-horizon-calibration-v1']
    before = {str(p.relative_to(ROOT)): base.sha(p) for folder in folders for p in (ROOT/folder).rglob('*') if p.is_file()}
    if (out/'preservation-before.json').exists() and base.read(out/'preservation-before.json') != before:
        raise RuntimeError('Una fuente cambió durante la interrupción.')
    write(out/'preservation-before.json', before)
    files = [path, Path(__file__), ROOT/config['plan'], ROOT/config['query'], ROOT/original['authorization'],
        ROOT/original['source_qvoice_config'], ROOT/'config/qvoice_annual_lag_policy_20261008.json']
    files += [ROOT/'tools'/name for name in ['engineering_c_qvoice_overlap.py', 'engineering_model_c.py',
        'engineering_model_c_qvoice.py', 'engineering_c_group_selection.py', 'compare_engineering_bc_priority.py',
        'qvoice_calibrated_model.py', 'qvoice_horizon_calibration.py', 'qvoice_model_data.py', 'qvoice_model_experiment.py']]
    for file in files:
        target = out/'source'/file.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, target)
    write(out/'started.json', {'date': shared.now(), 'status': 'running', 'resume': resume})
    write(out/'frozen-config.json', config)
    write(out/'mapping.json', mapping)
    base.db.psycopg2.connect = partial(base.db.psycopg2.connect, keepalives=1,
        keepalives_idle=30, keepalives_interval=10, keepalives_count=3)
    salt = secrets.token_hex(32)
    base.log('Carga única; C y CQ restaurados. Combinación fija con media de 28.')
    frame = shared.load_frame(config, cconfig, original, salt, out)
    features = list(dict.fromkeys([f for fs in qconfig['search']['blocks'].values() for f in fs]+shared.MEAN_ITEMS))
    timings = {}
    frame = horizon.attach_selected(frame, qconfig, metadata, salt, features, timings)
    del salt
    if not (frame.qvoice_wave.astype(str).to_numpy() == (frame.snapshot_date.dt.year-1).astype(str).to_numpy()).all():
        raise RuntimeError('Asignación de encuesta fuera de año.')
    for feature in features:
        frame['av_'+feature] = pd.Categorical(np.where(frame[feature].astype(str).isin(cq.VALID), 'available', frame[feature].astype(str)))
    monthly = frame.loc[frame.y_next.notna()].copy()
    bank = cq.catalog(original)
    periods, held, checks = [], [], []
    for period in original['periods']:
        source = ROOT/config['source_cq']/'folds'/period['id']
        target = out/'folds'/period['id']
        selection = base.read(source/'selection.json')
        selection['trials'] = [r for r in selection['trials'] if r['kind'] == 'blocks' and
                               r['features'] == config['fixed_overlap_features']]
        if len(selection['trials']) != len(config['l2_grid']):
            raise RuntimeError('No existe el subconjunto fijo en los candidatos originales.')
        model, fitted, records, selected = shared.fit_representations(frame, monthly, period['origin'], bank,
            selection, config, target, mapping)
        if records['disjoint']['derivation']['denominator'] != config['expected_mean_denominator']:
            raise RuntimeError('El promedio no tiene 28 componentes.')
        qitems = [f for f in records['disjoint']['features'] if not f.startswith('qv_remaining_')]
        if qitems != config['fixed_qvoice_items']:
            raise RuntimeError('Cambió el conjunto fijo de preguntas.')
        train = monthly.loc[monthly.label_end <= pd.Timestamp(period['origin'])]
        av_features = ['av_'+f for f in records['disjoint']['features']]
        av_encoder = qm.CategoryEncoder.fit(train, av_features)
        av_x = horizon.category_matrix(av_encoder, train)
        av_beta, okay, iterations = qm.fit_offset(av_x, train.y_next.to_numpy(float), cq.eta(model, train), records['disjoint']['l2'])
        if not okay:
            raise RuntimeError('No converge control de disponibilidad.')
        write(target/'mean28-availability-model.json', {'encoder': asdict(av_encoder), 'beta': av_beta,
            'l2': records['disjoint']['l2'], 'iterations': iterations, 'cutoff': period['origin'],
            'fit_maximum_label_end': str(train.label_end.max().date())})
        test = frame.loc[frame.y_6m.notna() & frame.snapshot_date.between(period['origin'], period['end'])].copy()
        if test.snapshot_date.nunique() != period['snapshots']:
            raise RuntimeError('Periodo externo incompleto.')
        archive = base.read(source/'model.json')
        own_q = horizon.categorical_eta(archive['correction']['encoder'], archive['correction']['beta'], test)
        own_av = horizon.categorical_eta(archive['availability_control']['encoder'], archive['availability_control']['beta'], test)
        predictions = {'C': model.risk(test), 'CQ': cq.risk(model, test, own_q),
                       'C_availability': cq.risk(model, test, own_av)}
        for name, (encoder, beta) in fitted.items():
            predictions[name] = cq.risk(model, test, shared.correction(encoder, beta, test))
        predictions['mean28_availability'] = cq.risk(model, test, shared.correction(av_encoder, av_beta, test))
        predictions['selected'] = predictions[selected]
        ev, allocations = shared.evaluate(test, predictions, original, original['groups'])
        reconciled = shared.verify_archived(ev, base.read(source/'evaluation.json')['evaluation'], config['reconciliation_absolute_tolerance'])
        checks.extend(reconciled)
        write(target/'reconciliation.json', {'outcome': 'pass', 'checks': reconciled})
        extra, _ = shared.evaluate(test, predictions, original, original['groups']+['acquisition_recorded'])
        record = {**period, 'evaluation': ev, 'four_cuts_evaluation': extra,
            'selected_representation_by_inner_brier': selected, 'exposures': len(test), 'people': int(test.person_key.nunique()),
            'latest_outcome': str(test.r6_end.max().date()), 'fixed_mean_denominator': 28,
            'features': records['disjoint']['features']}
        write(target/'evaluation.json', record)
        periods.append(record)
        held.append({'keys': test.person_key.to_numpy(), 'y': test.y_6m.to_numpy(float),
                     'predictions': predictions, 'allocations': allocations})
        base.log(f'Periodo {period["id"]} evaluado y C/CQ reconciliados.')
    # Copia exacta del final ya entrenado: no fingir un nuevo ajuste o una evaluación prospectiva.
    final_source = ROOT/config['source_overlap']/'trained-model/selected-model.json'
    final = out/'trained-model/model-mean28.json'
    final.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(final_source, final)
    write(out/'trained-model/provenance.json', {'source': str(final_source.relative_to(ROOT)),
        'sha256': base.sha(final_source), 'copy_sha256': base.sha(final), 'cutoff': '2026-09-07',
        'new_fit': False, 'post_fit_validation': False,
        'evaluation_scope': 'Mis mismos predictores, coeficientes reajustados antes de cada periodo histórico.'})
    base.log('Intervalos por persona y tabla comparativa.')
    stats = shared.summary(periods)
    intervals = uncertainty(held, config)
    result = {'date': shared.now(), 'stage': 'model_selection', 'reporting_mode': 'presentation',
        'periods': periods, 'summary': stats, 'four_cuts_summary': shared.summary(periods, 'four_cuts_evaluation'),
        'intervals': intervals, 'comparison_mean28': compare(periods, stats, intervals),
        'fixed_qvoice_items': config['fixed_qvoice_items'], 'mean_denominator': 28,
        'configuration_chosen_after_historical_exploration': True, 'coefficients_fit_only_before_each_period': True,
        'source_query': config['query'], 'source_query_sha256': base.sha(ROOT/config['query']),
        'authorization': original['authorization'], 'fit_count': 26, 'base_refits': 0, 'final_refits': 0,
        'elapsed_seconds': time.perf_counter()-start, 'survey_timings': timings,
        'employee_level_rows_persisted': False, 'individual_scores_published': False, 'score_changes': False}
    after = {name: base.sha(ROOT/name) for name in before}
    if before != after:
        raise RuntimeError('Cambió una fuente anterior.')
    write(out/'preservation.json', {'outcome': 'pass', 'files': len(before), 'before_equals_after': True})
    write(out/'analysis-checks.json', {'outcome': 'pass', 'reconciliations': len(checks),
        'all_reconciliations_pass': all(c['pass'] for c in checks), 'fixed_items_in_both_periods': True,
        'same_28_item_mean_in_both_periods': True, 'population_matches_archived_C': True})
    write(out/'results.json', result)
    write(out/'completed.json', {'date': shared.now(), 'status': 'calculations_complete', 'seconds': time.perf_counter()-start})
    base.log(f'Evaluación fija terminada en {(time.perf_counter()-start)/60:.1f} minutos.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config/engineering_c_qvoice_mean28_20261009.json')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    with threadpool_limits(limits=2):
        run(ROOT/args.config, args.resume)
