#!/usr/bin/env python3
"""Live tests only. No mock, fixture, or replay success path."""
import _bootstrap
import argparse,json,os,pathlib,datetime
from jev_agent.validation import load_json,ValidationError
from jev_agent.providers import ProviderError
from jev_agent.runtime import Session
from jev_agent.security import redact

def verify(provider=None,model=None,primitive=None,mcp_name=None):
 results=[]
 with Session(provider,model,mcp_name) as session:
  for name in ([primitive] if primitive else ['choice','score','noul']):
   packet=load_json((_bootstrap.ROOT/'examples'/f'{name}.json').read_text())
   try:
    result=session.evaluate(packet['state'],packet['questions'])
    results.append({'primitive':name,'status':'PASS','checks':'response shape, range, keys, distribution, legend (Score)','result':result})
   except (ProviderError,ValidationError) as e:
    results.append({'primitive':name,'status':'FAIL','provider':session.provider,'actual_model':None,'error':str(e)})
 return results

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--provider',choices=['typesafe','openrouter','mcp']);p.add_argument('--model');p.add_argument('--mcp-name')
 g=p.add_mutually_exclusive_group();g.add_argument('--primitive',choices=['choice','score','noul']);g.add_argument('--all',action='store_true')
 p.add_argument('--output');a=p.parse_args()
 try:results=verify(a.provider,a.model,a.primitive,a.mcp_name)
 except (ProviderError,ValidationError) as e:
  print(str(e));return 2
 report={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_mode':'live','results':results}
 for row in results:
  r=row.get('result',row)
  print(json.dumps({'status':row['status'],'provider':r.get('provider'),'actual_model':r.get('actual_model'),'model_resolution':r.get('model_resolution'),'primitive':row['primitive'],'usage':r.get('usage'),'latency_ms':r.get('latency_ms'),'error':row.get('error')},ensure_ascii=False))
 if a.output:
  fd=os.open(a.output,os.O_CREAT|os.O_TRUNC|os.O_WRONLY,0o600)
  with os.fdopen(fd,'w') as f:json.dump(redact(report),f,indent=2,ensure_ascii=False)
 return 0 if all(x['status']=='PASS' for x in results) else 1
if __name__=='__main__':raise SystemExit(main())
