"""Read-only discovery by default. Never equate configuration with readiness."""
import importlib.metadata
import json
import os
import pathlib
import re
import shutil
import sys
import tomllib
from .security import redact
from .mcp import StdioMCP,capabilities
from .providers import HTTPProvider,ProviderError,select_provider

ENV_NAMES=['TYPESAFE_API_KEY','OPENROUTER_API_KEY','JEV_PROVIDER','JEV_MODEL','JEV_MCP_MODEL','TYPESAFE_DEFAULT_MODEL','TYPESAFE_BASE_URL','JEV_OPENROUTER_BASE_URL','JEV_API_KEY','JEV_API_BASE_URL','JEV_MCP_REQUEST_TIMEOUT_MS','JEV_MCP_MAX_ATTEMPTS','JEV_CLOUDFLARE_API_TOKEN','CLOUDFLARE_API_TOKEN','CLOUDFLARE_ACCOUNT_ID','AI_GATEWAY_API_KEY']

def configurations(home=None,cwd=None):
    home=pathlib.Path(home or pathlib.Path.home());cwd=pathlib.Path(cwd or pathlib.Path.cwd())
    files=[('claude-user',home/'.claude.json'),('claude-settings',home/'.claude/settings.json'),('codex-user',home/'.codex/config.toml')]
    for directory in [cwd,*cwd.parents]:
        files += [('claude-project',directory/'.mcp.json'),('codex-project',directory/'.codex/config.toml')]
        if (directory/'.git').exists():break
    servers=[];issues=[];seen=set()
    for source,p in files:
        if p in seen or not p.exists():continue
        seen.add(p)
        try:
            data=tomllib.loads(p.read_text()) if p.suffix=='.toml' else json.loads(p.read_text())
            groups=[data.get('mcp_servers',data.get('mcpServers',{}))]
            # Only active Claude project configuration, not unrelated historical projects.
            project=data.get('projects',{}).get(str(cwd),{})
            if project:groups.append(project.get('mcpServers',{}))
            for group in groups:
                if isinstance(group,dict):
                    for name,config in group.items():
                        if isinstance(config,dict):servers.append({'name':name,'source':source,'config':config})
        except (OSError,ValueError):issues.append({'source':source,'status':'unreadable_or_invalid'})
    return servers,issues

def public_server(row):
    c=row['config'];fingerprint=' '.join([row['name'],str(c.get('command','')),str(c.get('args',[]))])
    return {'name':row['name'],'source':row['source'],'transport':'stdio' if c.get('command') else 'remote',
            'jev_name_hint':bool(re.search('jev|typesafe',fingerprint,re.I)),
            'credential_status':{k:'configured' if v else 'missing' for k,v in c.get('env',{}).items() if k in ENV_NAMES},
            'server_started':'not_tested','tools_discovered':'not_tested','live_inference':'not_tested'}

def configured_billing(rows):
    found=set()
    for row in rows:
        if not public_server(row)['jev_name_hint']:continue
        e=row['config'].get('env',{})
        if e.get('JEV_PROVIDER') in ('typesafe','openrouter'):found.add(e['JEV_PROVIDER'])
        elif e.get('TYPESAFE_API_KEY'):found.add('typesafe')
        elif e.get('OPENROUTER_API_KEY'):found.add('openrouter')
    if len(found)>1:raise ProviderError('Multiple configured MCP billing providers; select provider explicitly')
    return next(iter(found),None)

def npm_packages(home=None,cwd=None):
    home=pathlib.Path(home or pathlib.Path.home());cwd=pathlib.Path(cwd or pathlib.Path.cwd());found=[]
    roots=[cwd/'node_modules',home/'.npm-global/lib/node_modules']
    # Read package metadata; do not install packages or run npx during inventory.
    roots+=list((home/'.npm/_npx').glob('*/node_modules'))
    node=shutil.which('node')
    if node:roots.append(pathlib.Path(node).resolve().parents[1]/'lib/node_modules')
    for root in roots:
        for name in ('@typesafe-ai/sdk','@jkudish/jev-mcp','typesafe-mcp','jev-mcp'):
            p=root/name/'package.json'
            if p.exists():
                try:
                    d=json.loads(p.read_text());record={'name':d.get('name',name),'version':d.get('version'),'scope':'local_or_cached'}
                    if record not in found:found.append(record)
                except (OSError,ValueError):pass
    return found

def doctor(*,probe_mcp=None,discover_models=False,provider=None,model=None,agent_tools=None):
    rows,issues=configurations();mcp=[public_server(r) for r in rows]
    env_status={k:'configured' if os.environ.get(k) else 'missing' for k in ENV_NAMES}
    packages=npm_packages();py=[]
    for n in ('typesafe-sdk','mcp'):
        try:py.append({'name':n,'version':importlib.metadata.version(n)})
        except importlib.metadata.PackageNotFoundError:pass
    report={'agent':'Codex' if os.environ.get('CODEX_HOME') or os.environ.get('CODEX_THREAD_ID') else 'Claude Code' if os.environ.get('CLAUDECODE') else 'Unknown',
            'environment':env_status,'mcp':mcp,'agent_tools':[capabilities(t) for t in agent_tools or []],
            'sdk':{'python':py,'javascript':packages},'executables':{n:'available' if shutil.which(n) else 'missing' for n in ('jev-mcp','typesafe-mcp','node','uv')},
            'config_issues':issues,'provider':None,'model':{'configured_alias':None,'resolved_actual_model':None},'status':'PARTIAL','live_inference':'not_tested'}
    connected=False
    if probe_mcp:
        matches=[(i,r) for i,r in enumerate(rows) if r['name']==probe_mcp]
        if len(matches)!=1:raise ProviderError('MCP name missing or ambiguous; choose an unambiguous configuration')
        i,row=matches[0]
        try:
            with StdioMCP(row['config']) as client:
                info=client.metadata.get('serverInfo',{});listed=client.tools()
                mcp[i].update(server_started='PASS',tools_discovered='PASS',implementation=info.get('name'),client_version=info.get('version'),tools=[capabilities(t) for t in listed])
                connected=any(t['semantic_candidate'] for t in mcp[i]['tools'])
        except ProviderError as e:mcp[i]['probe_error']=str(e)
    try:
        env=dict(os.environ)
        if provider:env['JEV_PROVIDER']=provider
        billing=configured_billing(rows) if env.get('JEV_PROVIDER','auto') in ('auto','') else env.get('JEV_PROVIDER')
        selected=select_provider(env,mcp_available=connected or any(t['semantic_candidate'] for t in report['agent_tools']),configured_provider=billing)
        report['provider']=selected;report['configured_billing_provider']=billing
        report['model']['configured_alias']=model or env.get('JEV_MODEL') or env.get('JEV_MCP_MODEL') or env.get('TYPESAFE_DEFAULT_MODEL')
        if discover_models and selected in ('typesafe','openrouter'):
            client=HTTPProvider(selected,env);requested,pinned=client.resolve_model(model)
            report['model'].update(configured_alias=requested,discovery='PASS',pinned_request=pinned)
        elif discover_models:report['model']['discovery']='Use host MCP model discovery or explicit same-billing HTTP provider'
    except (ProviderError,ValueError) as e:report['selection_error']=str(e)
    if not report['provider'] and not any(m['jev_name_hint'] for m in mcp):report['status']='NOT READY'
    # Inventory and model discovery alone never claim READY. Live verifier owns that status.
    return redact(report)
