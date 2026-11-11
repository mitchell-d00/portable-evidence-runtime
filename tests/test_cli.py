import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_reference import ROOT, PIN


class CommandLineTests(unittest.TestCase):
    def cli(self, *args):
        return subprocess.run([sys.executable, '-m', 'per', *map(str, args)],
                              cwd=ROOT, env={**os.environ, 'PYTHONPATH': str(ROOT/'src')},
                              text=True, capture_output=True)

    def test_build_verify_ask(self):
        with tempfile.TemporaryDirectory() as directory:
            capsule = Path(directory)/'rebuilt.json'
            self.assertEqual(self.cli('build', ROOT/'experiment/fixtures/demo_source.json', capsule).returncode, 0)
            proof = self.cli('verify', capsule, '--expected-root', PIN)
            self.assertEqual(proof.returncode, 0)
            self.assertEqual(json.loads(proof.stdout)['root_sha256'], PIN)
            result = self.cli('ask', capsule, 'kiln-schedule', '--expected-root', PIN)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)['evidence']['id'], 'KILN-001')

    def test_refusal_process_results(self):
        capsule = ROOT/'experiment/fixtures/demo_capsule.json'
        for key, pin, code, status in [('kiln-schedule', '0'*64, 2, 'integrity_error'),
                                       ('what kiln?', PIN, 2, 'invalid_key'),
                                       ('unseen-key', PIN, 0, 'not_in_corpus'),
                                       ('conflicting-answer', PIN, 0, 'ambiguous')]:
            with self.subTest(key=key, status=status):
                result = self.cli('ask', capsule, key, '--expected-root', pin)
                self.assertEqual(result.returncode, code)
                self.assertEqual(json.loads(result.stdout)['status'], status)
                self.assertFalse(json.loads(result.stdout)['answer_supported'])

    def test_malformed_files_return_structured_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)/'bad.json'
            for content in (b'[null]', b'[1]', b'{}', b'not json', b'\xff'):
                with self.subTest(content=content):
                    source.write_bytes(content)
                    result = self.cli('build', source, Path(directory)/'output.json')
                    self.assertEqual(result.returncode, 2)
                    self.assertFalse(json.loads(result.stderr)['ok'])
                    self.assertNotIn('Traceback', result.stderr)
