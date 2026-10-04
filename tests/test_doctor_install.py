"""Offline configuration and clean-install checks; no credentials or API calls."""
import json,pathlib,sys,tempfile,unittest
from jev_agent.doctor import configurations,public_server,npm_packages
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from install_skill import install
class DiscoveryTests(unittest.TestCase):
 def test_configuration_redaction(self):
  with tempfile.TemporaryDirectory() as d:
   h=pathlib.Path(d);(h/'.codex').mkdir();(h/'project').mkdir()
   (h/'.codex/config.toml').write_text('[mcp_servers.jev]\ncommand="node"\nargs=["private-command-argument"]\n[mcp_servers.jev.env]\nOPENROUTER_API_KEY="fixture"\n')
   rows,issues=configurations(h,h/'project');self.assertFalse(issues)
   row=next(x for x in rows if x['source']=='codex-user');out=json.dumps(public_server(row))
   self.assertNotIn('private-command-argument',out);self.assertNotIn('fixture',out)
   self.assertIn('configured',out);self.assertIn('not_tested',out)
 def test_unknown_name_metadata_not_compatibility(self):
  r=public_server({'name':'judge','source':'fixture','config':{'url':'https://example.invalid'}})
  self.assertFalse(r['jev_name_hint']);self.assertEqual(r['transport'],'remote')
 def test_install_and_refuse_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   target=install('codex','project',project=d)
   self.assertTrue((target/'SKILL.md').is_file());self.assertTrue((target/'scripts/jev_doctor.py').is_file())
   self.assertFalse(list(target.rglob('__pycache__')))
   with self.assertRaises(FileExistsError):install('codex','project',project=d)
 def test_claude_install_location(self):
  with tempfile.TemporaryDirectory() as d:
   target=install('claude','project',project=d)
   self.assertEqual(target,(pathlib.Path(d)/'.claude/skills/jev-for-agent').resolve())
