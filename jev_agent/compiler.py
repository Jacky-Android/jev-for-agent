from .validation import require,validate_packet,meaningful
from .security import assert_no_secrets

def compile_plan(plan):
    require(isinstance(plan,dict),'Plan must be an object')
    for key in ('goal','inputs','constraints','candidate_actions','risk','required_output'):
        require(key in plan,'Plan is missing a required goal/context field')
    require(meaningful(plan['goal']),'Goal must be meaningful')
    steps=plan.get('steps');require(isinstance(steps,list) and bool(steps),'Plan needs steps')
    qs={}
    for step in steps:
        require(isinstance(step,dict),'Invalid plan step')
        kind=step.get('kind');require(kind in ('semantic_judgment','deterministic_code','generative_work','tool_execution'),'Unknown step kind')
        if kind!='semantic_judgment':
            require('question' not in step,'Nonsemantic steps cannot carry Jev questions');continue
        require(not step.get('depends_on_answers'),'Split answer-dependent questions into a later packet')
        qid=step.get('id');require(isinstance(qid,str) and qid and qid not in qs,'Missing or duplicate question ID')
        qs[qid]=step.get('question')
    require(bool(qs),'No semantic judgment required: continue with Agent/Code, no Jev call')
    packet={'state':plan.get('state'),'questions':qs}
    validate_packet(packet);assert_no_secrets(packet)
    return packet
