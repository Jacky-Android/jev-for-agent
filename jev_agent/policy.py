"""Example policy, not official thresholds and not authorization enforcement."""
from .validation import number,require

def gate(answer, *, authorized, fresh, evidence_complete, high_risk=False, threshold=.85):
    require(number(threshold,.500001,1),'Threshold must exceed .5 and be <=1')
    if not authorized:return {'route':'abstain','reason':'permission_missing'}
    if not fresh or not evidence_complete:return {'route':'gather_more_evidence','reason':'stale_or_incomplete'}
    if high_risk:return {'route':'review','reason':'high_risk_requires_independent_checks'}
    t=answer.get('type')
    if t=='noul':
        p=answer.get('noul');require(number(p),'Invalid Noul')
        return {'route':'act' if p>=threshold or p<=1-threshold else 'review', 'value':p>=threshold if p>=threshold or p<=1-threshold else None,'noul':p,'derived_certainty':abs(2*p-1),'policy':'example/default'}
    if t not in ('choice','score'):return {'route':'abstain','reason':'unknown_answer_type'}
    if answer.get('choice') in ('other','none','needs_review','unknown'):
        return {'route':'gather_more_evidence','reason':'escape_option'}
    confidence=answer.get('confidence')
    return {'route':'act' if number(confidence) and confidence>=threshold else 'review','value':answer.get('choice',answer.get('score')),'policy':'example/default'}
