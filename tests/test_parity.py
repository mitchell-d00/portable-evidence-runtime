"""Exercise both independent verifiers on the same boundary and mutation corpus."""
import copy
import json
import subprocess
import unittest

from test_reference import SAMPLE, PIN
from per import answer, build_capsule, root_hash


class CrossLanguageTests(unittest.TestCase):
    def test_shared_boundary_corpus(self):
        cases = []
        for value in ['line\n\t\x00"\\', 'é e\u0301 🌎', '🌎' * 10000]:
            bodies = [copy.deepcopy(SAMPLE['records'][0]['body'])]
            bodies[0]['value'] = value
            capsule = build_capsule(bodies)
            cases.append((capsule, bodies[0]['key'], capsule['root_sha256']))
        for field, value in [('revision', 9007199254740992),
                             ('revision', True), ('value', '\ud800'),
                             ('value', '🌎' * 10001), ('id', 'ABC\n'),
                             ('key', 'lab-rule\n'), ('origin', ['human'])]:
            c = copy.deepcopy(SAMPLE)
            c['records'][0]['body'][field] = value
            cases.append((c, 'lab-rule', PIN))
        c = copy.deepcopy(SAMPLE)
        c['policy'] = dict(reversed(list(c['policy'].items())))
        c['root_sha256'] = root_hash(c)
        cases.append((c, 'lab-rule', c['root_sha256']))
        cases.extend([(SAMPLE, 'lab-rule\n', PIN), (None, 'lab-rule', PIN),
                      (SAMPLE, 'lab-rule', '0' * 64)])
        script = """
const fs=require('node:fs'),vm=require('node:vm');
const ctx={TextEncoder};
vm.runInNewContext(fs.readFileSync('web/source_runtime.js','utf8'),ctx);
const cases=JSON.parse(fs.readFileSync(0,'utf8'));
console.log(JSON.stringify(cases.map(c=>ctx.PER.answer(...c))));
"""
        from test_reference import ROOT
        result = subprocess.run(['node', '-e', script], cwd=ROOT,
                                input=json.dumps(cases), text=True,
                                capture_output=True, check=True)
        for case, js in zip(cases, json.loads(result.stdout)):
            with self.subTest(key=case[1], status=js['status']):
                py = answer(*case)
                self.assertEqual(py['status'], js['status'])
                self.assertEqual(py['answer_supported'], js['answer_supported'])
                if py['answer_supported']:
                    self.assertEqual(py['answer'], js['answer'])
                    self.assertEqual(py['evidence'], js['evidence'])
