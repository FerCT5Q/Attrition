"""Transformaciones geográficas del V11; componentes y llaves sólo en RAM."""
from __future__ import annotations

from collections import defaultdict
from datetime import timezone
from zoneinfo import ZoneInfo

import pandas as pd

import build_v7_manager_timezone_annual_attrition_evidence as zones
import engineering_model_c as base


class TimezoneTransform:
    features = ['manager_colocation_v11','manager_timezone_relation']
    input_columns = ['site_key','city_key','manager_site','manager_city','usable_pair','colocation_check']

    def __init__(self):
        self.sites,self.cities,self.diagnostics=zones.zone_maps()
        self.offsets={}
        self.counts=defaultdict(lambda:defaultdict(int))
        self.people=defaultdict(set)
        self.catalog_sha256=base.sha(zones.CATALOG)

    def zone(self,site,city):
        a,b=self.sites.get(site),self.cities.get(city)
        return None if a is not None and b is not None and a!=b else a or b

    def offset(self,when,zone):
        key=(when,zone)
        if key not in self.offsets:
            instant=pd.Timestamp(when).to_pydatetime().replace(hour=12,tzinfo=timezone.utc)
            self.offsets[key]=int(instant.astimezone(ZoneInfo(zone)).utcoffset().total_seconds()/60)
        return self.offsets[key]

    def classify(self,when,site,city,manager_site,manager_city,usable):
        coloc='(unknown)'
        relation='(unknown)'
        if usable!=1 or not site or not manager_site:
            return coloc,relation
        if city and manager_city:
            coloc='same recorded site and city' if site==manager_site and city==manager_city else 'different recorded site or city'
        if site==manager_site:
            return coloc,'same recorded site'
        a,b=self.zone(site,city),self.zone(manager_site,manager_city)
        if a is None or b is None:
            return coloc,'(unmapped geography)'
        delta=abs(self.offset(when,a)-self.offset(when,b))
        return coloc,'different site up to 4 hours' if delta<=240 else 'different site more than 4 hours'

    def __call__(self,frame):
        columns=['snapshot_date','site_key','city_key','manager_site','manager_city','usable_pair']
        work=frame[columns].copy()
        for key in columns[1:-1]:
            work[key]=work[key].fillna('')
        lookup={row:self.classify(*row) for row in work.drop_duplicates().itertuples(index=False,name=None)}
        values=[lookup[row] for row in work.itertuples(index=False,name=None)]
        coloc,relation=zip(*values)
        result=frame[['snapshot_date','person_key']].copy()
        result[self.features[0]]=coloc
        result[self.features[1]]=relation
        independent=result[self.features[0]].map({'same recorded site and city':1,'different recorded site or city':0,'(unknown)':-1})
        if not independent.eq(frame.colocation_check).all():
            raise RuntimeError('No reconcilia co-location con el cálculo independiente en Redshift.')
        years=pd.to_datetime(frame.snapshot_date).dt.year
        for year in years.unique():
            part=result.loc[years.eq(year)]
            raw=frame.loc[years.eq(year)]
            record=self.counts[int(year)]
            record['person_snapshots']+=len(part)
            record['colocation_observable']+=int(part[self.features[0]].ne('(unknown)').sum())
            record['same_site_city_rows']+=int(part[self.features[0]].eq('same recorded site and city').sum())
            record['timezone_observable']+=int((~part[self.features[1]].str.startswith('(')).sum())
            record['unmapped_timezone_rows']+=int(part[self.features[1]].eq('(unmapped geography)').sum())
            for label,key in [('same recorded site','same_site_rows'),('different site up to 4 hours','up_to_four_hours_rows'),('different site more than 4 hours','over_four_hours_rows')]:
                record[key]+=int(part[self.features[1]].eq(label).sum())
            record['independent_formula_mismatches']+=0
            self.people[int(year)].update(raw.person_key)
        return result

    def evidence(self):
        return {'reporting_mode':'presentation','outcome':'pass','method':'Mapping público unívoco en RAM; offsets de la fecha en ZoneInfo; co-location reconciliada contra Redshift.',
            'catalog':zones.CATALOG.relative_to(base.ROOT).as_posix(),'catalog_sha256':self.catalog_sha256,
            'catalog_diagnostics':self.diagnostics,'independent_dst_evidence':'input-evidence/v11-timezone-dst.json',
            'rows':[{'year':year,**row,'employee_count':len(self.people[year])} for year,row in sorted(self.counts.items())],
            'employee_level_rows_persisted':False,'location_hashes_persisted':False,'assessment_score_changed':False}


def transformer_for(name):
    if name=='timezone_v11':
        return TimezoneTransform()
    if name=='commute_v11':
        from b_v11_commute import CommuteTransform
        return CommuteTransform()
    raise ValueError('Transformación geográfica desconocida.')
