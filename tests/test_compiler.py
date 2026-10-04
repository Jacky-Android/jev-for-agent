import copy,json,pathlib,unittest
from jev_agent.compiler import compile_plan
from jev_agent.validation import ValidationError
class CompilerTests(unittest.TestCase):
 def plan(self):return json.loads((pathlib.Path(__file__).resolve().parents[1]/'examples/triage_plan.json').read_text())
 def test_compiles_only_judgments(self):self.assertEqual(set(compile_plan(self.plan())['questions']),{'cause','impact','blocks_core'})
 def test_dependent_questions_rejected(self):
  p=self.plan();p['steps'][1]['depends_on_answers']=['cause']
  with self.assertRaises(ValidationError):compile_plan(p)
 def test_no_semantic_questions_no_call(self):
  p=self.plan();p['steps']=p['steps'][3:]
  with self.assertRaises(ValidationError):compile_plan(p)
