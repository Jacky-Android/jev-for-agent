"""Static checks only; these functions never perform semantic inference."""
import json
import math
import re

class ValidationError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise ValidationError(message)

def load_json(text):
    def pairs(entries):
        result = {}
        for key, value in entries:
            require(key not in result, 'Duplicate JSON key (value suppressed)')
            result[key] = value
        return result
    def constant(_):
        raise ValidationError('Non-finite JSON number')
    try:
        return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    except (json.JSONDecodeError, UnicodeError):
        raise ValidationError('Invalid JSON (input suppressed)') from None

def meaningful(value):
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return bool(value) and any(meaningful(v) for v in value.values())
    if isinstance(value, list):
        return bool(value) and any(meaningful(v) for v in value)
    return False

def validate_packet(packet):
    require(isinstance(packet, dict), 'Packet must be an object')
    require(set(packet) <= {'state','questions','model'}, 'Unknown packet field; keep plan/policy outside wire packet')
    state=packet.get('state')
    require((isinstance(state,str) and bool(state.strip())) or (isinstance(state,(dict,list)) and bool(state)), 'Nonempty string/object/array state required')
    try:
        encoded = json.dumps(packet, allow_nan=False)
    except (ValueError, TypeError):
        raise ValidationError('Packet is not finite JSON') from None
    require(len(encoded.encode()) <= 1_000_000, 'Local one-megabyte request safety limit exceeded (not a token count)')
    if 'model' in packet:
        require(isinstance(packet['model'], str) and bool(packet['model'].strip()), 'Invalid model')
    qs = packet.get('questions')
    require(isinstance(qs, dict) and bool(qs), 'Questions must be a nonempty map')
    warnings = []
    for qid, q in qs.items():
        require(isinstance(qid, str) and bool(qid.strip()), 'Nonempty question ID required')
        require(isinstance(q, dict), 'Question must be an object')
        require(set(q) <= {'type','instructions','criteria'}, 'Unknown question field; dependencies need separate requests')
        t = q.get('type')
        require(t in ('choice','score','noul'), 'Primitive must be choice, score or noul')
        require(meaningful(q.get('instructions')), 'Complete nonempty instructions required')
        c = q.get('criteria')
        if t == 'choice':
            require(isinstance(c, dict) and 1 <= len(c) <= 255, 'Choice requires 1..255 options')
            require(all(isinstance(k,str) and k.strip() for k in c), 'Invalid Choice key')
            require(all(meaningful(v) for v in c.values()), 'Skill policy requires explicit option meanings, even though API permits null')
            vals = [json.dumps(v, sort_keys=True, ensure_ascii=False).strip().casefold() for v in c.values()]
            require(len(set(vals)) == len(vals), 'Duplicate Choice descriptions')
            if len(c) == 1:
                warnings.append('One-option Choice provides no discrimination')
            if not set(c) & {'other','none','needs_review','unknown'}:
                warnings.append('Confirm candidate coverage or add an escape option')
        elif t == 'score':
            require(isinstance(c,list) and 2 <= len(c) <= 10, 'Score requires 2..10 ordered levels')
            require(all(meaningful(v) for v in c), 'Each Score level needs an independent description')
            require(len(set(json.dumps(v,sort_keys=True).casefold() for v in c)) == len(c), 'Duplicate Score levels')
        elif c is not None:
            require(isinstance(c,dict) and bool(c) and set(c) <= {'true','false'}, 'Noul criteria accepts true/false only')
            require(all(meaningful(v) for v in c.values()), 'Empty Noul criterion')
        instructions = json.dumps(q.get('instructions'),ensure_ascii=False)
        if re.search(r'(according to|based on).{0,25}(Q\d+.{0,10}answer|answer to)|根据\s*Q\d+\s*的?(答案|结果)',instructions,re.I):
            warnings.append('Possible within-request answer dependency; agent must inspect before calling')
    return warnings

def number(x, lo=0, hi=1):
    return type(x) in (int,float) and math.isfinite(x) and lo <= x <= hi

def validate_answers(packet, answers):
    require(isinstance(answers,dict) and set(answers) == set(packet['questions']), 'Response question IDs mismatch')
    for qid,q in packet['questions'].items():
        a = answers[qid]
        require(isinstance(a,dict) and a.get('type') == q['type'], 'Response primitive mismatch')
        if q['type'] == 'noul':
            require(number(a.get('noul')), 'Noul must be finite probability in [0,1]')
            require('confidence' not in a, 'Noul has no native confidence; wrapper certainty must be separately labeled')
            continue
        p = a.get('probabilities')
        keys = set(q['criteria']) if q['type']=='choice' else {str(i) for i in range(len(q['criteria']))}
        require(isinstance(p,dict) and set(p)==keys, 'Probability keys mismatch')
        require(all(number(v) for v in p.values()), 'Invalid probability')
        require(abs(sum(p.values())-1) <= .025, 'Probabilities do not sum approximately to one')
        if 'confidence' in a:
            require(number(a['confidence']), 'Invalid confidence')
        if q['type']=='choice':
            require(a.get('choice') in keys, 'Choice outside criteria')
            require(p[a['choice']] + .011 >= max(p.values()), 'Choice is not a highest-probability option')
        else:
            require(number(a.get('score'),0,len(keys)-1), 'Score outside rubric range')
            legend = a.get('legend')
            require(isinstance(legend,dict) and set(legend)==keys, 'Score legend missing or misaligned')
            for i,desc in enumerate(q['criteria']):
                # Some providers serialize structured descriptions into JSON strings.
                actual=legend[str(i)]
                if not isinstance(desc,str) and isinstance(actual,str):
                    try: actual=load_json(actual)
                    except ValidationError: pass
                require(actual==desc, 'Score legend differs from requested rubric')
            expected=sum(int(k)*v for k,v in p.items())
            require(abs(a['score']-expected) <= .03*len(keys), 'Score inconsistent with rounded probabilities')
    return True
