"""Real transports only. Unit fixtures live in tests and are never providers."""
import json
import http.client
import subprocess
import shutil
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from .validation import ValidationError,load_json,validate_packet,validate_answers
from .security import assert_no_secrets,redact

class ProviderError(RuntimeError):
    pass

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        raise ProviderError('Redirect refused; credentials were not forwarded')

def select_provider(env=None, *, mcp_available=False, configured_provider=None):
    env=os.environ if env is None else env
    explicit=env.get('JEV_PROVIDER','auto').lower()
    if explicit not in ('auto','','mcp','typesafe','openrouter'):
        raise ProviderError('Unsupported explicit provider; no billing fallback performed')
    choice=explicit if explicit not in ('auto','') else None
    if not choice:
        choice='mcp' if mcp_available else configured_provider
    if not choice:
        choice='typesafe' if env.get('TYPESAFE_API_KEY') else 'openrouter' if env.get('OPENROUTER_API_KEY') else None
    if choice=='mcp':
        if not mcp_available:raise ProviderError('MCP requested but compatible connection is unavailable')
        return choice
    if choice not in ('typesafe','openrouter'):
        raise ProviderError('LIVE VERIFICATION BLOCKED: NO JEV CREDENTIAL')
    if not env.get('TYPESAFE_API_KEY' if choice=='typesafe' else 'OPENROUTER_API_KEY'):
        raise ProviderError('Selected provider credential is missing; no billing fallback performed')
    return choice

def normalize(raw, provider, requested_model, latency_ms, request_id=None, *, pinned_model=False):
    if not isinstance(raw,dict) or not isinstance(raw.get('answers'),dict):
        raise ProviderError('Provider response missing answers object')
    reported=raw.get('model')
    if reported is not None and not isinstance(reported,str):
        raise ProviderError('Invalid response model')
    alias=not reported or 'latest' in reported or 'preview' in reported
    actual=reported if not alias else (requested_model if pinned_model else None)
    return {'provider':provider,'actual_model':actual,'reported_model':reported,
            'requested_model':requested_model,'model_resolution':'response' if not alias else 'pinned_request' if pinned_model else 'unresolved',
            'request_status':'success','source_mode':'live','answers':raw['answers'],
            'raw_response':raw,'usage':raw.get('usage'),'latency_ms':round(latency_ms,3),
            'request_id':raw.get('id') or request_id}

class HTTPProvider:
    def __init__(self, provider, env=None, timeout=30, attempts=2):
        if provider not in ('typesafe','openrouter'):raise ProviderError('Unknown HTTP provider')
        self.provider=provider;self.env=dict(os.environ if env is None else env)
        self.key=self.env.get('TYPESAFE_API_KEY' if provider=='typesafe' else 'OPENROUTER_API_KEY')
        if not self.key:raise ProviderError('Selected provider credential is missing')
        default='https://api.typesafe.ai/v1' if provider=='typesafe' else 'https://openrouter.ai/api'
        var='TYPESAFE_BASE_URL' if provider=='typesafe' else 'JEV_OPENROUTER_BASE_URL'
        self.base=self.env.get(var,default).rstrip('/')
        parsed=urllib.parse.urlsplit(self.base)
        if parsed.scheme!='https' or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ProviderError('Provider base URL must be HTTPS without credentials/query/fragment')
        self.timeout=min(max(float(timeout),1),60);self.attempts=min(max(int(attempts),1),3)
        self.opener=urllib.request.build_opener(NoRedirect());self.catalog=None
        self.http_transport=self.env.get('JEV_HTTP_TRANSPORT','curl' if shutil.which('curl') else 'urllib')
        if self.http_transport not in ('curl','urllib'):raise ProviderError('Unknown HTTP transport')

    def request(self,path,payload=None):
        if self.http_transport=='curl':return self.request_curl(path,payload)
        encoded=json.dumps(payload,allow_nan=False).encode() if payload is not None else None
        headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json','Accept':'application/json','User-Agent':'jev-for-agent/0.1.0'}
        deadline=time.monotonic()+self.timeout
        for attempt in range(self.attempts):
            req=urllib.request.Request(self.base+path,data=encoded,headers=headers)
            try:
                remaining=deadline-time.monotonic()
                if remaining<=0:raise ProviderError('Request deadline exceeded')
                with self.opener.open(req,timeout=remaining) as r:
                    body=r.read(2_000_001)
                    if len(body)>2_000_000:raise ProviderError('Response exceeds local size limit')
                    try:raw=load_json(body.decode())
                    except (ValidationError,UnicodeError):raise ProviderError('Invalid JSON response (body suppressed)') from None
                    return raw,r.headers.get('x-request-id')
            except urllib.error.HTTPError as e:
                status=e.code;retry=e.headers.get('Retry-After');e.close()
                # Only known rate-limit / overload responses; never network timeouts.
                if status in (429,529) and attempt+1<self.attempts:
                    delay=min(4,float(retry)) if retry and retry.isdigit() else .5*(2**attempt)
                    if time.monotonic()+delay>=deadline:raise ProviderError('Request deadline exceeded') from None
                    time.sleep(delay);continue
                raise ProviderError(f'{self.provider} HTTP {status}; response body suppressed') from None
            except ProviderError:raise
            except (OSError,ValueError,TimeoutError,http.client.HTTPException):
                raise ProviderError('Transport failed or timed out; not retried to avoid duplicate billing') from None
        raise ProviderError('Request attempts exhausted')

    def request_curl(self,path,payload=None):
        # Secret header and payload are piped through stdin, never process argv.
        config='header = '+json.dumps('Authorization: Bearer '+self.key)+'\n'
        config+='header = "Content-Type: application/json"\nheader = "Accept: application/json"\n'
        if payload is not None:
            config+='data-binary = '+json.dumps(json.dumps(payload,allow_nan=False))+'\n'
        deadline=time.monotonic()+self.timeout
        for attempt in range(self.attempts):
            remaining=deadline-time.monotonic()
            if remaining<=0:raise ProviderError('Request deadline exceeded')
            command=['curl','--disable','--silent','--show-error','--http1.1','--proto','=https',
                     '--max-time',str(remaining),'--max-filesize','2000000',
                     '--request','POST' if payload is not None else 'GET',
                     '--url',self.base+path,'--write-out','\n%{http_code}','--config','-']
            try:
                process=subprocess.run(command,input=config.encode(),stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=remaining+1)
            except (OSError,subprocess.TimeoutExpired):raise ProviderError('HTTP transport unavailable or timed out; request not retried') from None
            if process.returncode:raise ProviderError('HTTP transport failed; request not retried to avoid duplicate billing')
            try:
                body,code=process.stdout.rsplit(b'\n',1);status=int(code)
            except (ValueError,TypeError):raise ProviderError('Invalid HTTP transport response') from None
            if status in (429,529) and attempt+1<self.attempts:
                delay=.5*(2**attempt)
                if time.monotonic()+delay>=deadline:raise ProviderError('Request deadline exceeded')
                time.sleep(delay);continue
            if not 200<=status<300:raise ProviderError(f'{self.provider} HTTP {status}; response body suppressed')
            if len(body)>2_000_000:raise ProviderError('Response exceeds local size limit')
            try:return load_json(body.decode()),None
            except (ValidationError,UnicodeError):raise ProviderError('Invalid JSON response (body suppressed)') from None
        raise ProviderError('Request attempts exhausted')

    def models(self):
        path='/models' if self.provider=='typesafe' else '/v1/models?output_modalities=decisions&q=typesafe'
        raw,_=self.request(path)
        rows=raw.get('models') if self.provider=='typesafe' else raw.get('data')
        if not isinstance(rows,list):raise ProviderError('Model discovery returned an unsupported schema')
        self.catalog=[r for r in rows if isinstance(r,dict)]
        return self.catalog

    def resolve_model(self,model=None):
        rows=self.catalog if self.catalog is not None else self.models()
        requested=model or self.env.get('JEV_MODEL') or self.env.get('JEV_MCP_MODEL')
        if self.provider=='typesafe':
            requested=requested or self.env.get('TYPESAFE_DEFAULT_MODEL') or 'jev-latest'
            ids={x.get('name') for x in rows}
            if requested in ids:return requested,False
            # TypeSafe documents that concrete IDs can be valid while absent from /models.
            # Resolve allowed concrete release IDs from live official models documentation.
            if re.fullmatch(r'jev-\d+(?:\.\d+){1,2}',requested):
                try:
                    with urllib.request.urlopen('https://docs.typesafe.ai/models.md',timeout=15) as r:doc=r.read(100_000).decode()
                    if requested in re.findall(r'`(jev-\d+(?:\.\d+){1,2})`',doc):return requested,True
                except (OSError,ValueError,http.client.HTTPException):pass
            raise ProviderError('Requested TypeSafe model not confirmed by model discovery or live official model docs')
        requested=requested or '~typesafe/jev-latest'
        ids={x.get('id') for x in rows}
        if requested in ids and re.fullmatch(r'~?typesafe/jev-(?:latest|\d+(?:\.\d+){1,2})',requested):
            return requested,'latest' not in requested
        raise ProviderError('Requested OpenRouter Jev decision model not in live model catalog; no silent substitution')

    def evaluate(self,state,questions,model=None):
        packet={'state':state,'questions':questions};validate_packet(packet);assert_no_secrets(packet,self.env)
        requested,pinned=self.resolve_model(model)
        packet['model']=requested
        start=time.monotonic();raw,rid=self.request('/systemone' if self.provider=='typesafe' else '/alpha/decisions',packet)
        # Preserve legitimate responses exactly; secret-reflecting responses are rejected.
        assert_no_secrets(raw,self.env)
        validate_answers(packet,raw.get('answers') if isinstance(raw,dict) else None)
        return normalize(raw,self.provider,requested,(time.monotonic()-start)*1000,rid,pinned_model=pinned)

class ExistingMCP:
    """Adapter for a discovered generic tool; callback invokes tools/call on its host.

    Specialized tools are invoked by the host agent against their own schema;
    arbitrary Score rubrics must not be squeezed into fixed-review wrappers.
    """
    def __init__(self,call_tool,tool,provider=None):
        props=tool.get('inputSchema',{}).get('properties',{})
        if not {'state','questions'}<=set(props):
            raise ProviderError('This MCP tool is specialized; use its documented task schema or an explicitly selected HTTP provider')
        self.call_tool=call_tool;self.tool=tool;self.billing=provider
    def evaluate(self,state,questions,model=None):
        packet={'state':state,'questions':questions};validate_packet(packet);assert_no_secrets(packet)
        if model:
            if 'model' not in self.tool['inputSchema'].get('properties',{}):
                raise ProviderError('MCP tool cannot accept a model override')
            packet['model']=model
        required=set(self.tool['inputSchema'].get('required',[]))
        if not required<=set(packet):raise ProviderError('Generic MCP tool has additional required arguments; inspect schema')
        start=time.monotonic();reply=self.call_tool(self.tool['name'],packet)
        if reply.get('isError'):raise ProviderError('MCP tools/call failed; content suppressed')
        raw=reply.get('structuredContent')
        if raw is None:
            blocks=[b.get('text','') for b in reply.get('content',[]) if b.get('type')=='text']
            if len(blocks)!=1:raise ProviderError('MCP response requires an implementation-specific decoder')
            raw=load_json(blocks[0])
        if not isinstance(raw,dict):raise ProviderError('MCP response must be an object')
        assert_no_secrets(raw);validate_answers(packet,raw.get('answers'))
        r=normalize(raw,'mcp',model,(time.monotonic()-start)*1000)
        r['billing_provider']=raw.get('provider') or self.billing
        r['raw_mcp_response']=reply
        return r
