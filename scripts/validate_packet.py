#!/usr/bin/env python3
import _bootstrap
import argparse,json,pathlib
from jev_agent.validation import load_json,validate_packet,ValidationError
from jev_agent.security import assert_no_secrets

def main():
 p=argparse.ArgumentParser(description='Static packet validation; no inference or paid requests')
 p.add_argument('packet');a=p.parse_args()
 try:
  packet=load_json(pathlib.Path(a.packet).read_text());warnings=validate_packet(packet);assert_no_secrets(packet)
  print(json.dumps({'status':'PASS','validation':'static_only','warnings':warnings}));return 0
 except (ValidationError,OSError):print(json.dumps({'status':'FAIL','reason':'Packet invalid or unreadable; inspect schema and remove sensitive data'}));return 1
if __name__=='__main__':raise SystemExit(main())
