import unittest
from jev_agent.providers import select_provider,ProviderError,normalize
class SelectionTests(unittest.TestCase):
 def test_mcp_first(self): self.assertEqual(select_provider({},mcp_available=True),'mcp')
 def test_typesafe_before_router(self):self.assertEqual(select_provider({'TYPESAFE_API_KEY':'fixture','OPENROUTER_API_KEY':'fixture'}),'typesafe')
 def test_explicit(self):self.assertEqual(select_provider({'JEV_PROVIDER':'openrouter','TYPESAFE_API_KEY':'fixture','OPENROUTER_API_KEY':'fixture'},mcp_available=True),'openrouter')
 def test_no_silent_switch(self):
  with self.assertRaises(ProviderError):select_provider({'JEV_PROVIDER':'typesafe','OPENROUTER_API_KEY':'fixture'})
 def test_no_credential(self):
  with self.assertRaises(ProviderError):select_provider({})
 def test_existing_billing(self):self.assertEqual(select_provider({'TYPESAFE_API_KEY':'fixture','OPENROUTER_API_KEY':'fixture'},configured_provider='openrouter'),'openrouter')
 def test_normalized_missing_not_zero(self):
  raw={'answers':{'x':{'type':'noul','noul':.5}}};r=normalize(raw,'openrouter','~typesafe/jev-latest',10)
  self.assertIsNone(r['actual_model']);self.assertIsNone(r['usage']);self.assertEqual(r['raw_response'],raw)
 def test_actual_from_response(self):
  r=normalize({'model':'typesafe/jev-1.13','answers':{}},'openrouter','~typesafe/jev-latest',10)
  self.assertEqual(r['actual_model'],'typesafe/jev-1.13')

class ModelTests(unittest.TestCase):
 def test_openrouter_decision_discovery_not_chat_default(self):
  from jev_agent.providers import HTTPProvider
  c=HTTPProvider('openrouter',{'OPENROUTER_API_KEY':'fixture'})
  seen=[]
  def fixture_request(path,payload=None):
   seen.append(path);return {'data':[{'id':'typesafe/jev-1.13'},{'id':'~typesafe/jev-latest'}]},None
  c.request=fixture_request
  self.assertEqual(c.resolve_model()[0],'~typesafe/jev-latest')
  self.assertIn('output_modalities=decisions',seen[0])
 def test_refuse_chat_router(self):
  from jev_agent.providers import HTTPProvider
  c=HTTPProvider('openrouter',{'OPENROUTER_API_KEY':'fixture'});c.catalog=[{'id':'typesafe/jev-router'}]
  with self.assertRaises(ProviderError):c.resolve_model('typesafe/jev-router')

class SessionSelectionTests(unittest.TestCase):
 def test_explicit_provider_overrides_ambiguous_other_configs(self):
  from unittest.mock import patch
  from jev_agent.runtime import Session
  rows=[{'name':'jev-a','source':'fixture','config':{'env':{'TYPESAFE_API_KEY':'fixture'}}},
        {'name':'jev-b','source':'fixture','config':{'env':{'OPENROUTER_API_KEY':'fixture'}}}]
  with patch('jev_agent.runtime.configurations',return_value=(rows,[])),patch('jev_agent.runtime.HTTPProvider'),patch.dict('os.environ',{'OPENROUTER_API_KEY':'fixture'}):
   with Session(provider='openrouter') as session:self.assertEqual(session.provider,'openrouter')
