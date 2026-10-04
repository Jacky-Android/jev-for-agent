"""Session-scoped provider reuse; configuration scans happen once per session."""
import os
from .doctor import configurations,configured_billing,public_server
from .providers import HTTPProvider,ExistingMCP,ProviderError,select_provider
from .mcp import StdioMCP,capabilities

class Session:
    def __init__(self,provider=None,model=None,mcp_name=None):
        self.model=model;self.mcp=None
        rows,_=configurations();env=dict(os.environ)
        if provider:env['JEV_PROVIDER']=provider
        candidates=[r for r in rows if public_server(r)['jev_name_hint']]
        if mcp_name:candidates=[r for r in rows if r['name']==mcp_name]
        # Known config is a hint, not an already-connected MCP. Auto still gives it
        # a chance, but never crosses billing providers after a failed connection.
        explicit=env.get('JEV_PROVIDER','auto')
        use_mcp=explicit=='mcp' or (explicit in ('auto','') and bool(candidates))
        if use_mcp:
            if len(candidates)!=1:raise ProviderError('MCP configuration absent or ambiguous; select an explicit provider/name')
            self.mcp=StdioMCP(candidates[0]['config'])
            try:
                self.mcp.__enter__();listed=self.mcp.tools()
                generic=[t for t in listed if capabilities(t)['generic_state_questions']]
                if len(generic)!=1:
                    raise ProviderError('Connected MCP exposes no unique generic state/questions tool. Use its specialized host tools, or explicitly select the same billing provider for custom primitives')
                self.adapter=ExistingMCP(self.mcp.call,generic[0],configured_billing(candidates));self.provider='mcp'
            except Exception:
                self.close();raise
        else:
            billing=configured_billing(rows) if explicit in ('auto','') else None
            self.provider=select_provider(env,configured_provider=billing)
            self.adapter=HTTPProvider(self.provider,env)
            self.adapter.resolve_model(model)  # discovery once, cached for this session
    def evaluate(self,state,questions,model=None):return self.adapter.evaluate(state,questions,model or self.model)
    def close(self):
        if self.mcp:self.mcp.close();self.mcp=None
    def __enter__(self):return self
    def __exit__(self,*_):self.close()
