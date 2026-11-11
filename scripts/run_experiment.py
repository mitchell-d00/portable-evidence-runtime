"""Run a declared deterministic experiment and record actual results.

No claim of independent external validation is made. All inputs are synthetic.
"""
import copy
import datetime
import hashlib
import json
import os
import platform
import sys
import shutil
import tempfile
from pathlib import Path

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'src'))
from per import answer,record_hash,root_hash,verify_capsule

CAPSULE=json.loads((R/'experiment/fixtures/demo_capsule.json').read_text(encoding='utf-8'))
PIN=(R/'experiment/fixtures/demo_root.sha256').read_text(encoding='utf-8').strip()

CASES = [
 ('valid_pinned', 'verification', True),
 ('exact_source', 'supported', True),
 ('retired_excluded', 'supported', True),
 ('machine_excluded', 'not_in_corpus', False),
 ('blocked_excluded', 'not_in_corpus', False),
 ('ambiguous_refused', 'ambiguous', False),
 ('unknown_refused', 'not_in_corpus', False),
 ('paraphrase_refused', 'invalid_key', False),
 ('value_corruption_refused', 'integrity_error', False),
 ('status_corruption_refused', 'integrity_error', False),
 ('policy_corruption_refused', 'integrity_error', False),
 ('root_corruption_refused', 'integrity_error', False),
 ('relocated_capsule', 'supported', True),
 ('rehashed_substitution_pin_refused', 'integrity_error', False),
 ('missing_all_bytes_refused', 'integrity_error', False),
]

def run():
    out=[]
    for case,expected,expected_support in CASES:
        c=copy.deepcopy(CAPSULE)
        if case=='valid_pinned':
            r={'status':'verification','answer_supported':True} if verify_capsule(c,PIN)['ok'] else {'status':'integrity_error','answer_supported':False}
        else:
            key={'retired_excluded':'kiln-schedule','machine_excluded':'machine-claim',
                 'blocked_excluded':'blocked-note','ambiguous_refused':'conflicting-answer',
                 'unknown_refused':'unseen-key','paraphrase_refused':'what is the kiln schedule?'
                }.get(case,'kiln-schedule')
            if case=='value_corruption_refused':c['records'][4]['body']['value']='wrong'
            if case=='status_corruption_refused':c['records'][4]['body']['status']='blocked'
            if case=='policy_corruption_refused':c['policy']['answer_mode']='free-text'
            if case=='root_corruption_refused':c['root_sha256']='0'*64
            if case=='rehashed_substitution_pin_refused':
                c['records'][4]['body']['value']='rewritten';c['records'][4]['sha256']=record_hash(c['records'][4]['body']);c['root_sha256']=root_hash(c)
            if case=='missing_all_bytes_refused':c['records']=[];c['root_sha256']=root_hash(c)
            if case=='relocated_capsule':
                with tempfile.TemporaryDirectory() as directory:
                    target=Path(directory)/'transferred.json'
                    shutil.copyfile(R/'experiment/fixtures/demo_capsule.json',target)
                    c=json.loads(target.read_text(encoding='utf-8'))
            r=answer(c,key,PIN)
        passed=(r['status']==expected and r['answer_supported']==expected_support)
        if case in ('exact_source','retired_excluded','relocated_capsule'):
            expected_record=next(x for x in CAPSULE['records'] if x['body']['id']=='KILN-001')
            passed=passed and r.get('answer')==expected_record['body']['value'] and r.get('evidence',{}).get('revision')==2
        out.append({'case':case,'expected_status':expected,'observed_status':r['status'],
                    'expected_support':expected_support,'observed_support':r['answer_supported'],
                    'pass':passed})
    result={
        'experiment_id':'PER-SYNTHETIC-001',
        'run_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
        'python':platform.python_version(),
        'platform':platform.platform(),
        'fixture_sha256':hashlib.sha256((R/'experiment/fixtures/demo_capsule.json').read_bytes()).hexdigest(),
        'pinned_capsule_root_sha256':PIN,
        'condition':'local self-contained exact-key capsule; deterministic synthetic scenarios',
        'validation_type':'engineering feasibility, not external/clinical/scientific superiority test',
        'n_cases':len(out),'n_passed':sum(x['pass'] for x in out),'all_passed':all(x['pass'] for x in out),
        'cases':out,
    }
    dest=R/'experiment/results/synthetic_run.json'
    dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'result':str(dest.relative_to(R)),'passes':result['n_passed'],'cases':len(out),'all_passed':result['all_passed']},indent=2))
    return 0 if result['all_passed'] else 1

if __name__=='__main__':raise SystemExit(run())
