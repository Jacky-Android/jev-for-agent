"""Offline protocol fixtures. None of these tests verifies live Jev inference."""
import json,subprocess,unittest
from unittest.mock import patch
from jev_agent.providers import HTTPProvider,ExistingMCP,ProviderError
from jev_agent.mcp import capabilities
Q={'check':{'type':'noul','instructions':'Does the note explicitly require migration?'}}
RAW={'model':'fixture-model','answers':{'check':{'type':'noul','noul':.7}}}
class AdapterTests(unittest.TestCase):
 def client(self):return HTTPProvider('openrouter',{'OPENROUTER_API_KEY':'fixture','JEV_HTTP_TRANSPORT':'curl'})
 def test_correct_endpoint_and_raw_preserved(self):
  for provider,path in [('typesafe','/systemone'),('openrouter','/alpha/decisions')]:
   c=HTTPProvider(provider,{'TYPESAFE_API_KEY':'fixture','OPENROUTER_API_KEY':'fixture'})
   seen=[]
   c.resolve_model=lambda model:('fixture-model',True)
   def request(route,payload):seen.append((route,payload));return RAW,'request-fixture'
   c.request=request;r=c.evaluate('Migration is required.',Q)
   self.assertEqual(seen[0][0],path);self.assertIs(r['raw_response'],RAW)
   self.assertEqual(r['request_id'],'request-fixture')
 def test_curl_secret_not_in_argv(self):
  c=self.client()
  with patch('jev_agent.providers.subprocess.run',return_value=subprocess.CompletedProcess([],0,json.dumps(RAW).encode()+b'\n200')) as call:
   c.request('/alpha/decisions',{'state':'note','questions':Q})
   args,kwargs=call.call_args
   self.assertNotIn(c.key,' '.join(args[0]));self.assertIn(b'Authorization: Bearer fixture',kwargs['input'])
   self.assertNotIn('--location',args[0])
 def test_http_failure_body_suppressed(self):
  with patch('jev_agent.providers.subprocess.run',return_value=subprocess.CompletedProcess([],0,b'private-body\n401')):
   with self.assertRaises(ProviderError) as e:self.client().request('/alpha/decisions',{})
   self.assertNotIn('private-body',str(e.exception))
 def test_network_failure_no_retry(self):
  with patch('jev_agent.providers.subprocess.run',return_value=subprocess.CompletedProcess([],28,b'')) as call:
   with self.assertRaises(ProviderError):self.client().request('/alpha/decisions',{})
   self.assertEqual(call.call_count,1)
 def test_rate_limit_bounded_retry(self):
  rows=[subprocess.CompletedProcess([],0,b'{}\n429'),subprocess.CompletedProcess([],0,b'{}\n529')]
  with patch('jev_agent.providers.subprocess.run',side_effect=rows) as call,patch('jev_agent.providers.time.sleep'):
   with self.assertRaises(ProviderError):self.client().request('/alpha/decisions',{})
   self.assertEqual(call.call_count,2)
 def test_generic_mcp_both_envelopes(self):
  tool={'name':'judge','inputSchema':{'properties':{'state':{},'questions':{}},'required':['state','questions']}}
  for reply in [{'structuredContent':RAW},{'content':[{'type':'text','text':json.dumps(RAW)}]}]:
   c=ExistingMCP(lambda name,args:reply,tool,'openrouter');r=c.evaluate('note',Q)
   self.assertEqual(r['answers'],RAW['answers']);self.assertEqual(r['billing_provider'],'openrouter')
   self.assertEqual(r['raw_mcp_response'],reply)
 def test_specialized_mcp_cannot_take_generic_packet(self):
  with self.assertRaises(ProviderError):ExistingMCP(lambda *a:None,{'inputSchema':{'properties':{'code':{}}}})
 def test_discovery_does_not_claim_compatibility(self):
  c=capabilities({'name':'unrelated-name','description':'probabilistic judgment','inputSchema':{'properties':{'state':{},'questions':{}}}})
  self.assertTrue(c['generic_state_questions']);self.assertFalse(c['confirmed_compatible'])
 def test_bad_mcp_payload(self):
  tool={'name':'judge','inputSchema':{'properties':{'state':{},'questions':{}}}}
  with self.assertRaises(ProviderError):ExistingMCP(lambda *a:{'structuredContent':[]},tool).evaluate('note',Q)
