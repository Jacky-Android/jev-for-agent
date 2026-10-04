import unittest
from jev_agent.policy import gate
class PolicyTests(unittest.TestCase):
 def test_uncertain_noul(self):self.assertEqual(gate({'type':'noul','noul':.5},authorized=True,fresh=True,evidence_complete=True)['route'],'review')
 def test_no_permission(self):self.assertEqual(gate({'type':'noul','noul':1},authorized=False,fresh=True,evidence_complete=True)['route'],'abstain')
 def test_stale(self):self.assertEqual(gate({'type':'noul','noul':1},authorized=True,fresh=False,evidence_complete=True)['route'],'gather_more_evidence')
 def test_high_risk(self):self.assertEqual(gate({'type':'noul','noul':1},authorized=True,fresh=True,evidence_complete=True,high_risk=True)['route'],'review')
 def test_negative_is_not_positive_action(self):
  r=gate({'type':'noul','noul':.01},authorized=True,fresh=True,evidence_complete=True);self.assertEqual(r['value'],False)
