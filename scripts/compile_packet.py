#!/usr/bin/env python3
"""Agent authors a semantic plan; this deterministic compiler checks/writes the wire packet."""
import _bootstrap
import argparse,json,pathlib
from jev_agent.compiler import compile_plan
from jev_agent.validation import load_json,ValidationError

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('plan');p.add_argument('--output',required=True);a=p.parse_args()
 try:
  packet=compile_plan(load_json(pathlib.Path(a.plan).read_text()))
  pathlib.Path(a.output).write_text(json.dumps(packet,indent=2,ensure_ascii=False)+'\n')
  print('PASS: packet compiled and statically validated; no Jev inference yet');return 0
 except ValidationError as e:print('FAIL: '+str(e));return 1
 except (OSError,ValueError):print('FAIL: unreadable plan or output; details suppressed');return 1
if __name__=='__main__':raise SystemExit(main())
