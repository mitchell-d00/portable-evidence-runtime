"""Offline consistency checks for packaged browser artifacts and fixed capsule.

Not a publisher signature or source-truth verification.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'src'))
from per import verify_capsule

def run():
    checks={}
    c=json.loads((R/'experiment/fixtures/demo_capsule.json').read_text(encoding='utf-8'))
    root=(R/'experiment/fixtures/demo_root.sha256').read_text().strip()
    checks['fixture_matches_pin']=verify_capsule(c,root)['root_sha256']==root
    checks['authoring_build_in_sync']=subprocess.run([sys.executable,str(R/'tools/build.py'),'--check'],cwd=R,capture_output=True,text=True).returncode==0
    checks['strict_build_in_sync']=subprocess.run([sys.executable,str(R/'scripts/build_web.py'),'--check'],cwd=R,capture_output=True,text=True).returncode==0
    generated=(R/'web/index.html').read_text(encoding='utf-8')
    checks['strict_html_contains_pin']=root in generated
    checks['strict_html_has_embedded_capsule']='id="embedded-capsule"' in generated
    checks['strict_html_has_no_remote_script']=not any(s in generated for s in ('<script src=',"fetch(",'<link href="https:'))
    checks['paper_formats_exist']=all((R/'paper'/('Portable_Evidence_Runtime.'+ext)).exists() for ext in ('md','txt','pdf'))
    checks['paper_pdf_valid']=(R/'paper/Portable_Evidence_Runtime.pdf').read_bytes().startswith(b'%PDF')
    checks['legacy_paper_matches_core']=all((R/'paper'/('Portable_Evidence_Runtime.'+ext)).read_bytes()==(R/'core-papers'/('Portable_Evidence_Runtime.'+ext)).read_bytes() for ext in ('md','txt','pdf'))
    checks['review_formats_exist']=all((R/'core-papers'/('Validation_and_Publication_Review.'+ext)).exists() for ext in ('md','txt','pdf'))
    checks['review_pdf_valid']=(R/'core-papers/Validation_and_Publication_Review.pdf').read_bytes().startswith(b'%PDF')
    for name in ('synthetic_run','browser_offline_probe'):
        report=json.loads((R/'experiment/results'/f'{name}.json').read_text())
        checks[name+'_passed']=report['all_passed'] and report['n_cases']==len(report['cases']) and all(case['pass'] for case in report['cases'])
    for k,v in checks.items():print(('PASS' if v else 'FAIL')+' '+k)
    return 0 if all(checks.values()) else 1

if __name__=='__main__':raise SystemExit(run())
