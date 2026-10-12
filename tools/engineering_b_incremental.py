"""B obligatorio: selección temporal de incorporaciones; resultados sólo agregados."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import gc
import itertools
from pathlib import Path
import time

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.metrics import average_precision_score
from threadpoolctl import threadpool_limits

import engineering_model_c as base
import engineering_model_c_fast as fast
import engineering_c_group_selection as groups

ROOT = base.ROOT
DEFAULT = ROOT / 'config/engineering_b_playbook_v11_20261012.json'
B_TERMS = ('level_grouped', 'tenure_playbook_band', 'calendar_month',
           'manager_changes_12m', 'team_exits_12m', 'direct_reports_band',
           'time_since_promotion_band', 'rehire', 'level_x_tenure', 'tenure_x_manager_changes')
MISSING = {'(unknown)', '(antes de la fuente)', '(historia no confirmada)',
           '(no comparable group)', 'no_available_wave', 'no_linked_row',
           'different_employment_episode', 'missing', 'question_absent',
           'sentinel_255', 'invalid', '(region too small)', '(zero region variance)',
           'no_comment', 'duplicate', '(mapping not historically dated)', '(unmapped geography)',
           '(not onsite)', '(unmapped postal centroid)', '(unmapped office)'}
VALID_Q = {'v0','v1','<50','50–69','70–79','80–89','90–99','100',
           'below -1 sd','-1 to 0 sd','0 to 1 sd','above 1 sd','available'}
write = groups.write


def hr_candidates(config):
    result = config['existing_hr_features'] + config['history_features'] + config['pending_features']
    result += [f for block in config.get('extra_hr_queries',[]) for f in block['features']]
    if len(result)!=len(set(result)):
        raise ValueError('El catálogo contiene representaciones duplicadas.')
    return result


def q_candidates(config):
    return [f'qv_M{i:02d}' for i in range(1, config['qvoice']['common_items']+1)] + config['qvoice']['extra_features']


def mandatory_features(additions, config):
    if tuple(config['base_features']) != B_TERMS:
        raise ValueError('Se alteró el conjunto obligatorio de B.')
    if len(set(additions)) != len(additions) or set(additions) & set(B_TERMS):
        raise ValueError('Incorporaciones repetidas o confundidas con B.')
    if not set(additions) <= set(hr_candidates(config)):
        raise ValueError('Incorporación fuera del catálogo congelado.')
    return list(B_TERMS) + list(additions)


def design_order(design, features):
    """Alinea features con columnas y coeficientes al extraer un submodelo."""
    requested = set(features)
    if len(requested) != len(features) or not requested <= set(design.features):
        raise ValueError('Features repetidas o ausentes del diseño.')
    return [f for f in design.features if f in requested]


def temporal_split(frame, cutoff, config, qvoice=False):
    cutoff = pd.Timestamp(cutoff)
    source = frame.loc[frame.snapshot_date >= pd.Timestamp(config['qvoice']['start'])] if qvoice else frame
    n = config['selection']['validation_snapshots']
    dates = sorted(source.loc[source.y_6m.notna() & (source.r6_end <= cutoff), 'snapshot_date'].unique())
    mode = 'r6'
    core, valid = None, None
    if len(dates) >= n:
        chosen = dates[-n:]
        origin = pd.Timestamp(chosen[0])
        core = base.train_before(source, origin)
        valid = source.loc[source.snapshot_date.isin(chosen) & source.y_6m.notna()]
    if core is None or core.snapshot_date.nunique() < config['selection']['minimum_monthly_training_snapshots']:
        if not qvoice:
            raise RuntimeError('Historia insuficiente para la validación R6 de RH.')
        mode = 'monthly_fallback'
        dates = sorted(source.loc[source.y_next.notna() & (source.label_end <= cutoff), 'snapshot_date'].unique())
        chosen = dates[-n:]
        if len(chosen) != n:
            raise RuntimeError('Historia insuficiente para reserva mensual QVoice.')
        origin = pd.Timestamp(chosen[0])
        core = base.train_before(source, origin)
        valid = source.loc[source.snapshot_date.isin(chosen) & source.y_next.notna() & (source.label_end <= cutoff)]
    if core.empty or core.snapshot_date.nunique() < config['selection']['minimum_monthly_training_snapshots']:
        raise RuntimeError('La reserva no deja suficiente entrenamiento.')
    outcome = valid.y_6m if mode == 'r6' else valid.y_next
    if core.y_next.sum() < 30 or outcome.sum() < 30:
        raise RuntimeError('Menos de 30 eventos en ajuste o validación.')
    if core.label_end.max() > origin or valid.snapshot_date.min() < origin:
        raise RuntimeError('Solapamiento temporal de entrenamiento y validación.')
    last_outcome = valid.r6_end.max() if mode == 'r6' else valid.label_end.max()
    if last_outcome > cutoff:
        raise RuntimeError('La selección recibió etiquetas aún no conocidas.')
    record = {'selection_mode': mode, 'cutoff': str(cutoff.date()), 'origin': str(origin.date()),
              'training_last_label_end': str(core.label_end.max().date()),
              'validation_first': str(valid.snapshot_date.min().date()),
              'validation_last': str(valid.snapshot_date.max().date()),
              'validation_last_outcome': str(last_outcome.date()),
              'training_snapshots': int(core.snapshot_date.nunique()),
              'validation_snapshots': int(valid.snapshot_date.nunique())}
    return core, valid, mode, record


@dataclass
class RarePool:
    keep: dict

    @classmethod
    def fit(cls, frame, features, minimum):
        keep = {}
        for f in features:
            counts = frame[['person_key',f]].drop_duplicates().groupby(f, observed=True).size()
            keep[f] = sorted(str(v) for v,n in counts.items() if n >= minimum)
        return cls(keep)

    def apply(self, frame):
        result = frame.copy(deep=False)
        for f, categories in self.keep.items():
            values = frame[f].astype(str)
            result[f] = values.where(values.isin(categories), '(other)').astype('category')
        return result


@dataclass
class HRModel:
    model: base.Model
    pool: RarePool
    cutoff: str

    def eta(self, frame):
        f = self.pool.apply(frame)
        return np.asarray(self.model.design.matrix(f) @ self.model.beta).ravel()

    def risk(self, frame):
        return self.model.risk(self.pool.apply(frame))

    def calendar(self):
        result = np.zeros(13)
        for column, value in zip(self.model.design.columns, self.model.beta):
            if column.startswith('calendar_month='):
                result[int(column.split('=',1)[1])] = value
        return result

    def artifact(self):
        if not set(B_TERMS) <= set(self.model.features):
            raise RuntimeError('Un artefacto perdió términos de B.')
        return {'status': 'experimental', 'training_cutoff': self.cutoff,
                'mandatory_features': list(B_TERMS), 'model': self.model.artifact(),
                'rare_pool': self.pool.keep, 'employee_level_rows_persisted': False,
                'individual_scores_published': False}

    @classmethod
    def restore(cls, artifact):
        a = artifact['model']
        model = base.Model(base.Design(**a['encoder']), np.asarray(a['beta']), a['features'], a['l2'], a['iterations'])
        if not set(B_TERMS) <= set(model.features):
            raise ValueError('Artefacto sin B completo.')
        return cls(model, RarePool(artifact['rare_pool']), artifact['training_cutoff'])


class Evaluation:
    def __init__(self, frame, config, mode='r6'):
        self.frame, self.config, self.mode = frame, config, mode
        self.reference_weights = None
        if mode == 'r6':
            encoded = groups.encode(groups.cut_keys(frame, []))
            self.codes, self.count, self.names = groups.combined(encoded, tuple(config['groups']), True)

    def grouped(self, p):
        return groups.Grouped(self.frame, p, self.codes, self.count, self.config, self.names)

    def set_reference(self, p):
        if self.mode == 'r6':
            g = self.grouped(p)
            self.reference_weights = g.allocation(self.config['primary_capacity_fraction'])[0]

    def score(self, p, detailed=False):
        if not np.isfinite(p).all() or ((p<=0)|(p>=1)).any():
            raise RuntimeError('Predicciones inválidas.')
        if self.mode != 'r6':
            y = self.frame.y_next.to_numpy(float)
            return {**{k:float(v.mean()) for k,v in base.losses(y,p).items()},
                    'pr_auc':float(average_precision_score(y,p)),
                    'observed_percent':float(y.mean()*100), 'predicted_percent':float(np.mean(p)*100)}
        m = base.metrics(self.frame, p)
        g = self.grouped(p)
        m['common_group_snapshot_mae_pp'] = float(100*np.abs(g.p-g.e).sum()/g.n.sum())
        m['common_group_mae_pp'] = float(100*np.abs((g.p-g.e).sum(axis=0)).sum()/g.n.sum())
        m['minimum_eligible_groups'] = int(g.eligible.sum(axis=1).min())
        m['maximum_eligible_groups'] = int(g.eligible.sum(axis=1).max())
        m['rest_percent'] = float(100*g.n[~g.eligible].sum()/g.n.sum())
        primary = self.config['primary_capacity_fraction']
        allocation = g.allocation(primary)[0]
        main = g.quick(allocation)
        m['capture_percent'] = main['capture_percent']
        m['priority_group_snapshot_mae_pp'] = main['group_snapshot_mae_pp']
        if self.reference_weights is not None:
            same = g.quick(self.reference_weights)
            m['on_B_selection_mae_pp'] = same['group_snapshot_mae_pp']
            m['on_B_selection_bias_pp'] = same['bias_pp']
        if detailed:
            m['individual_capacity_capture_percent'] = aggregate_score_capture(self.frame,p,primary)
            m['individual_minus_group_capture_pp'] = m['individual_capacity_capture_percent']-m['capture_percent']
            m['scenarios'] = {}
            for fraction in self.config['capacity_fractions']:
                w, lo, hi = g.allocation(fraction)
                detail, rows = g.detail(w)
                if detail.get('suppressed'):
                    raise RuntimeError('La cohorte evaluada no es publicable.')
                m['scenarios'][str(int(fraction*100))] = {'metrics':detail,'groups':rows}
        return m


def aggregate_score_capture(frame,p,fraction):
    """Diagnóstico agregado de capacidad, sin guardar rankings ni resolver empates por ID."""
    if not 0<fraction<=1:
        raise ValueError('Capacidad fuera de rango.')
    y=frame.y_6m.to_numpy(float)
    prediction=np.asarray(p)
    captured=0.
    for date in frame.snapshot_date.unique():
        mask=frame.snapshot_date.eq(date).to_numpy()
        values=prediction[mask]
        target=len(values)*fraction
        threshold=np.partition(values,len(values)-int(np.ceil(target)))[len(values)-int(np.ceil(target))]
        higher=values>threshold
        tied=values==threshold
        share=(target-int(higher.sum()))/int(tied.sum())
        captured+=float(y[mask][higher].sum()+share*y[mask][tied].sum())
    return float(100*captured/y.sum())


class HRContext:
    def __init__(self, train, valid, config, cutoff):
        self.config, self.cutoff, self.valid = config, str(pd.Timestamp(cutoff).date()), valid
        self.pool = RarePool.fit(train, hr_candidates(config), config['rare_category_minimum_training_people'])
        prepared = self.pool.apply(train)
        features = mandatory_features(hr_candidates(config), config)
        self.design = base.Design.fit(prepared, features, config['interactions'])
        self.x, self.y = self.design.matrix(prepared), train.y_next.to_numpy(float)
        self.vx = self.design.matrix(self.pool.apply(valid)) if valid is not None else None
        self.months = valid.snapshot_date.dt.month.to_numpy() if valid is not None else None
        self.evaluation = Evaluation(valid, config) if valid is not None else None
        self.availability = {}
        for f in hr_candidates(config):
            observable = ~train[f].astype(str).isin(MISSING)
            dates = train.loc[observable,'snapshot_date'].nunique()
            self.availability[f] = {'observable_training_snapshots': int(dates),
                'training_categories': len(self.design.levels[f]),
                'eligible_for_selection': bool(dates >= config['minimum_observable_training_snapshots_for_selection']
                                              and len(self.design.levels[f])>1)}
        self._cached_key, self._compressed = None, None

    def fit(self, additions, l2):
        features = design_order(self.design, mandatory_features(additions, self.config))
        indices = self.design.indices(features)
        key = tuple(features)
        if key != self._cached_key:
            self._compressed = fast.collapse(self.x[:,indices], self.y)
            self._cached_key = key
        cx, cy, cn = self._compressed
        beta, iterations = fast.fit_weighted(cx, cy, cn, l2, self.config['penalty_cell_scale'])
        full = base.Model(self.design, beta, features, l2, iterations)
        artifact = full.artifact()
        minimal = base.Model(base.Design(**artifact['encoder']), beta, features, l2, iterations)
        fitted = HRModel(minimal, RarePool({f:self.pool.keep[f] for f in additions}), self.cutoff)
        prediction = full.risk_matrix(self.vx, self.months) if self.vx is not None else None
        return fitted, prediction, int(len(cy))


def meets_guards(row, baseline, config, mode='r6'):
    if row.get('status') != 'ok' or not row.get('eligible_for_selection', True):
        return False
    m,b,s = row['metrics'],baseline['metrics'],config['selection']
    if m['brier_score'] > b['brier_score']*(1+s['maximum_relative_brier_worsening']) + 1e-12:
        return False
    if m['pr_auc'] < b['pr_auc']*s['minimum_relative_pr_auc'] - 1e-12:
        return False
    if mode == 'r6':
        if m['lift_at_10_percent'] < b['lift_at_10_percent']*s['minimum_relative_lift10']-1e-12:
            return False
        if m['common_group_snapshot_mae_pp'] > b['common_group_snapshot_mae_pp']+s['maximum_common_group_mae_worsening_pp']+1e-12:
            return False
        if m['capture_percent'] < b['capture_percent']-s['maximum_capture_loss_pp']-1e-12:
            return False
    return True


def choose(trials, baseline, config, mode='r6'):
    eligible = [r for r in trials if meets_guards(r,baseline,config,mode)]
    if not eligible:
        raise RuntimeError('El control debe estar disponible como respaldo.')
    best = min(r['metrics']['log_loss'] for r in eligible)
    near = [r for r in eligible if r['metrics']['log_loss'] <= best*(1+config['selection']['log_loss_parsimony_relative_tolerance'])+1e-12]
    return min(near,key=lambda r:(len(r['additions']),r['metrics']['log_loss'],r['id']))


def combination_sets(shortlist, maximum):
    return [list(c) for size in range(2,maximum+1) for c in itertools.combinations(shortlist,size)]


def select_hr(frame, cutoff, config, out):
    core, valid, mode, split = temporal_split(frame,cutoff,config)
    context = HRContext(core,valid,config,split['origin'])
    trials, counter = [], 0

    def trial(additions,l2,stage):
        nonlocal counter
        row = {'id':'B'+(' + '+' + '.join(additions) if additions else ''),
               'additions':list(additions),'l2':float(l2),'stage':stage,
               'eligible_for_selection':all(context.availability[f]['eligible_for_selection'] for f in additions)}
        try:
            fitted,p,unique = context.fit(additions,l2)
            row.update(status='ok',metrics=context.evaluation.score(p),
                       iterations=fitted.model.iterations,parameters=len(fitted.model.beta),unique_design_rows=unique)
        except (RuntimeError,np.linalg.LinAlgError) as error:
            row.update(status='failed',reason=str(error))
        trials.append(row)
        counter += 1
        if counter % 5 == 0:
            base.log(f'RH {cutoff}: {counter} ajustes de selección; {stage}.')
        return row

    controls = [trial([],l2,'baseline_ridge') for l2 in config['selection']['ridge_grid_for_b']]
    valid_controls = [r for r in controls if r['status']=='ok']
    if not valid_controls:
        raise RuntimeError('No convergió B en la reserva temporal.')
    baseline = min(valid_controls,key=lambda r:(r['metrics']['log_loss'],r['l2']))
    _,bp,_ = context.fit([],baseline['l2'])
    context.evaluation.set_reference(bp)
    singles = [trial([f],baseline['l2'],'single') for f in hr_candidates(config)]
    ranked = sorted((r for r in singles if r['status']=='ok' and r['eligible_for_selection']),
                    key=lambda r:(r['metrics']['log_loss'],r['id']))
    shortlist = [r['additions'][0] for r in ranked[:config['selection']['shortlist_size']]]
    combos = [trial(fs,baseline['l2'],'combination') for fs in combination_sets(shortlist,config['selection']['maximum_additions'])]
    winner = choose([baseline]+singles+combos,baseline,config)
    record = {'cutoff':cutoff,'split':split,'baseline':baseline,'winner':winner,'shortlist':shortlist,
              'candidate_availability':context.availability,'trials':trials,'fits':counter,
              'external_outcomes_used_for_selection':False,'mandatory_features':list(B_TERMS)}
    write(out,record)
    base.log(f'RH {cutoff}: elegidas {len(winner["additions"])} incorporaciones; B completo.')
    del context,core,valid
    gc.collect()
    return record


def weighted_offset_fit(x,y,offset,l2,scale=8.0,max_iter=100):
    """Compresión binomial exacta incluyendo los bits del offset; paso decreciente."""
    if x.nnz and not np.all(x.data==1):
        raise ValueError('El diseño de la corrección debe ser binario.')
    packed = np.packbits(x.astype(np.uint8).toarray(),axis=1)
    ob = np.asarray(offset,np.float64).view(np.uint8).reshape(-1,8)
    raw_keys = np.ascontiguousarray(np.column_stack([packed,ob]))
    keys = raw_keys.view(np.dtype((np.void,raw_keys.shape[1]))).ravel()
    _,first,inverse = np.unique(keys,return_index=True,return_inverse=True)
    n = np.bincount(inverse).astype(float)
    success = np.bincount(inverse,weights=np.asarray(y,float))
    x,y,offset = x[first].tocsr(),success/n,np.asarray(offset,float)[first]
    penalty = np.full(x.shape[1],l2*scale)
    penalty[0] = 0
    beta = np.zeros(x.shape[1])

    def objective(b):
        z = np.exp(np.clip(offset+x@b,-30,5))
        return float(np.sum(n*((1-y)*z-y*np.log(-np.expm1(-z))))+.5*np.sum(penalty*b*b))

    previous = objective(beta)
    for it in range(1,max_iter+1):
        eta = offset+x@beta
        z = np.exp(np.clip(eta,-30,5))
        p = np.clip(-np.expm1(-z),1e-12,1-1e-12)
        derivative = np.maximum(z*np.exp(-z),1e-12)
        w = n*derivative*derivative/np.maximum(p*(1-p),1e-12)
        target = x@beta+(y-p)/derivative
        normal = (x.T@x.multiply(w[:,None])).toarray()
        normal.flat[::len(beta)+1] += penalty+1e-10
        proposed = np.linalg.solve(normal,np.asarray(x.T@(w*target)).ravel())
        step = 1.
        for _ in range(25):
            candidate = beta+step*(proposed-beta)
            value = objective(candidate)
            if value <= previous+1e-8:
                break
            step *= .5
        else:
            raise RuntimeError('La corrección no encontró un paso descendente.')
        delta = float(np.max(np.abs(candidate-beta)))
        beta,previous = candidate,value
        if delta<1e-7:
            return beta,it,len(y)
    raise RuntimeError('No convergió la corrección QVoice.')


def risk_with_correction(hr,frame,correction,eta=None):
    eta = hr.eta(frame) if eta is None else eta
    months = frame.snapshot_date.dt.month.to_numpy()
    calendar = hr.calendar()
    future = (months[:,None]-1+np.arange(6))%12+1
    linear = eta[:,None]-calendar[months,None]+calendar[future]+np.asarray(correction)[:,None]
    return np.clip(-np.expm1(-np.exp(np.clip(linear,-30,5)).sum(axis=1)),1e-8,1-1e-8)


def fit_hr(frame,cutoff,additions,l2,config):
    train = base.train_before(frame,cutoff)
    features = mandatory_features(additions,config)
    pool = RarePool.fit(train,additions,config['rare_category_minimum_training_people'])
    design = base.Design.fit(pool.apply(train),features,config['interactions'])
    x = design.matrix(pool.apply(train))
    cx,cy,cn = fast.collapse(x,train.y_next.to_numpy(float))
    beta,iterations = fast.fit_weighted(cx,cy,cn,l2,config['penalty_cell_scale'])
    return HRModel(base.Model(design,beta,features,l2,iterations),pool,str(pd.Timestamp(cutoff).date()))


def main():
    from run_engineering_b_incremental import run
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=DEFAULT)
    args = parser.parse_args()
    config = base.read(args.config)
    with threadpool_limits(limits=config['thread_limit']):
        run(args.config)


if __name__ == '__main__':
    main()
