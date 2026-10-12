"""Preguntas individuales y combinaciones pequeñas, condicionadas a B obligatorio."""
from __future__ import annotations

from dataclasses import dataclass
import gc

import numpy as np
import pandas as pd

import engineering_b_incremental as inc
import engineering_model_c as base


def availability_name(feature):
    return feature if feature=='qv_availability' else 'availability_'+feature


def prepared(frame,features):
    additions = {}
    for feature in features:
        name = availability_name(feature)
        if name!=feature:
            value = frame[feature].astype(str)
            additions[name] = pd.Categorical(np.where(value.isin(inc.VALID_Q),'available',value))
    retained = frame.drop(columns=[name for name in additions if name in frame])
    return pd.concat([retained,pd.DataFrame(additions,index=frame.index)],axis=1)


@dataclass
class Correction:
    design: base.Design
    beta: np.ndarray
    l2: float
    iterations: int

    def offset(self,frame):
        return np.asarray(self.design.matrix(frame)@self.beta).ravel()

    def artifact(self):
        return {'encoder':vars(self.design),'beta':self.beta.tolist(),'l2':self.l2,
                'iterations':self.iterations,'link':'monthly_cloglog_offset'}

    @classmethod
    def restore(cls,artifact):
        return cls(base.Design(**artifact['encoder']),np.asarray(artifact['beta']),artifact['l2'],artifact['iterations'])


class Context:
    def __init__(self,train,valid,hr,config,mode='r6'):
        self.hr,self.config,self.valid,self.mode = hr,config,valid,mode
        candidates = inc.q_candidates(config)
        self.train,self.prepared_valid = prepared(train,candidates),prepared(valid,candidates)
        features = candidates+[availability_name(f) for f in candidates if availability_name(f)!=f]
        self.design = base.Design.fit(self.train,features,{})
        self.x,self.vx = self.design.matrix(self.train),self.design.matrix(self.prepared_valid)
        self.y = train.y_next.to_numpy(float)
        self.offset = hr.eta(train)
        self.valid_eta = hr.eta(valid)
        self.evaluation = inc.Evaluation(valid,config,mode)
        self.fixed_prediction = hr.risk(valid) if mode=='r6' else base.hazard(self.valid_eta)
        self.evaluation.set_reference(self.fixed_prediction)

    def fit(self,features,l2):
        features = inc.design_order(self.design,features)
        indices = self.design.indices(features)
        beta,iterations,unique = inc.weighted_offset_fit(self.x[:,indices],self.y,self.offset,l2,self.config['penalty_cell_scale'])
        full = base.Model(self.design,beta,features,l2,iterations).artifact()
        correction = Correction(base.Design(**full['encoder']),beta,l2,iterations)
        offset = np.asarray(self.vx[:,indices]@beta).ravel()
        prediction = inc.risk_with_correction(self.hr,self.valid,offset,self.valid_eta) if self.mode=='r6' else base.hazard(self.valid_eta+offset)
        return correction,prediction,unique


def select(qframe,full_frame,cutoff,hr_additions,l2,anchor,config,out):
    core,valid,mode,split = inc.temporal_split(qframe,cutoff,config,qvoice=True)
    # Reajuste de los coeficientes de B y RH antes de la reserva Q; nunca se
    # reutilizan aquí coeficientes ajustados al corte externo posterior.
    hr = inc.fit_hr(full_frame,split['origin'],hr_additions,l2,config)
    context = Context(core,valid,hr,config,mode)
    trials,counter = [],0

    def fit_row(features,lq,kind,identifier,additions):
        nonlocal counter
        row = {'id':identifier,'additions':list(additions),'encoded_features':list(features),
               'l2':float(lq),'kind':kind,'eligible_for_selection':True}
        try:
            correction,p,unique = context.fit(features,lq)
            row.update(status='ok',metrics=context.evaluation.score(p),
                       parameters=len(correction.beta),iterations=correction.iterations,unique_design_rows=unique)
        except (RuntimeError,np.linalg.LinAlgError) as error:
            row.update(status='failed',reason=str(error))
        counter+=1
        return row

    fixed = {'id':anchor,'additions':[],'encoded_features':[],'l2':0.,'kind':'fixed',
             'eligible_for_selection':True,'status':'ok','metrics':context.evaluation.score(context.fixed_prediction)}
    refresh = fit_row([],0.,'refresh',anchor+' + intercepto',[])
    if refresh['status']!='ok':
        raise RuntimeError('No convergió el control de intercepto QVoice.')
    baseline = min([fixed,refresh],key=lambda r:r['metrics']['log_loss'])
    trials += [fixed,refresh]

    def grid(features,stage):
        identifier = anchor+' + '+' + '.join(features)
        fits = [fit_row(features,lq,'q',identifier,features) for lq in config['qvoice']['ridge_grid']]
        valid_fits = [r for r in fits if r['status']=='ok']
        if not valid_fits:
            failed = {'id':identifier,'additions':features,'status':'failed','stage':stage,'fits':fits}
            trials.append(failed)
            return failed
        winner = min(valid_fits,key=lambda r:(r['metrics']['log_loss'],-r['l2']))
        winner = dict(winner,stage=stage,ridge_trials=fits)
        af = list(dict.fromkeys(availability_name(f) for f in features))
        available_fits = [fit_row(af,lq,'availability_control',identifier+' / disponibilidad',features)
                          for lq in config['qvoice']['ridge_grid']]
        valid_available = [r for r in available_fits if r['status']=='ok']
        if not valid_available:
            winner['eligible_for_selection'] = False
            winner['availability_control_failed'] = True
        else:
            control = min(valid_available,key=lambda r:(r['metrics']['log_loss'],-r['l2']))
            winner['availability_control'] = control
            content = any(f!='qv_availability' for f in features)
            winner['content_improves_availability'] = winner['metrics']['log_loss'] < control['metrics']['log_loss']-1e-12
            if content and config['qvoice']['content_must_improve_matched_availability']:
                winner['eligible_for_selection'] = winner['content_improves_availability']
        trials.append(winner)
        return winner

    singles = []
    for i,f in enumerate(inc.q_candidates(config),1):
        singles.append(grid([f],'single'))
        if i%5==0:
            base.log(f'QVoice {cutoff} sobre {anchor}: {i}/{len(inc.q_candidates(config))} candidatas individuales.')
    ranked = sorted((r for r in singles if r['status']=='ok'),key=lambda r:(r['metrics']['log_loss'],r['id']))
    shortlist = [r['additions'][0] for r in ranked[:config['selection']['shortlist_size']]]
    combinations = inc.combination_sets(shortlist,config['qvoice']['maximum_additions'])
    combos = []
    for i,fs in enumerate(combinations,1):
        combos.append(grid(fs,'combination'))
        if i%5==0:
            base.log(f'QVoice {cutoff} sobre {anchor}: {i}/{len(combinations)} pares y tríos.')
    winner = inc.choose([baseline]+singles+combos,baseline,config,mode)
    record = {'cutoff':cutoff,'anchor':anchor,'hr_additions':hr_additions,'hr_l2':l2,
              'split':split,'baseline':baseline,'fixed_control':fixed,'intercept_control':refresh,
              'winner':winner,'shortlist':shortlist,'trials':trials,'fits':counter,
              'external_outcomes_used_for_selection':False,'conditional_hr_selection':'RH elegido sólo con pasado del corte externo.'}
    inc.write(out,record)
    base.log(f'QVoice {cutoff} sobre {anchor}: elegidas {len(winner["additions"])} incorporaciones; control {winner["kind"]}.')
    del context,core,valid,hr
    gc.collect()
    return record


def refit(context,spec):
    if spec['kind']=='fixed':
        return None,context.fixed_prediction
    features = spec.get('encoded_features',spec['additions'])
    correction,p,_ = context.fit(features,spec['l2'])
    return correction,p


def artifact(hr,correction,spec,cutoff):
    return {'status':'experimental','training_cutoff':str(cutoff),'base':hr.artifact(),
            'correction':correction.artifact() if correction is not None else None,
            'qvoice_features':list(spec['additions']),'kind':spec['kind'],
            'employee_level_rows_persisted':False,'individual_scores_published':False,
            'formula':'R6 con calendario futuro, RH y QVoice conocidos en t congelados durante seis meses.'}


def predict_saved(artifact,frame):
    hr = inc.HRModel.restore(artifact['base'])
    if artifact['correction'] is None:
        return hr.risk(frame)
    correction = Correction.restore(artifact['correction'])
    return inc.risk_with_correction(hr,frame,correction.offset(frame))
