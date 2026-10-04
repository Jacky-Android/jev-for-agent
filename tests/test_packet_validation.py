import copy,json,unittest
from jev_agent.validation import validate_packet,validate_answers,load_json,ValidationError

P={'state':{'report':'Export produces an empty file.'},'questions':{'route':{'type':'choice','instructions':'Which category describes report?','criteria':{'bug':'Unexpected behavior.','other':'No reported failure.'}}}}
class PacketTests(unittest.TestCase):
 def test_valid(self): self.assertEqual(validate_packet(P),[])
 def test_invalid_states(self):
  for s in [None,3,False,'',{},[]]:
   p=copy.deepcopy(P);p['state']=s
   with self.assertRaises(ValidationError):validate_packet(p)
 def test_empty_instructions(self):
  p=copy.deepcopy(P);p['questions']['route']['instructions']=' '
  with self.assertRaises(ValidationError):validate_packet(p)
 def test_duplicate_keys(self):
  with self.assertRaises(ValidationError):load_json('{"state":"a","state":"b"}')
 def test_score_boundaries(self):
  for n in [1,11]:
   p={'state':'x','questions':{'x':{'type':'score','instructions':'Rate impact.','criteria':[str(i) for i in range(n)]}}}
   with self.assertRaises(ValidationError):validate_packet(p)
 def test_noul_schema(self):
  p={'state':'x','questions':{'x':{'type':'noul','instructions':'Is it explicit?','criteria':{'yes':'yes'}}}}
  with self.assertRaises(ValidationError):validate_packet(p)
 def test_structured(self):
  p=copy.deepcopy(P);p['questions']['route']['instructions']={'question':'Which category?','scope':['report']};validate_packet(p)
 def test_duplicate_descriptions(self):
  p=copy.deepcopy(P);p['questions']['route']['criteria']={'a':'same','b':'same'}
  with self.assertRaises(ValidationError):validate_packet(p)
 def test_fixture_answers_not_live(self):
  a={'route':{'type':'choice','choice':'bug','probabilities':{'bug':.9,'other':.1},'confidence':.8}}
  validate_answers(P,a)
  for bad in [float('nan'),True,1.1]:
   b=copy.deepcopy(a);b['route']['probabilities']['bug']=bad
   with self.assertRaises(ValidationError):validate_answers(P,b)
 def test_missing_answer(self):
  with self.assertRaises(ValidationError):validate_answers(P,{})
 def test_score_legend(self):
  p={'state':'x','questions':{'s':{'type':'score','instructions':'Rate impact.','criteria':['No effect.','Core failure.']}}}
  a={'s':{'type':'score','score':.5,'legend':{'0':'No effect.','1':'Core failure.'},'probabilities':{'0':.5,'1':.5},'confidence':0}}
  validate_answers(p,a);a['s']['legend']['1']='Wrong'
  with self.assertRaises(ValidationError):validate_answers(p,a)
 def test_noul_no_native_confidence(self):
  p={'state':'x','questions':{'n':{'type':'noul','instructions':'Is it explicit?'}}};a={'n':{'type':'noul','noul':.5}}
  validate_answers(p,a);a['n']['confidence']=.9
  with self.assertRaises(ValidationError):validate_answers(p,a)

 def test_numeric_structured_state(self):
  p=copy.deepcopy(P);p['state']={'temperature':25,'enabled':False};validate_packet(p)
