import unittest
import uuid
from jev_agent.security import assert_no_secrets,redact
from jev_agent.validation import ValidationError
class SecurityTests(unittest.TestCase):
 def test_secret_rejected_and_redacted(self):
  env={'OPENROUTER_API_KEY':uuid.uuid4().hex}
  text={'report':'Echo: '+env['OPENROUTER_API_KEY']}
  with self.assertRaises(ValidationError):assert_no_secrets(text,env)
  self.assertNotIn(env['OPENROUTER_API_KEY'],str(redact(text,env)))
 def test_credential_field(self):
  with self.assertRaises(ValidationError):assert_no_secrets({'api_key':'abc'}, {})
 def test_harmless_state(self):assert_no_secrets({'report':'Run the migration.'},{})

 def test_semantic_labels_preserved(self):
  value={'criteria':{'password':'Requests about password resets.'},'probabilities':{'password':1.0}}
  assert_no_secrets(value,{})
  self.assertEqual(redact(value,{}),value)
 def test_secret_value_in_criteria_still_rejected(self):
  env={'TYPESAFE_API_KEY':uuid.uuid4().hex}
  with self.assertRaises(ValidationError):assert_no_secrets({'criteria':{'password':env['TYPESAFE_API_KEY']}},env)
