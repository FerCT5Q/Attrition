"""Casos sintéticos del proxy geográfico; no lee registros de RH."""
from collections import defaultdict
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from b_v11_geography import TimezoneTransform
from b_v11_commute import CommuteTransform,distance_band,independent_distance
import build_global_commute_distance_evidence as commute_source


class TimezoneTests(unittest.TestCase):
    def setUp(self):
        self.t=object.__new__(TimezoneTransform)
        self.t.sites={'ny':'America/New_York','ak':'America/Anchorage','la':'America/Los_Angeles','uk':'Europe/London'}
        self.t.cities={'newyork':'America/New_York','london':'Europe/London'}
        self.t.offsets={}
        self.t.counts=defaultdict(lambda:defaultdict(int))
        self.t.people=defaultdict(set)

    def test_four_hour_boundary_and_dst_use_prediction_date(self):
        self.assertEqual(self.t.classify('2025-01-15','ny','', 'ak','',1)[1],'different site up to 4 hours')
        self.assertEqual(self.t.classify('2025-01-15','la','', 'uk','',1)[1],'different site more than 4 hours')
        self.assertEqual(self.t.offset('2025-01-15','America/Los_Angeles'),-480)
        self.assertEqual(self.t.offset('2025-07-15','America/Los_Angeles'),-420)

    def test_unknown_conflicts_and_same_code_do_not_imply_same_city(self):
        self.assertIsNone(self.t.zone('ny','london'))
        self.assertEqual(self.t.classify('2025-01-15','ny','london','ak','',1)[1],'(unmapped geography)')
        self.assertEqual(self.t.classify('2025-01-15','ny','newyork','ny','london',1),
                         ('different recorded site or city','same recorded site'))
        self.assertEqual(self.t.classify('2025-01-15','ny','newyork','ny','newyork',0),('(unknown)','(unknown)'))

    def test_transform_drops_components_and_rejects_sql_disagreement(self):
        frame=pd.DataFrame({'snapshot_date':[pd.Timestamp('2025-01-15')],'person_key':['synthetic'],
            'site_key':['ny'],'city_key':['newyork'],'manager_site':['ny'],'manager_city':['newyork'],
            'usable_pair':[1],'colocation_check':[1]})
        result=self.t(frame)
        self.assertEqual(set(result),{'snapshot_date','person_key',*self.t.features})
        frame['colocation_check']=0
        with self.assertRaises(RuntimeError):
            self.t(frame)


class CommuteTests(unittest.TestCase):
    def test_bands_and_independent_spherical_formula(self):
        self.assertEqual(distance_band(0),'0–<1 km')
        self.assertEqual(distance_band(.999),'0–<1 km')
        self.assertEqual(distance_band(1),'1–<2 km')
        self.assertEqual(distance_band(30),'30+ km')
        office={'latitude':35.,'longitude':-115.}
        actual=commute_source.haversine_km(34.,-116.,office)
        self.assertLess(abs(actual-independent_distance(34.,-116.,office)),.0001)

    def test_missing_catalog_never_calls_network_fallback(self):
        transform=object.__new__(CommuteTransform)
        transform.centroids={}
        transform.sources={}
        with patch.object(commute_source,'download_centroids',side_effect=AssertionError('No debe descargar')):
            self.assertEqual(transform.centroid_map('ZZ_NOT_A_COUNTRY'),{})

    def test_unknown_and_offsite_cannot_be_zero_distance(self):
        transform=object.__new__(CommuteTransform)
        self.assertEqual(transform.classify({'valid_components':1,'onsite_flag':-1})[0],'(unknown)')
        self.assertEqual(transform.classify({'valid_components':1,'onsite_flag':0})[0],'(not onsite)')
        self.assertEqual(transform.classify({'valid_components':0,'onsite_flag':1})[0],'(unknown)')

    def test_postal_prefix_prefers_specific_match(self):
        transform=object.__new__(CommuteTransform)
        row={name:name for name in transform.input_columns}
        keys=transform.postal_keys(row,'GB')
        self.assertEqual(keys[-3:],['postal_hash_prefix_4','postal_hash_prefix_3','postal_hash_prefix_2'])


if __name__=='__main__':
    unittest.main()
