"""Optional real-browser file:// offline probe; requires preinstalled Playwright.

The standalone browser applications DO NOT depend on this script or Playwright.
"""
from __future__ import annotations
import datetime
import json
import platform
import shutil
from pathlib import Path

R=Path(__file__).resolve().parents[1]
OUT=R/'experiment/results/browser_offline_probe.json'

def run():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print('Playwright not installed: optional browser probe unavailable')
        return 2
    results=[]
    reqs=[]
    with sync_playwright() as p:
        browser_path=(shutil.which('chromium') or shutil.which('chromium-browser') or shutil.which('google-chrome'))
        launch_kwargs={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
        if browser_path: launch_kwargs['executable_path']=browser_path
        browser=p.chromium.launch(**launch_kwargs)
        context=browser.new_context(offline=True,viewport={'width':1120,'height':850},accept_downloads=True)
        def monitor(request):
            if request.url.startswith(('http:','https:','ws:','wss:')):reqs.append(request.url)
        context.on('request',monitor)
        page=context.new_page()
        errors=[]
        page.on('pageerror',lambda exc:errors.append(str(exc)))
        # Some managed Chromium installs prohibit file:// navigation. In that case test
        # the identical embedded document through in-memory set_content, recording the limitation.
        file_direct=True
        try:
            page.goto((R/'web/index.html').resolve().as_uri(),wait_until='load')
        except Exception as exc:
            if 'ERR_BLOCKED_BY_ADMINISTRATOR' not in str(exc): raise
            file_direct=False
            page.close()
            page=context.new_page()
            page.on('pageerror',lambda exc:errors.append(str(exc)))
            page.set_content((R/'web/index.html').read_text(encoding='utf-8'),wait_until='load')
        page.wait_for_timeout(200)
        state=page.locator('#integrity-status').inner_text()
        supported=page.locator('#answer-output').inner_text()
        results.append({'case':'strict_pinned_valid','pass':state.startswith('ANCHORED:') and supported.startswith('SUPPORTED'), 'state':state,'decision':supported[:150]})
        page.locator('#query').fill('conflicting-answer')
        page.locator('#ask-btn').click()
        ambiguous=page.locator('#answer-output').inner_text()
        results.append({'case':'strict_ambiguous_refusal','pass':ambiguous.startswith('REFUSED') and 'ambiguous' in ambiguous,'decision':ambiguous[:150]})
        page.locator('#query').fill('kiln-schedule')
        page.locator('#anchor').fill('0'*64)
        blocked=page.locator('#answer-output').inner_text()
        results.append({'case':'strict_wrong_root_refusal','pass':blocked.startswith('REFUSED') and 'integrity_error' in blocked,'decision':blocked[:150]})
        page.screenshot(path=str(R/'experiment/results/strict_offline.png'),full_page=True)
        page.locator('#anchor').fill('')
        results.append({'case':'strict_missing_root_refusal','pass':'missing_anchor' in page.locator('#answer-output').inner_text()})
        page.locator('#reset-btn').click()
        page.locator('#import-input').set_input_files({'name':'oversize.json','mimeType':'application/json','buffer':b' ' * 2000001})
        results.append({'case':'strict_oversize_import_clears_answer','pass':page.locator('#answer-output').inner_text().startswith('REFUSED')})
        page.locator('#reset-btn').click()
        with page.expect_download() as event:
            page.locator('#export-btn').click()
        exported=Path(event.value.path()).read_bytes()
        # A fresh context has no cookies or local storage from the first one.
        fresh=browser.new_context(offline=True,accept_downloads=True)
        fresh.on('request',monitor)
        recipient=fresh.new_page()
        recipient.on('pageerror',lambda exc:errors.append(str(exc)))
        if file_direct:
            recipient.goto((R/'web/index.html').resolve().as_uri(),wait_until='load')
        else:
            recipient.set_content((R/'web/index.html').read_text(encoding='utf-8'),wait_until='load')
        recipient.locator('#import-input').set_input_files({'name':'transfer.json','mimeType':'application/json','buffer':exported})
        recipient.wait_for_function("document.getElementById('import-input').value === ''")
        decision=recipient.locator('#answer-output').inner_text()
        results.append({'case':'strict_export_import_fresh_context','pass':decision.startswith('SUPPORTED') and 'KILN-001' in decision})
        substituted=json.loads(exported)
        substituted['records'][0]['body']['value']='altered'
        recipient.locator('#import-input').set_input_files({'name':'tampered.json','mimeType':'application/json','buffer':json.dumps(substituted).encode()})
        recipient.wait_for_function("document.getElementById('import-input').value === ''")
        results.append({'case':'strict_tampered_import_refusal','pass':'integrity_error' in recipient.locator('#answer-output').inner_text()})
        fresh.close()
        if file_direct:
            page.goto((R/'index.html').resolve().as_uri(),wait_until='load')
        else:
            page.set_content((R/'index.html').read_text(encoding='utf-8'),wait_until='load')
        page.wait_for_timeout(200)
        authoring=page.locator('#answer').inner_text()
        results.append({'case':'authoring_demo_local_answer','pass':authoring.startswith('SUPPORTED ANSWER:') and '900 C' in authoring,'decision':authoring[:150]})
        with page.expect_download() as event:
            page.locator('#export').click()
        ledger=json.loads(Path(event.value.path()).read_bytes())
        ledger['records'][0]['facts'][0]['value']='forged'
        page.locator('#import-file').set_input_files({'name':'altered-ledger.json','mimeType':'application/json','buffer':json.dumps(ledger).encode()})
        page.wait_for_function("document.getElementById('import-file').value === ''")
        results.append({'case':'authoring_import_refreshes_answer','pass':page.locator('#answer').inner_text().startswith('REFUSED')})
        page.once('dialog',lambda dialog:dialog.accept())
        page.locator('#reset').click()
        results.append({'case':'authoring_reset_refreshes_answer','pass':page.locator('#answer').inner_text().startswith('SUPPORTED ANSWER:')})
        page.locator('#id').fill('KILN-002')
        page.locator('#title').fill('Synthetic revision')
        page.locator('#facts').fill('Kiln A | maximum temperature | 800 C')
        page.locator('#supersedes').select_option('KILN-001')
        page.locator('#add').click()
        results.append({'case':'authoring_revision_refreshes_answer','pass':page.locator('#answer').inner_text().startswith('SUPPORTED ANSWER: 800 C')})
        page.screenshot(path=str(R/'experiment/results/authoring_offline.png'),full_page=True)
        browser_version=browser.version
        context.close()
        browser.close()
    results.append({'case':'no_remote_requests','pass':not reqs,'requests':reqs})
    results.append({'case':'no_browser_script_errors','pass':not errors,'errors':errors})
    obj={
      'experiment_id':'PER-BROWSER-001','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
      'platform':platform.platform(),'browser':'Chromium '+browser_version,
      'offline_mode':True,'load':('file:// direct' if file_direct else 'offline in-memory HTML; managed browser blocked file://'),'file_uri_load_confirmed':file_direct,'network_requests':reqs,
      'n_cases':len(results),'n_passed':sum(t['pass'] for t in results),'all_passed':all(t['pass'] for t in results),'cases':results,
      'limitations':('single host browser engine; not a physical cross-device replication' if file_direct else 'managed Chromium policy blocks file:// and data: navigation; identical standalone HTML tested with set_content under offline network mode; physical direct-file test NOT verified'),
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'cases':obj['n_cases'],'passed':obj['n_passed'],'browser':obj['browser'],'result':str(OUT.relative_to(R))},indent=2))
    return 0 if obj['all_passed'] else 1

if __name__=='__main__':raise SystemExit(run())
