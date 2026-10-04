"""Do not expose credentials through packets, exceptions, or reports."""
import json
import os
import re
from .validation import ValidationError
SECRET_NAME = re.compile(r'(api.?key|token|secret|password|authorization)',re.I)
TOKEN = re.compile(r'\b(?:sk-or-v1-|sk-)[A-Za-z0-9_-]{16,}\b|Bearer\s+\S+',re.I)

def secrets(env=None):
    env=os.environ if env is None else env
    return [v for k,v in env.items() if SECRET_NAME.search(k) and isinstance(v,str) and len(v)>=8]

def assert_no_secrets(value, env=None):
    text=json.dumps(value,ensure_ascii=False)
    if TOKEN.search(text) or any(v in text for v in secrets(env)):
        raise ValidationError('Possible credential in payload; request blocked (value suppressed)')
    def walk(x, parent=None):
        if isinstance(x,dict):
            for k,v in x.items():
                if parent not in ('criteria','probabilities','legend') and SECRET_NAME.fullmatch(k) and v:
                    raise ValidationError('Credential-bearing field in payload; request blocked')
                walk(v,k)
        elif isinstance(x,list):
            for v in x:walk(v)
    walk(value)

def redact(value, env=None):
    sensitive=secrets(env)
    def walk(v, parent=None):
        if isinstance(v,str):
            for s in sensitive:v=v.replace(s,'[REDACTED]')
            return TOKEN.sub('[REDACTED]',v)
        if isinstance(v,dict):
            return {walk(k):('[REDACTED]' if parent not in ('criteria','probabilities','legend') and SECRET_NAME.fullmatch(k) else walk(x,k)) for k,x in v.items()}
        if isinstance(v,list):return [walk(x) for x in v]
        return v
    return walk(value)
