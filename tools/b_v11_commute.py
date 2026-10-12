"""Bandas de distancia del playbook; hashes y componentes exclusivamente en RAM."""
from __future__ import annotations

from collections import defaultdict
import math

import pandas as pd

import build_global_commute_distance_evidence as geo
import engineering_model_c as base


def independent_distance(latitude,longitude,office):
    """Ángulo central por producto punto, independiente de Haversine."""
    a,b,c,d=map(math.radians,[latitude,longitude,office['latitude'],office['longitude']])
    cosine=math.sin(a)*math.sin(c)+math.cos(a)*math.cos(c)*math.cos(b-d)
    return 6371.0088*math.acos(max(-1.,min(1.,cosine)))


def distance_band(km):
    if not math.isfinite(km) or km<0:
        raise ValueError('Distancia no válida.')
    return f'{math.floor(km)}–<{math.floor(km)+1} km' if km<30 else '30+ km'


class CommuteTransform:
    features=['commute_distance_onsite_v11']
    input_columns=['country_label','city_label','office_hash','postal_hash','postal_hash_compact',
        'postal_hash_prefix_2','postal_hash_prefix_3','postal_hash_prefix_4','postal_hash_prefix_5',
        'postal_hash_zero_pad_5','postal_hash_zero_pad_6','postal_hash_zero_pad_7','onsite_flag','valid_components']

    def __init__(self):
        all_offices,self.catalog_sha256=geo.load_offices()
        bad=[o for o in all_offices if str(o.get('officeCode','')).upper()=='DAL.B']
        self.blocked_aliases={geo.md5(o[k]) for o in bad for k in ['officeCode','name'] if o.get(k)}
        self.offices=[o for o in all_offices if str(o.get('officeCode','')).upper()!='DAL.B']
        self.by_alias,self.by_city=geo.office_candidates(self.offices)
        self.centroids={}
        self.sources={}
        self.cache={}
        self.counts=defaultdict(lambda:defaultdict(int))
        self.people=defaultdict(set)
        self.first_observed=None
        self.max_formula_difference=0.
        self.unique_calculations=0

    def centroid_map(self,code):
        if code not in self.centroids:
            archive=geo.POSTAL_CACHE_DIR/f'{code}.zip'
            if not archive.is_file():
                self.centroids[code]={}
                self.sources[code]={'status':'no_local_catalog'}
            else:
                # La comprobación anterior impide entrar al fallback de red del helper.
                values,digest,count=geo.download_centroids(code)
                self.centroids[code]=values
                self.sources[code]={'status':'local','path':archive.relative_to(base.ROOT).as_posix(),
                    'sha256':digest,'source_rows':count}
        return self.centroids[code]

    def postal_keys(self,row,code):
        fields=['postal_hash','postal_hash_compact']
        if code=='US':
            fields+=['postal_hash_prefix_5']
        elif code in {'CA','IE'}:
            fields+=['postal_hash_prefix_3']
        elif code=='GB':
            fields+=['postal_hash_prefix_4','postal_hash_prefix_3','postal_hash_prefix_2']
        elif code=='NL':
            fields+=['postal_hash_prefix_4']
        width={'CN':6,'DE':5,'FR':5,'IN':6,'JP':7,'KR':5,'SG':6}.get(code)
        if width:
            fields+=[f'postal_hash_zero_pad_{width}']
        return [row[key] for key in fields if row[key]]

    def classify(self,row):
        if row['valid_components']!=1 or row['onsite_flag']==-1:
            return '(unknown)',False,False,False,0.
        if row['onsite_flag']!=1:
            return '(not onsite)',False,False,False,0.
        if not all(row[key] for key in ['country_label','city_label','office_hash','postal_hash']):
            return '(unknown)',False,False,False,0.
        if row['office_hash'] in self.blocked_aliases:
            return '(unmapped office)',False,False,False,0.
        offices,resolution=geo.choose_offices(row,self.by_alias,self.by_city,self.offices)
        offices=[o for o in offices if geo.canonical_country(o['country'])==geo.canonical_country(row['country_label'])]
        unique={(float(o['latitude']),float(o['longitude'])):o for o in offices}
        if not unique:
            return '(unmapped office)',False,False,False,0.
        code=geo.COUNTRY_ISO.get(geo.canonical_country(row['country_label']))
        centroids=self.centroid_map(code) if code else {}
        point=next((centroids[k] for k in self.postal_keys(row,code) if k in centroids),None)
        if point is None:
            return '(unmapped postal centroid)',len(unique)>1,resolution!='office_site',False,0.
        distances=[(geo.haversine_km(*point,o),independent_distance(*point,o)) for o in unique.values()]
        value=min(a for a,b in distances)
        independent=min(b for a,b in distances)
        error=abs(value-independent)
        self.max_formula_difference=max(self.max_formula_difference,error)
        self.unique_calculations+=1
        if error>0.0001:
            raise RuntimeError('La distancia no reconcilia con la fórmula independiente.')
        return distance_band(value),len(unique)>1,resolution!='office_site',value>500,error

    def __call__(self,frame):
        eligible=frame.valid_components.eq(1) & frame.onsite_flag.eq(1)
        work=frame.loc[eligible,self.input_columns].copy()
        for key in self.input_columns[:-2]:
            work[key]=work[key].fillna('')
        for row in work.drop_duplicates().itertuples(index=False,name=None):
            if row not in self.cache:
                self.cache[row]=self.classify(dict(zip(self.input_columns,row)))
        computed=[('(unknown)',False,False,False,0.) for _ in range(len(frame))]
        offsite=frame.valid_components.eq(1) & frame.onsite_flag.eq(0)
        for index in offsite.to_numpy().nonzero()[0]:
            computed[index]=('(not onsite)',False,False,False,0.)
        for index,row in zip(eligible.to_numpy().nonzero()[0],work.itertuples(index=False,name=None)):
            computed[index]=self.cache[row]
        result=frame[['snapshot_date','person_key']].copy()
        result[self.features[0]]=[r[0] for r in computed]
        metadata=pd.DataFrame(computed,columns=['band','ambiguous','office_fallback','over500','formula_error'],index=frame.index)
        years=pd.to_datetime(frame.snapshot_date).dt.year
        for year in years.unique():
            mask=years.eq(year)
            part=result.loc[mask]
            extra=metadata.loc[mask]
            record=self.counts[int(year)]
            observable=~extra.band.str.startswith('(')
            record['person_snapshots']+=len(part)
            record['onsite_rows']+=int(frame.loc[mask,'onsite_flag'].eq(1).sum())
            record['distance_observable']+=int(observable.sum())
            record['unmapped_office_rows']+=int(extra.band.eq('(unmapped office)').sum())
            record['unmapped_centroid_rows']+=int(extra.band.eq('(unmapped postal centroid)').sum())
            record['ambiguous_office_rows']+=int((extra.ambiguous & observable).sum())
            record['office_fallback_rows']+=int((extra.office_fallback & observable).sum())
            record['over500_km_rows']+=int(extra.over500.sum())
            record['independent_formula_mismatches']+=int(extra.formula_error.gt(.0001).sum())
            self.people[int(year)].update(part.person_key)
            if observable.any():
                earliest=str(pd.to_datetime(part.loc[observable,'snapshot_date']).min().date())
                self.first_observed=min(self.first_observed or earliest,earliest)
        return result

    def evidence(self):
        return {'reporting_mode':'presentation','outcome':'pass',
            'method':'Haversine y recálculo por producto punto; mínimo entre oficinas compatibles; prefijo postal más específico.',
            'catalog':geo.OFFICE_CATALOG.relative_to(base.ROOT).as_posix(),'catalog_sha256':self.catalog_sha256,
            'centroid_sources':self.sources,'first_observed_snapshot':self.first_observed,
            'maximum_independent_formula_difference_km':self.max_formula_difference,
            'unique_geographic_calculations':self.unique_calculations,
            'rows':[{'year':year,**row,'employee_count':len(self.people[year])} for year,row in sorted(self.counts.items())],
            'employee_level_rows_persisted':False,'location_hashes_persisted':False,'assessment_score_changed':False,
            'limitation':'Catálogo estático 2026, sin historia de direcciones; la distancia mínima es un proxy inferior, no trayecto real.'}
