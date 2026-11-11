import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from per import CapsuleError, answer, build_capsule, verify_capsule, root_hash, record_hash

SAMPLE=json.loads((ROOT/'experiment/fixtures/demo_capsule.json').read_text(encoding='utf-8'))
PIN=(ROOT/'experiment/fixtures/demo_root.sha256').read_text(encoding='utf-8').strip()

class OfflineCapsuleTests(unittest.TestCase):
    def fresh(self): return copy.deepcopy(SAMPLE)
    def test_01_pinned_root(self):
        self.assertEqual(PIN,verify_capsule(SAMPLE,PIN)['root_sha256'])
    def test_02_self_consistent_no_authentication_claim(self):
        self.assertIn('not authenticated',verify_capsule(SAMPLE)['trust'])
    def test_03_exact_key_supported(self):
        r=answer(SAMPLE,'kiln-schedule',PIN)
        self.assertEqual(r['status'],'supported');self.assertEqual(r['evidence']['id'],'KILN-001')
    def test_04_evidence_sha_is_record_digest(self):
        r=answer(SAMPLE,'kiln-schedule'); self.assertEqual(r['evidence']['sha256'],
            next(x['sha256'] for x in SAMPLE['records'] if x['body']['id']=='KILN-001'))
    def test_05_retired_never_owns(self):
        self.assertEqual(answer(SAMPLE,'kiln-schedule')['evidence']['revision'],2)
    def test_06_machine_origin_refused(self):
        self.assertEqual(answer(SAMPLE,'machine-claim')['status'],'not_in_corpus')
    def test_07_blocked_refused(self):
        self.assertEqual(answer(SAMPLE,'blocked-note')['status'],'not_in_corpus')
    def test_08_conflict_refused(self):
        self.assertEqual(answer(SAMPLE,'conflicting-answer')['status'],'ambiguous')
    def test_09_missing_refused(self):
        self.assertEqual(answer(SAMPLE,'nonexistent')['status'],'not_in_corpus')
    def test_10_natural_language_refused(self):
        self.assertEqual(answer(SAMPLE,'what is the kiln schedule?')['status'],'invalid_key')
    def test_11_content_tamper_fails_closed(self):
        c=self.fresh();c['records'][4]['body']['value']='Bad';
        self.assertEqual(answer(c,'kiln-schedule')['status'],'integrity_error')
    def test_12_metadata_tamper_fails_closed(self):
        c=self.fresh();c['records'][6]['body']['status']='current';
        self.assertEqual(answer(c,'kiln-schedule')['status'],'integrity_error')
    def test_13_policy_tamper_fails_closed(self):
        c=self.fresh();c['policy']['allowed_origin']=['machine'];
        self.assertEqual(answer(c,'kiln-schedule')['status'],'integrity_error')
    def test_14_root_tamper_fails_closed(self):
        c=self.fresh();c['root_sha256']='0'*64;
        self.assertEqual(answer(c,'kiln-schedule')['status'],'integrity_error')
    def test_15_duplicate_id_fails_closed(self):
        c=self.fresh();c['records'].append(copy.deepcopy(c['records'][-1]));
        self.assertEqual(answer(c,'kiln-schedule')['status'],'integrity_error')
    def test_16_missing_parent_fails_closed(self):
        c=self.fresh();c['records'][4]['body']['supersedes']='MISSING';
        c['records'][4]['sha256']=record_hash(c['records'][4]['body']);c['root_sha256']=root_hash(c)
        self.assertEqual(answer(c,'kiln-schedule')['status'],'integrity_error')
    def test_17_full_rewrite_is_self_consistent_but_pinned_failure(self):
        c=self.fresh();c['records'][4]['body']['value']='Attacker substitute';
        c['records'][4]['sha256']=record_hash(c['records'][4]['body']);c['root_sha256']=root_hash(c)
        self.assertTrue(verify_capsule(c)['ok'])
        self.assertEqual(answer(c,'kiln-schedule',PIN)['status'],'integrity_error')
    def test_18_reconstruction_from_disk_copy(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'different_dir'/'archive.json';path.parent.mkdir()
            path.write_text(json.dumps(SAMPLE,ensure_ascii=False),encoding='utf-8')
            c=json.loads(path.read_text(encoding='utf-8'))
            self.assertTrue(verify_capsule(c,PIN)['ok'])
            self.assertEqual(answer(c,'lab-rule')['status'],'supported')
    def test_19_only_actual_sources_can_build(self):
        c=build_capsule([x['body'] for x in SAMPLE['records']]);self.assertEqual(c,SAMPLE)
    def test_20_bad_field_order_rejected(self):
        c=self.fresh();c['records'][0]['body']={'value':'x',**c['records'][0]['body']}
        self.assertEqual(answer(c,'lab-rule')['status'],'integrity_error')
    def test_21_wrong_origin_type_rejected(self):
        c=self.fresh();c['records'][0]['body']['origin']=['human'];
        self.assertEqual(answer(c,'lab-rule')['status'],'integrity_error')
    def test_22_unsorted_refused(self):
        c=self.fresh();c['records'].reverse();c['root_sha256']=root_hash(c)
        self.assertEqual(answer(c,'lab-rule')['status'],'integrity_error')
    def test_23_missing_content_always_refuses(self):
        c=self.fresh();c['records']=[];c['root_sha256']=root_hash(c)
        self.assertEqual(answer(c,'lab-rule')['status'],'integrity_error')
    def test_24_untrusted_pin_refused(self):
        self.assertEqual(answer(SAMPLE,'lab-rule','9'*64)['status'],'integrity_error')
    def test_25_json_roundtrip_stability(self):
        c=json.loads(json.dumps(SAMPLE,ensure_ascii=False));self.assertEqual(verify_capsule(c)['root_sha256'],PIN)

if __name__=='__main__':unittest.main()
