"""Bounded MCP stdio initialization, discovery and tools/call; no shell eval."""
import json
import os
import queue
import subprocess
import threading
import time
from .providers import ProviderError
from .validation import load_json

class StdioMCP:
    def __init__(self,config,timeout=30):
        if not isinstance(config.get('command'),str):raise ProviderError('This configuration is not stdio; use the host agent for remote MCP')
        self.config=config;self.timeout=timeout;self.proc=None;self.messages=queue.Queue();self.seq=0
    def __enter__(self):
        env=dict(os.environ)
        # Environment is passed to the process, never tool arguments or stdout.
        for k,v in self.config.get('env',{}).items():
            if isinstance(v,str):
                if v.startswith('${') and v.endswith('}'):
                    v=os.environ.get(v[2:-1],'')
                env[k]=v
        try:
            self.proc=subprocess.Popen([self.config['command'],*self.config.get('args',[])],env=env,
                cwd=self.config.get('cwd'),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        except OSError:raise ProviderError('MCP process could not start (command details suppressed)') from None
        def read():
            try:
                while True:
                    line=self.proc.stdout.readline(2_000_001)
                    if not line:break
                    if len(line)>2_000_000:
                        self.messages.put(ProviderError('MCP response too large'));return
                    try:self.messages.put(load_json(line.decode()))
                    except Exception:self.messages.put(ProviderError('MCP stdout is not valid JSON-RPC'));return
            finally:self.messages.put(None)
        threading.Thread(target=read,daemon=True).start()
        try:
            self.metadata=self.rpc('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'jev-for-agent','version':'0.1.0'}})
            self.send({'jsonrpc':'2.0','method':'notifications/initialized'})
            return self
        except Exception:
            self.close();raise
    def send(self,message):
        try:
            self.proc.stdin.write((json.dumps(message)+'\n').encode());self.proc.stdin.flush()
        except (OSError,BrokenPipeError):raise ProviderError('MCP process input closed') from None
    def rpc(self,method,params):
        self.seq+=1;identity=self.seq
        self.send({'jsonrpc':'2.0','id':identity,'method':method,'params':params})
        deadline=time.monotonic()+self.timeout
        while True:
            try:message=self.messages.get(timeout=max(.001,deadline-time.monotonic()))
            except queue.Empty:raise ProviderError('MCP request timed out') from None
            if message is None:raise ProviderError('MCP process exited before response')
            if isinstance(message,Exception):raise message
            if 'method' in message and 'id' in message:
                self.send({'jsonrpc':'2.0','id':message['id'],'error':{'code':-32601,'message':'Client capability not offered'}})
                continue
            if message.get('id')==identity:
                if 'error' in message:raise ProviderError('MCP JSON-RPC error (body suppressed)')
                return message.get('result',{})
            if time.monotonic()>deadline:raise ProviderError('MCP request timed out')
    def tools(self):
        result=[];cursor=None;seen=set()
        for _ in range(20):
            page=self.rpc('tools/list',{'cursor':cursor} if cursor else {})
            result.extend(page.get('tools',[]));cursor=page.get('nextCursor')
            if not cursor:return result
            if cursor in seen:raise ProviderError('MCP pagination repeated cursor')
            seen.add(cursor)
        raise ProviderError('MCP tool-list pagination limit exceeded')
    def call(self,name,arguments):return self.rpc('tools/call',{'name':name,'arguments':arguments})
    def close(self):
        if self.proc:
            if self.proc.poll() is None:
                self.proc.terminate()
                try:self.proc.wait(timeout=3)
                except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait(timeout=3)
            for stream in (self.proc.stdin,self.proc.stdout):
                if stream:stream.close()
    def __exit__(self,*_):self.close()

def capabilities(tool):
    schema=tool.get('inputSchema',{});p=schema.get('properties',{})
    generic={'state','questions'}<=set(p)
    description=(tool.get('description','')+' '+json.dumps(schema)).lower()
    primitives=[x for x in ('choice','score','noul') if x in description]
    semantic=any(x in description for x in ('probabilit','classif','rerank','judgment','judgement','system one','typesafe'))
    return {'name':tool.get('name'),'generic_state_questions':generic,'primitive_hints':primitives,'semantic_candidate':semantic or generic,'confirmed_compatible':False}
