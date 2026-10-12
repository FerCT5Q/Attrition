"""Contratos de comentarios con texto y llaves exclusivamente sintéticos."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import b_v11_qvoice_comments as comments
import b_incremental_qvoice as model_q


class CommentTests(unittest.TestCase):
    def test_compiled_patterns_reproduce_original_helpers(self):
        examples=['','More remote work and flexible office days.',
            'Home office is useful. Tools and automation can improve.',
            'Please improve salaries, career growth and manager feedback.',
            'Quisiera trabajo híbrido, menos carga de trabajo y más respeto.',
            'Job security and company direction matter.',
            'Office policy is mandatory; commute costs are high.',
            'I like remote work. We need new tools.',
            'Compensation process changes support career development.',
            'A promotion is different from promotional material.']
        for text in examples:
            values={'doing_well':'','can_improve':text,'processes_to_improve':''}
            self.assertEqual(comments.classify(values),comments.classify(values,reference=True))

    def test_no_comment_is_distinct_from_no_topic_and_question_absent(self):
        empty=comments.classify({'doing_well':None,'can_improve':None})
        self.assertEqual(empty['qv_comment_presence'],'v0')
        self.assertEqual(empty['qv_comment_rewards'],'no_comment')
        neutral=comments.classify({'can_improve':'Improve the cafeteria menu.'})
        self.assertEqual(neutral['qv_comment_rewards'],'v0')
        absent=comments.classify({'doing_well':'The cafeteria menu is good.'})
        self.assertEqual(absent['qv_comment_rewards'],'question_absent')
        self.assertEqual(set(empty),set(comments.FEATURES))

    def test_request_does_not_cross_clause_or_home_office_boundary(self):
        result=comments.classify({'can_improve':'I like remote work. We need better tools.'})
        self.assertEqual(result['qv_remote_hybrid_request'],'v0')
        home=comments.classify({'can_improve':'Home office should continue.'})
        self.assertEqual(home['qv_comment_office'],'v0')

    def test_link_preserves_no_link_duplicate_and_episode_states(self):
        frame=pd.DataFrame({'person_key':pd.Categorical(['matched','none','dup','new-episode']),
            'same_episode_2024':[1,1,1,0]})
        lookup={'matched':{f:'v0' for f in comments.FEATURES},'new-episode':{f:'v1' for f in comments.FEATURES}}
        result=comments.attach_lookup(frame,lookup,{'dup'},2024)
        self.assertEqual(result.qv_comment_presence.tolist(),['v0','no_linked_row','duplicate','different_employment_episode'])
        self.assertEqual(set(result),set(comments.FEATURES))

    def test_availability_control_drops_content_but_keeps_missing_reason(self):
        frame=pd.DataFrame({'qv_comment_rewards':['v0','v1','no_comment','no_linked_row']})
        encoded=model_q.prepared(frame,['qv_comment_rewards'])
        self.assertEqual(encoded.availability_qv_comment_rewards.tolist(),['available','available','no_comment','no_linked_row'])

    def test_annual_replacement_does_not_read_wave_2026_or_rescue_old_response(self):
        frame=pd.DataFrame({'snapshot_date':pd.to_datetime(['2025-06-01','2026-06-01']),
            'person_key':pd.Categorical(['a','a']),'same_episode_2024':[1,1],'same_episode_2025':[1,1]})
        config={'sources':{'waves':[{'year':y} for y in [2024,2025,2026]]},'temporal_rules':{'maximum_age_months':12}}
        meta={'waves':[{'year':y} for y in [2024,2025]]}
        def source(wave,*args):
            lookup={'a':{f:'v1' for f in comments.FEATURES}} if wave['year']==2024 else {}
            return lookup,set(),{'year':wave['year']}
        with patch.object(comments,'availability_date',side_effect=lambda w:pd.Timestamp(year=w['year']+1,month=1,day=1)),patch.object(comments,'scan',side_effect=source) as scanner:
            result,_=comments.attach(frame,config,meta,'synthetic')
        self.assertEqual([c.args[0]['year'] for c in scanner.call_args_list],[2024,2025])
        self.assertEqual(result.qv_comment_presence.astype(str).tolist(),['v1','no_linked_row'])


if __name__=='__main__':
    unittest.main()
