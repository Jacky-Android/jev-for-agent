"""Paid integration checks require explicit opt-in, never substitute fixtures."""
import os,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
@unittest.skipUnless(os.environ.get('JEV_RUN_LIVE')=='1','Live tests disabled; run verify_primitives.py explicitly')
class LiveTests(unittest.TestCase):
 def test_all_primitives(self):
  from verify_primitives import verify
  for row in verify(os.environ.get('JEV_PROVIDER'),os.environ.get('JEV_MODEL')):
   self.assertEqual(row['status'],'PASS',row.get('error'))
