"""CLI. Run with PYTHONPATH=src python -m per verify|ask|build ..."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from .core import CapsuleError, answer, build_capsule, verify_capsule


def main() -> int:
    p = argparse.ArgumentParser(description='Portable Evidence Runtime')
    sub = p.add_subparsers(dest='action',required=True)
    v = sub.add_parser('verify', help='check integrity (and optionally a pinned root)')
    v.add_argument('capsule'); v.add_argument('--expected-root')
    a = sub.add_parser('ask', help='exact-key query; no semantic paraphrases')
    a.add_argument('capsule'); a.add_argument('key'); a.add_argument('--expected-root')
    b = sub.add_parser('build', help='build sealed capsule from honest source records')
    b.add_argument('source'); b.add_argument('output')
    args = p.parse_args()
    try:
        data = json.loads(Path(args.source if args.action=='build' else args.capsule).read_text(encoding='utf-8'))
        if args.action == 'build':
            result = build_capsule(data)
            Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            result = verify_capsule(result)
        elif args.action=='verify':
            result = verify_capsule(data,args.expected_root)
        else:
            result = answer(data,args.key,args.expected_root)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0 if result.get('status') not in ('integrity_error','invalid_key') else 2
    except (CapsuleError, json.JSONDecodeError, UnicodeError, OSError) as exc:
        print(json.dumps({'ok':False,'error':str(exc)}),file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
