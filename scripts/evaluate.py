#!/usr/bin/env python3
import _bootstrap
import argparse,json,pathlib,os
from jev_agent.validation import load_json,ValidationError,validate_packet
from jev_agent.runtime import Session
from jev_agent.providers import ProviderError
from jev_agent.security import redact

def main():
 p=argparse.ArgumentParser(description='Send one real Jev decision packet; no business actions are executed')
 p.add_argument('packet');p.add_argument('--provider',choices=['typesafe','openrouter','mcp']);p.add_argument('--model');p.add_argument('--mcp-name');p.add_argument('--output')
 a=p.parse_args()
 try:
  packet=load_json(pathlib.Path(a.packet).read_text());validate_packet(packet)
  with Session(a.provider,a.model or packet.get('model'),a.mcp_name) as session:r=session.evaluate(packet['state'],packet['questions'])
  text=json.dumps(redact(r),indent=2,ensure_ascii=False)
  if a.output:
   fd=os.open(a.output,os.O_CREAT|os.O_TRUNC|os.O_WRONLY,0o600)
   with os.fdopen(fd,'w') as f:f.write(text+'\n')
  print(text);return 0
 except (ProviderError,ValidationError) as e:print(json.dumps({'request_status':'failed','error':str(e)}));return 1
 except (OSError,ValueError):print('{"request_status":"failed","error":"Local input or output error; details suppressed"}');return 1
if __name__=='__main__':raise SystemExit(main())
