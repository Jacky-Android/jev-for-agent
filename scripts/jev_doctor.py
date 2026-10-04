#!/usr/bin/env python3
import _bootstrap
import argparse,json
from jev_agent.doctor import doctor
from jev_agent.providers import ProviderError
from jev_agent.validation import load_json
p=argparse.ArgumentParser(description='Read-only Jev environment inventory; probing does not imply inference success.')
p.add_argument('--json',action='store_true');p.add_argument('--probe-mcp',metavar='NAME',help='Initialize configured stdio server and list tools; may start its configured command')
p.add_argument('--discover-models',action='store_true');p.add_argument('--provider',choices=['typesafe','openrouter','mcp']);p.add_argument('--model')
p.add_argument('--agent-tools',help='Host-exported tools/list JSON; never secrets')
def main():
 a=p.parse_args()
 try:
  tools=load_json(open(a.agent_tools).read()) if a.agent_tools else None
  if isinstance(tools,dict):tools=tools.get('tools',[])
  r=doctor(probe_mcp=a.probe_mcp,discover_models=a.discover_models,provider=a.provider,model=a.model,agent_tools=tools)
  if not a.json:print('JEV FOR AGENT DOCTOR\nMCP / Client Version and Jev Model Version are separate.\n')
  print(json.dumps(r,indent=2,ensure_ascii=False))
  return 2 if r['status']=='NOT READY' else 0
 except (ProviderError,OSError,ValueError) as e:print(type(e).__name__+': diagnostic failed (details suppressed)');return 2
if __name__=='__main__':raise SystemExit(main())
