"""Reference verification and answer implementation.

The hashes are *integrity checks*, NOT signatures, authenticity, or proof of truth.
The independently pinned expected-root option is needed to detect replacement of
an entire internally consistent capsule. Every sample statement is synthetic.
"""
from __future__ import annotations
import hashlib
import json
import re
from typing import Any

FORMAT = 'portable-evidence-capsule/1'
DEFAULT_POLICY = {
    'answer_mode': 'exact-key',
    'allowed_status': ['current'],
    'allowed_origin': ['human'],
    'ambiguous': 'refuse',
}
FIELDS = ('id','key','value','status','origin','revision','supersedes')
STATUS = {'current','retired','blocked'}
ORIGIN = {'human','machine','imported'}

class CapsuleError(ValueError):
    """The capsule cannot be used safely."""


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(',',':'), allow_nan=False)


def digest(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode('utf-8')).hexdigest()


def check_body(body: Any) -> dict:
    if not isinstance(body, dict) or set(body) != set(FIELDS):
        raise CapsuleError('record body must have exactly seven declared fields')
    if list(body) != list(FIELDS):
        raise CapsuleError('record fields must follow the canonical order')
    if not isinstance(body['id'], str) or not re.fullmatch(r'[A-Z0-9_-]{3,80}', body['id']):
        raise CapsuleError('invalid record ID')
    if not isinstance(body['key'], str) or not re.fullmatch(r'[a-z0-9-]{2,80}', body['key']):
        raise CapsuleError('invalid exact lookup key')
    if not isinstance(body['value'], str) or not (1 <= len(body['value']) <= 10000):
        raise CapsuleError('invalid value')
    if (not isinstance(body['status'], str) or not isinstance(body['origin'], str) or
        body['status'] not in STATUS or body['origin'] not in ORIGIN):
        raise CapsuleError('invalid status or origin')
    if any(0xD800 <= ord(ch) <= 0xDFFF for ch in body['value']):
        raise CapsuleError('value must contain Unicode scalar values')
    if type(body['revision']) is not int or not 1 <= body['revision'] <= 9007199254740991:
        raise CapsuleError('revision must be a positive JavaScript-safe integer')
    if body['supersedes'] is not None and (not isinstance(body['supersedes'], str) or
        not re.fullmatch(r'[A-Z0-9_-]{3,80}', body['supersedes'])):
        raise CapsuleError('invalid supersedes pointer')
    return body


def record_hash(body: dict) -> str:
    return digest(check_body(body))


def _root_material(capsule: dict) -> dict:
    return {
        'format': capsule['format'],
        'policy': capsule['policy'],
        'records': [{'id':record['body']['id'],'sha256':record['sha256']}
                    for record in capsule['records']],
    }


def root_hash(capsule: dict) -> str:
    return digest(_root_material(capsule))


def build_capsule(bodies: list[dict]) -> dict:
    if not isinstance(bodies, list) or not bodies:
        raise CapsuleError('at least one record is required')
    bodies = sorted((dict(check_body(body)) for body in bodies), key=lambda b:b['id'])
    capsule = {'format': FORMAT, 'policy': dict(DEFAULT_POLICY),
               'records': [{'body': b, 'sha256':record_hash(b)} for b in bodies]}
    capsule['root_sha256'] = root_hash(capsule)
    verify_capsule(capsule)
    return capsule


def verify_capsule(capsule: Any, expected_root: str | None = None) -> dict:
    if not isinstance(capsule, dict) or list(capsule) != ['format','policy','records','root_sha256']:
        raise CapsuleError('invalid capsule envelope or field order')
    if (capsule['format'] != FORMAT or capsule['policy'] != DEFAULT_POLICY or
        list(capsule['policy']) != list(DEFAULT_POLICY)):
        raise CapsuleError('unsupported format or changed fixed policy')
    records = capsule['records']
    if not isinstance(records, list) or not (1 <= len(records) <= 10000):
        raise CapsuleError('capsule must have 1 to 10000 records')
    ids = []
    indexed = {}
    for rec in records:
        if not isinstance(rec, dict) or list(rec) != ['body','sha256']:
            raise CapsuleError('malformed record wrapper')
        body = check_body(rec['body'])
        actual = record_hash(body)
        if rec['sha256'] != actual:
            raise CapsuleError('record hash mismatch: '+body['id'])
        ids.append(body['id'])
        indexed[body['id']] = body
    if ids != sorted(set(ids)):
        raise CapsuleError('duplicate or unsorted record identifiers')
    for body in indexed.values():
        predecessor_id = body['supersedes']
        if predecessor_id is None:
            continue
        predecessor = indexed.get(predecessor_id)
        if not predecessor or predecessor['key'] != body['key'] or predecessor['revision'] >= body['revision']:
            raise CapsuleError('invalid revision lineage: '+body['id'])
    calculated = root_hash(capsule)
    if capsule['root_sha256'] != calculated:
        raise CapsuleError('capsule root mismatch')
    if expected_root is not None and calculated != expected_root:
        raise CapsuleError('capsule does not match separately pinned expected root')
    return {'ok':True,'record_count':len(records),'root_sha256':calculated,
            'trust':'self-consistent, not authenticated' if expected_root is None
                    else 'matches supplied expected root, subject to anchor trust'}


def answer(capsule: dict, key: str, expected_root: str | None = None) -> dict:
    try:
        report = verify_capsule(capsule, expected_root)
    except CapsuleError as exc:
        return {'status':'integrity_error','answer_supported':False,'reason':str(exc)}
    if not isinstance(key, str) or not re.fullmatch(r'[a-z0-9-]{2,80}', key):
        return {'status':'invalid_key','answer_supported':False,
                'reason':'enter a literal exact lookup key, not natural language'}
    eligible = [r for r in capsule['records'] if
        r['body']['key'] == key and
        r['body']['status'] in capsule['policy']['allowed_status'] and
        r['body']['origin'] in capsule['policy']['allowed_origin']]
    if len(eligible) > 1:
        return {'status':'ambiguous','answer_supported':False,
                'reason':'more than one eligible current owner','owner_count':len(eligible)}
    if not eligible:
        return {'status':'not_in_corpus','answer_supported':False,
                'reason':'no eligible current human-authored record for exact key'}
    record = eligible[0]
    body = record['body']
    return {'status':'supported','answer_supported':True,'answer':body['value'],
            'evidence':{'id':body['id'],'key':body['key'],
                        'revision':body['revision'],'sha256':record['sha256'],
                        'root_sha256':report['root_sha256']}}
