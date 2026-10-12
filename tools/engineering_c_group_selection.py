"""Selección temporal de agrupaciones; modelos archivados, datos sólo en RAM."""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
import shutil
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

import engineering_model_c as base
import compare_engineering_bc_priority as prior
import engineering_playbook_group_selection as historical

ROOT = base.ROOT
DEFAULT = ROOT / 'config/engineering_c_group_selection_20261008.json'
B_CUT = ('antiguedad', 'salidas_equipo', 'nivel')
COMMON = dict(zip(historical.VARIABLES, [
    'tenure_playbook_band', 'team_exits_12m', 'direct_reports_band',
    'level_grouped', 'manager_changes_12m', 'time_since_promotion_band', 'rehire']))
LABELS = {
    'B_cuts': 'B · cortes originales', 'C_Bcuts': 'C · mismos cortes de B',
    'B_tree8': 'B · árbol de hasta 8 grupos', 'B_tree16': 'B · árbol de hasta 16 grupos',
    'C_tree8': 'C · árbol de hasta 8 grupos', 'C_tree16': 'C · árbol de hasta 16 grupos',
    'C_selected': 'C · selección por prioridad', 'C_gini': 'C · selección por Gini'}


def native(x):
    if isinstance(x, dict):
        return {str(k): native(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [native(v) for v in x]
    if isinstance(x, np.ndarray):
        return native(x.tolist())
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, (pd.Timestamp, datetime)):
        return x.isoformat()
    return x


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(native(value), ensure_ascii=False, indent=2,
                               allow_nan=False) + '\n', encoding='utf-8')


def cut_keys(frame, features):
    keys = historical.coarse_keys(frame)
    for f in features:
        if f not in COMMON.values() and f != 'calendar_month' and '_x_' not in f:
            keys[f] = frame[f].astype(str)
    return keys


def encode(keys):
    result = {}
    for name in keys:
        codes, values = pd.factorize(keys[name], sort=True)
        if np.any(codes < 0):
            raise RuntimeError('Una dimensión no tiene categoría explícita.')
        result[name] = (codes.astype(np.int64), [str(v) for v in values])
    return result


def combined(encoded, dims, names=False):
    raw = np.zeros(len(encoded[dims[0]][0]), dtype=np.int64)
    for d in dims:
        raw = raw * len(encoded[d][1]) + encoded[d][0]
    values, codes = np.unique(raw, return_inverse=True)
    labels = None
    if names:
        labels = []
        for value in values:
            bits = []
            for d in reversed(dims):
                categories = encoded[d][1]
                value, rem = divmod(int(value), len(categories))
                bits.append(f'{historical.DISPLAY.get(d, d)}: {categories[rem]}')
            labels.append(' · '.join(reversed(bits)))
    return codes, len(values), labels


def gini(n, y, score):
    valid = n > 0
    n, y, score = n[valid], y[valid], score[valid]
    if y.sum() <= 0:
        return 0.
    values, codes = np.unique(score, return_inverse=True)
    ns = np.bincount(codes, weights=n, minlength=len(values))[::-1]
    ys = np.bincount(codes, weights=y, minlength=len(values))[::-1]
    x = np.r_[0., np.cumsum(ns) / ns.sum()]
    z = np.r_[0., np.cumsum(ys) / ys.sum()]
    return float(np.sum(np.diff(x) * (z[1:] + z[:-1])) - 1.)


class Grouped:
    def __init__(self, frame, pred, codes, count, config, names=None):
        self.frame, self.pred, self.codes = frame, pred, codes
        self.names = names or [f'Grupo {i}' for i in range(count)]
        self.config = config
        self.dates, self.date_values = pd.factorize(frame.snapshot_date, sort=True)
        self.y = frame.y_6m.to_numpy(float)
        self.keys = frame.person_key.to_numpy()
        self.cells = self.dates * count + codes
        shape = (len(self.date_values), count)
        self.n = np.bincount(self.cells, minlength=np.prod(shape)).reshape(shape)
        self.e = np.bincount(self.cells, weights=self.y, minlength=np.prod(shape)).reshape(shape)
        self.p = np.bincount(self.cells, weights=pred, minlength=np.prod(shape)).reshape(shape)
        self.score = np.divide(self.p, self.n, out=np.zeros(shape), where=self.n > 0)
        self.eligible = self.n >= config['minimum_group_people_each_snapshot']

    def allocation(self, fraction):
        weights = np.zeros_like(self.score)
        low, high = weights.copy(), weights.copy()
        for i in range(len(self.n)):
            target = self.n[i].sum() * fraction
            remaining = target
            # Tratar empates como un solo bloque, independientemente del código del grupo.
            for score in np.unique(self.score[i, self.eligible[i]])[::-1]:
                mask = self.eligible[i] & (self.score[i] == score)
                size = self.n[i, mask].sum()
                value = min(1., max(0., remaining / size))
                weights[i, mask] = value
                low[i, mask] = float(value >= 1 - 1e-12)
                high[i, mask] = float(value > 1e-12)
                remaining -= size * value
            if remaining > 1e-7:
                raise RuntimeError('Población elegible insuficiente para la capacidad declarada.')
            if not np.isclose((weights[i] * self.n[i]).sum(), target, atol=1e-7):
                raise RuntimeError('La capacidad no se conserva por snapshot.')
        return weights, low, high

    def quick(self, weights):
        n = float((weights * self.n).sum())
        if n <= 0:
            return {'suppressed': True, 'coverage_percent': 0., 'capture_percent': 0.}
        e, p = float((weights * self.e).sum()), float((weights * self.p).sum())
        residual = weights * (self.p - self.e)
        m = {'coverage_percent': 100 * n / self.n.sum(),
             'capture_percent': 100 * e / self.e.sum(), 'observed_percent': 100 * e / n,
             'predicted_percent': 100 * p / n, 'bias_pp': 100 * (p - e) / n,
             'aggregate_error_pp': 100 * abs(p - e) / n,
             'group_mae_pp': 100 * abs(residual.sum(axis=0)).sum() / n,
             'group_snapshot_mae_pp': 100 * abs(residual).sum() / n,
             'lift': (e / n) / (self.e.sum() / self.n.sum()),
             'mean_people_per_snapshot': n / len(self.n),
             'mean_selected_groups_per_snapshot': float((weights > 1e-12).sum(axis=1).mean())}
        if not np.isclose(m['capture_percent'], m['coverage_percent'] * m['lift']):
            raise RuntimeError('No concuerdan captura, cobertura y lift.')
        return m

    def detail(self, weights, with_rows=True):
        result = self.quick(weights)
        if result.get('suppressed'):
            return result, []
        rw = weights.ravel()[self.cells]
        active = rw > 1e-12
        minimum = float((weights * self.n).sum(axis=1).min())
        events = len(np.unique(self.keys[active & (self.y == 1)]))
        if minimum < self.config['minimum_public_people_each_snapshot'] or events < self.config['minimum_distinct_events']:
            return {'suppressed': True, 'coverage_percent': result['coverage_percent']}, []
        # Reconciliación independiente contra las filas que siguen sólo en RAM.
        direct_capture = 100 * (rw @ self.y) / self.y.sum()
        if not np.isclose(direct_capture, result['capture_percent'], atol=1e-9):
            raise RuntimeError('El cálculo por celdas no reproduce la captura directa.')
        result['distinct_people_with_event'] = events
        rows, public_errors, public_n = [], [], 0.
        for g in np.flatnonzero((weights > 1e-12).any(axis=0)):
            ng = weights[:, g] * self.n[:, g]
            positive = ng[ng > 1e-12]
            rowmask = (self.codes == g) & active & (self.y == 1)
            distinct = len(np.unique(self.keys[rowmask]))
            safe = bool(positive.min() >= self.config['minimum_public_people_each_snapshot'] and
                        distinct >= self.config['minimum_distinct_events'])
            size = float(ng.sum())
            pe = float((weights[:, g] * self.p[:, g]).sum())
            ey = float((weights[:, g] * self.e[:, g]).sum())
            row = {'group': self.names[g], 'observed_publishable': safe}
            if positive.min() >= self.config['minimum_public_people_each_snapshot']:
                row.update(mean_selected_people_per_snapshot=size / len(self.n),
                           predicted_percent=100 * pe / size,
                           selected_snapshots=int(len(positive)),
                           minimum_effective_people_selected_snapshot=float(positive.min()))
            if safe:
                error = 100 * abs(pe - ey) / size
                public_errors.append(error)
                public_n += size
                row.update(observed_percent=100 * ey / size, error_pp=error,
                           distinct_people_with_event=distinct)
            if with_rows:
                rows.append(row)
        result['worst_publishable_group_error_pp'] = max(public_errors) if public_errors else None
        result['publishable_group_exposure_percent'] = 100 * public_n / (weights * self.n).sum()
        return result, rows

    def structure(self, individual_ginis):
        ginis = []
        for i in range(len(self.n)):
            valid = self.eligible[i]
            ns = np.r_[self.n[i, valid], self.n[i, ~valid].sum()]
            es = np.r_[self.e[i, valid], self.e[i, ~valid].sum()]
            scores = np.r_[self.score[i, valid], -1.]
            ginis.append(gini(ns, es, scores))
        eligible = self.eligible.sum(axis=1)
        return {'mean_eligible_groups': float(eligible.mean()), 'minimum_eligible_groups': int(eligible.min()),
                'maximum_eligible_groups': int(eligible.max()),
                'rest_percent': 100 * float(self.n[~self.eligible].sum()) / self.n.sum(),
                'gini_groups': float(np.mean(ginis)),
                'efficiency_percent': 100 * float(np.mean(np.asarray(ginis) / individual_ginis))}


def individual_ginis(frame, pred):
    dates = frame.snapshot_date.to_numpy()
    y = frame.y_6m.to_numpy(float)
    return np.array([gini(np.ones((dates == d).sum()), y[dates == d], pred[dates == d])
                     for d in np.unique(dates)])


def select(candidates, config, criterion):
    fixed = [x for x in candidates if x['kind'] == 'cut']
    trees = [x for x in candidates if x['kind'] == 'tree']
    metric = 'capture_percent' if criterion == 'priority' else 'efficiency_percent'
    best = max(x[metric] for x in fixed)
    close = [x for x in fixed if x[metric] >= best * (1 - config['capture_relative_tolerance'])]
    if criterion == 'priority':
        minimum_error = min(x['group_snapshot_mae_pp'] for x in close)
        close = [x for x in close if x['group_snapshot_mae_pp'] <= minimum_error + config['error_tolerance_pp']]
    winner = min(close, key=lambda x: (len(x['dimensions']), x['mean_eligible_groups'], -x[metric], x['name']))
    eligible_trees = [x for x in trees if x[metric] > winner[metric] * (1 + config['tree_relative_gain_required'])]
    if criterion == 'priority':
        eligible_trees = [x for x in eligible_trees if x['group_snapshot_mae_pp'] <=
                          winner['group_snapshot_mae_pp'] + config['error_tolerance_pp']]
    if eligible_trees:
        winner = max(eligible_trees, key=lambda x: x[metric])
    return {'criterion': criterion, 'winner': winner, 'best_fixed_metric': best,
            'candidates_in_final_tolerance': len(close)}


def tree_codes(frame, artifact):
    leaf = prior.apply_rules(frame, artifact)
    values, codes = np.unique(leaf, return_inverse=True)
    lookup = {int(r['node']): r for r in artifact['rules']}
    names = []
    for value in values:
        names.append(' y '.join(('' if c['present'] else 'no ') + c['condition']
                               for c in lookup[int(value)]['conditions']) or 'Toda la población')
    return codes, len(values), names


def search(frame, pred, features, artifacts, config):
    encoded = encode(cut_keys(frame, features))
    varying = [k for k, (_, values) in encoded.items() if len(values) > 1]
    gi = individual_ginis(frame, pred)
    if np.any(gi <= 0):
        raise RuntimeError('Gini individual no positivo; revisar criterio de eficiencia.')
    candidates = []
    for size in config['combination_sizes']:
        for dims in itertools.combinations(varying, size):
            codes, count, _ = combined(encoded, dims)
            group = Grouped(frame, pred, codes, count, config)
            w, _, _ = group.allocation(config['primary_capacity_fraction'])
            candidates.append({'name': ' × '.join(dims), 'kind': 'cut', 'dimensions': list(dims),
                               **group.quick(w), **group.structure(gi)})
    for name, artifact in artifacts.items():
        codes, count, names = tree_codes(frame, artifact)
        group = Grouped(frame, pred, codes, count, config, names)
        w, _, _ = group.allocation(config['primary_capacity_fraction'])
        candidates.append({'name': name, 'kind': 'tree', 'dimensions': artifact['features'],
                           **group.quick(w), **group.structure(gi)})
    return candidates, select(candidates, config, 'priority'), select(candidates, config, 'gini')


def period(frame, predictions, specs, artifacts, features, config):
    encoded = encode(cut_keys(frame, features))
    gis = {k: individual_ginis(frame, v) for k, v in predictions.items()}
    outputs, allocations = {}, {str(int(f * 100)): {} for f in config['capacity_fractions']}
    for variant, spec in specs.items():
        model_name = variant[0]
        if spec['kind'] == 'cut':
            codes, count, names = combined(encoded, spec['dimensions'], True)
        else:
            codes, count, names = tree_codes(frame, artifacts[spec['name']])
        group = Grouped(frame, predictions[model_name], codes, count, config, names)
        result = {'definition': spec, 'structure': group.structure(gis[model_name]), 'scenarios': {}}
        for f in config['capacity_fractions']:
            key = str(int(f * 100))
            w, low, high = group.allocation(f)
            metrics, rows = group.detail(w)
            lower, _ = group.detail(low, False)
            upper, _ = group.detail(high, False)
            rw = w.ravel()[group.cells]
            allocations[key][variant] = rw
            result['scenarios'][key] = {'metrics': metrics, 'selected_groups': rows,
                                       'whole_groups_excluding_boundary': lower,
                                       'whole_groups_including_boundary': upper}
            if metrics.get('suppressed'):
                raise RuntimeError('El escenario principal no tiene cohortes publicables.')
        if variant == 'B_cuts':
            other = Grouped(frame, predictions['C'], codes, count, config, names)
            w, _, _ = group.allocation(config['primary_capacity_fraction'])
            result['same_selected_people_C_estimator'], _ = other.detail(w, False)
        outputs[variant] = result
    return outputs, allocations


def bootstrap(held, config):
    capacities = list(held[0]['allocations'])
    variants = [k for k in LABELS if k != 'B_cuts']
    all_keys = np.concatenate([h['keys'] for h in held])
    codes, people = pd.factorize(all_keys, sort=False)
    width = 1 + len(capacities) * len(variants)
    sums = np.zeros((len(people), len(held), width))
    offset = 0
    for i, h in enumerate(held):
        local = codes[offset:offset + len(h['y'])]
        offset += len(local)
        sums[:, i, 0] = np.bincount(local, weights=h['y'], minlength=len(people))
        for j, (cap, variant) in enumerate(itertools.product(capacities, variants), 1):
            delta = h['allocations'][cap][variant] - h['allocations'][cap]['B_cuts']
            sums[:, i, j] = np.bincount(local, weights=h['y'] * delta, minlength=len(people))
    rng = np.random.default_rng(config['seed'])
    flat = sums.reshape(len(people), -1)
    draws = []
    for _ in range(config['bootstrap_repetitions']):
        w = np.bincount(rng.integers(len(people), size=len(people)), minlength=len(people))
        total = (w @ flat).reshape(len(held), width)
        draws.append(np.mean(100 * total[:, 1:] / total[:, :1], axis=0))
    draws = np.array(draws)
    total = sums.sum(axis=0)
    point = np.mean(100 * total[:, 1:] / total[:, :1], axis=0)
    result = {cap: {} for cap in capacities}
    for j, (cap, variant) in enumerate(itertools.product(capacities, variants)):
        result[cap][variant] = {'difference_vs_B_cuts_pp': point[j],
                                'ci95_pp': np.quantile(draws[:, j], [.025, .975])}
    return result


def summary(folds, intervals, config):
    result = {}
    for fraction in config['capacity_fractions']:
        cap = str(int(fraction * 100))
        result[cap] = {}
        ref = [f['evaluation']['B_cuts']['scenarios'][cap]['metrics'] for f in folds]
        for variant in LABELS:
            rows = [f['evaluation'][variant]['scenarios'][cap]['metrics'] for f in folds]
            metrics = {k: float(np.mean([r[k] for r in rows if r[k] is not None]))
                       for k in rows[0] if all(isinstance(r[k], (int, float, np.number)) for r in rows)}
            structure = {k: float(np.mean([f['evaluation'][variant]['structure'][k] for f in folds]))
                         for k in folds[0]['evaluation'][variant]['structure']}
            entry = {'label': LABELS[variant], 'metrics': metrics, 'structure': structure}
            if variant != 'B_cuts':
                ci = intervals[cap][variant]
                wins = sum(r['capture_percent'] > b['capture_percent'] + 1e-9 for r, b in zip(rows, ref))
                loss = sum(r['capture_percent'] < b['capture_percent'] - 1e-9 for r, b in zip(rows, ref))
                okay = bool(ci['ci95_pp'][0] > 0 and wins >= 3 and all(
                    metrics[k] <= np.mean([r[k] for r in ref]) + config['error_tolerance_pp']
                    for k in ['group_mae_pp', 'group_snapshot_mae_pp']))
                entry.update(comparison=ci, winning_periods=wins, losing_periods=loss,
                             tied_periods=4-wins-loss, meets_preference_rule=okay)
            for mode in ['whole_groups_excluding_boundary', 'whole_groups_including_boundary']:
                rws = [f['evaluation'][variant]['scenarios'][cap][mode] for f in folds]
                if not any(r.get('suppressed') for r in rws):
                    entry[mode] = {k: float(np.mean([r[k] for r in rws])) for k in
                                   ['coverage_percent', 'capture_percent', 'group_snapshot_mae_pp']}
            result[cap][variant] = entry
    return result


def run(config_path):
    started = time.perf_counter()
    config = base.read(config_path)
    out, source, source_bc = [ROOT / config[k] for k in ['output', 'source_c', 'source_bc']]
    if (out / 'started.json').exists() or (out / 'results.json').exists():
        raise RuntimeError('Run existente: utilizar una nueva configuración.')
    bc = base.read(source_bc / 'results.json')
    original = base.read(source / 'results.json')
    base_config = base.read(source / 'frozen-config.json')
    preserved = sorted(set([p for directory in [source, source_bc,
        ROOT / 'output/analysis/engineering/20261003/playbook-group-selection-v1',
        ROOT / 'output/analysis/engineering/20261008/qvoice-model-b-calibrated-v1',
        ROOT / 'output/analysis/engineering/20261008/qvoice-horizon-calibration-v1',
        ROOT / 'output/analysis/engineering/20261003/playbook-tenure-confirmation-v1',
        ROOT / 'output/analysis/engineering/20261003/playbook-priority-v1']
        for p in directory.rglob('*') if p.is_file()]))
    before = {str(p.relative_to(ROOT)): base.sha(p) for p in preserved}
    frozen = base.read(source / 'frozen-sources.json')
    if base.sha(ROOT / base_config['query']) != frozen[base_config['query'].replace('/', '\\')]:
        raise RuntimeError('Cambió la consulta del modelo C.')
    for module in ['tools/engineering_model_c.py', 'tools/engineering_model_c_fast.py']:
        if base.sha(ROOT / module) != base.sha(source / 'source' / module):
            raise RuntimeError('El motor local difiere del archivado.')
    # Abrir antes del marcador permite reintentar un bloqueo de red sin sobrescribir resultados.
    with base.db.connect() as connection:
        connection.set_session(readonly=True, autocommit=True)
    write(out / 'started.json', {'started_at': datetime.now(timezone.utc), 'status': 'running'})
    write(out / 'frozen-config.json', config)
    paths = [config_path, Path(__file__), ROOT / base_config['query'],
             ROOT / config['authorization'], ROOT / 'docs/plans/attrition-c-group-selection-20261008.md',
             ROOT / 'tools/engineering_model_c.py', ROOT / 'tools/engineering_model_c_fast.py',
             ROOT / 'tools/compare_engineering_bc_priority.py', ROOT / 'tools/engineering_playbook_group_selection.py',
             ROOT / 'tools/qvoice_model_validation.py']
    for path in paths:
        dest = out / 'source' / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
    write(out / 'frozen-sources.json', {str(p.relative_to(ROOT)): base.sha(p) for p in paths})
    base.log('Carga única en RAM; se restauran ocho modelos, cero ajustes hazard.')
    frame = base.load_frame(base_config)
    load_seconds = time.perf_counter() - started
    population = frame.groupby('snapshot_date').agg(exposures=('person_key', 'size'),
        people=('person_key', 'nunique'), monthly_labeled=('y_next', 'count'),
        six_month_labeled=('y_6m', 'count')).reset_index()
    old_population = pd.DataFrame(base.read(source / 'population.json'))
    old_population['snapshot_date'] = pd.to_datetime(old_population.snapshot_date)
    if not population.equals(old_population):
        raise RuntimeError('Cambió la población o la madurez de etiquetas.')
    write(out / 'population.json', population.to_dict('records'))
    folds, held = [], []
    for row in original['folds']:
        tick = time.perf_counter()
        i, origin = row['fold'], pd.Timestamp(row['origin'])
        models = {'B': prior.restore_model(base.read(source_bc / 'reconstructed-models' / f'fold-{i}-B.json')),
                  'C': prior.restore_model(base.read(source / 'folds' / f'fold-{i}-C-model.json'))}
        mature = frame.y_6m.notna() & (frame.r6_end < origin)
        dates = sorted(frame.loc[mature, 'snapshot_date'].unique())[-config['development_snapshots']:]
        dev = frame.loc[frame.snapshot_date.isin(dates)]
        if len(dates) != config['development_snapshots'] or dev.r6_end.max() >= origin:
            raise RuntimeError('Desarrollo temporal inválido.')
        test = base.evaluation(frame, row['origin'], base_config['outer_snapshots'], base_config['knowledge_boundary'])
        predictions = {k: m.risk(test) for k, m in models.items()}
        reproduction = {k: prior.compare_metrics(base.metrics(test, p), row[k],
                       config['reproduction_absolute_tolerance'], f'{k}, periodo {i}') for k, p in predictions.items()}
        archived = next(f for f in bc['folds'] if f['fold'] == i)['group_definitions']
        artifacts = {f'{k}_tree8': archived[k] for k in models}
        train = base.train_before(frame, origin)
        tree_config = {**base_config, 'groups': {**base_config['groups'], 'depth': 4, 'maximum_leaves': 16}}
        for k, model in models.items():
            _, _, artifacts[f'{k}_tree16'] = base.make_groups(model, train, tree_config)
        base.log(f'Periodo {i}: modelos reproducidos; búsqueda en seis fotos maduras anteriores a {origin.date()}.')
        candidates, priority, efficiency = search(dev, models['C'].risk(dev), models['C'].features,
            {k: v for k, v in artifacts.items() if k.startswith('C')}, config)
        specs = {'B_cuts': {'kind': 'cut', 'dimensions': B_CUT, 'name': ' × '.join(B_CUT)},
                 'C_Bcuts': {'kind': 'cut', 'dimensions': B_CUT, 'name': ' × '.join(B_CUT)}}
        specs.update({k: {'kind': 'tree', 'name': k, 'dimensions': a['features']} for k, a in artifacts.items()})
        for name, selection in [('C_selected', priority), ('C_gini', efficiency)]:
            specs[name] = {k: selection['winner'][k] for k in ['kind', 'name', 'dimensions']}
        evaluation, allocations = period(test, predictions, specs, artifacts, models['C'].features, config)
        record = {'fold': i, 'origin': row['origin'], 'first_snapshot': row['first_snapshot'],
                  'last_snapshot': row['last_snapshot'], 'latest_outcome': row['latest_outcome'],
                  'exposures': len(test), 'reproduction': reproduction,
                  'development': {'first_snapshot': str(dev.snapshot_date.min().date()),
                     'last_snapshot': str(dev.snapshot_date.max().date()),
                     'latest_outcome': str(dev.r6_end.max().date()), 'exposures': len(dev)},
                  'candidates_count': len(candidates), 'selection_priority': priority,
                  'selection_efficiency': efficiency, 'evaluation': evaluation,
                  'group_artifacts': artifacts, 'elapsed_seconds': time.perf_counter() - tick}
        folds.append(record)
        held.append({'keys': test.person_key.to_numpy(), 'y': test.y_6m.to_numpy(float), 'allocations': allocations})
        write(out / 'folds' / f'fold-{i}.json', record)
        write(out / 'development-candidates' / f'fold-{i}.json', sorted(candidates, key=lambda x: -x['capture_percent']))
        base.log(f'Periodo {i}: {len(candidates)} candidatos; elegido {priority["winner"]["name"]}; {record["elapsed_seconds"]:.1f} s.')
        del train, dev, test, candidates
    base.log('Incertidumbre pareada y foto madura adicional; sólo agregados se guardan.')
    intervals = bootstrap(held, config)
    extension_frame = frame.loc[frame.snapshot_date == pd.Timestamp(config['extension_snapshot'])]
    if extension_frame.empty or extension_frame.y_6m.isna().any():
        raise RuntimeError('Foto adicional sin seguimiento completo.')
    ep = {k: m.risk(extension_frame) for k, m in models.items()}
    extension_result, _ = period(extension_frame, ep, specs, artifacts, models['C'].features, config)
    unchanged = all(base.sha(ROOT / p) == digest for p, digest in before.items())
    if not unchanged:
        raise RuntimeError('Cambió un artefacto anterior durante la ejecución.')
    results = {'run_id': config['run_id'], 'reporting_mode': 'presentation',
        'created_at': datetime.now(timezone.utc), 'query': base_config['query'],
        'knowledge_boundary': base_config['knowledge_boundary'], 'folds': folds,
        'summary': summary(folds, intervals, config),
        'extension': {'snapshot': config['extension_snapshot'], 'followup_end': str(extension_frame.r6_end.max().date()),
            'people': len(extension_frame), 'model_origin': original['folds'][-1]['origin'], 'evaluation': extension_result},
        'load_seconds': load_seconds, 'elapsed_seconds': time.perf_counter() - started,
        'hazard_refits': 0, 'employee_level_rows_persisted': False, 'individual_scores_published': False,
        'qvoice_included': False}
    write(out / 'results.json', results)
    write(out / 'preservation.json', {'unchanged': unchanged, 'files_before_after_sha256': before})
    write(out / 'analysis-checks.json', {'population_reproduced': True,
        'model_reproduction': [f['reproduction'] for f in folds], 'source_models_unchanged': unchanged,
        'selection_before_external_outcomes': True, 'capacity_checked_every_snapshot': True,
        'grouped_capture_reconciled_against_direct_rows': True, 'capture_equals_coverage_times_lift': True,
        'minimum_group_people_each_snapshot': config['minimum_group_people_each_snapshot'],
        'rows_scores_keys_persisted': False, 'hazard_refits': 0})
    write(out / 'completed.json', {'status': 'complete_analysis', 'elapsed_seconds': results['elapsed_seconds']})
    write(out / 'manifest.json', {'run_id': config['run_id'], 'status': 'completed_analysis',
        'reporting_mode': 'presentation', 'authorization': config['authorization'],
        'employee_level_rows_persisted': False, 'individual_scores_published': False, 'salt_persisted': False,
        'original_models_promoted': False,
        'files': {str(p.relative_to(out)): base.sha(p) for p in out.rglob('*') if p.is_file() and p.name != 'manifest.json'}})
    base.log(f'Completado en {results["elapsed_seconds"]:.1f} s; cero ajustes hazard.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        run(args.config.resolve())
