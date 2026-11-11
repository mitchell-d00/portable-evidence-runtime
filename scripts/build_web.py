"""Build a genuinely standalone offline HTML file from local JS and capsule."""
from pathlib import Path
import json
import sys
R=Path(__file__).resolve().parents[1]
source=json.loads((R/'experiment/fixtures/demo_capsule.json').read_text(encoding='utf-8'))
root=source['root_sha256']
js=(R/'web/source_runtime.js').read_text(encoding='utf-8').replace('__PINNED_ROOT__',root)
embedded=json.dumps(source,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
html='''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Portable Evidence Runtime · Offline Laboratory</title>
<style>
:root {font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#132334;background:#f5f8fb;}
*{box-sizing:border-box} body{margin:0} header{background:#102539;color:#eef7ff;padding:36px max(22px,calc((100% - 940px)/2));border-bottom:4px solid #35b6a5}
header .tag{color:#75eddd;text-transform:uppercase;letter-spacing:.15em;font-size:12px;font-weight:700}h1{font-size:clamp(26px,4vw,43px);line-height:1.12;margin:13px 0}header p{color:#d1e2ed;max-width:690px;line-height:1.5;margin:0}
main{max-width:940px;padding:28px 22px 60px;margin:auto;display:grid;gap:20px}.card{background:white;border:1px solid #dce5ec;border-radius:16px;padding:24px;box-shadow:0 5px 16px #172a400a}h2{margin:0 0 12px;font-size:20px}p{line-height:1.55}label{display:block;font-size:13px;font-weight:700;color:#435566;margin-bottom:8px}input[type=text]{width:100%;padding:14px;border:1px solid #a8b8c6;border-radius:9px;font-size:17px;font-family:ui-monospace,monospace}
.buttons{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}button,.upload{padding:11px 15px;border:1px solid #a9c4ca;border-radius:9px;background:white;color:#154d57;font-weight:700;cursor:pointer;font-size:14px}button.primary{background:#126f6c;border-color:#126f6c;color:white}button:hover,.upload:hover{filter:brightness(.95)}.upload{display:inline-flex;align-items:center}.upload input{display:none}
.state{padding:11px 14px;border-radius:9px;background:#edf3f8;color:#223647;font-weight:700}.state.ok{background:#e8f7ef;color:#116045}.state.bad{background:#ffedeb;color:#a52c27}.output{background:#f4f7fb;white-space:pre-wrap;word-break:break-word;border-radius:10px;padding:16px;line-height:1.55;min-height:95px;font-family:ui-monospace,monospace;font-size:13px}.output.good{border-left:4px solid #168568}
small{color:#566977}code{background:#edf1f5;padding:2px 5px;border-radius:5px}footer{color:#4b6170;line-height:1.5;font-size:13px} .hash{overflow-wrap:anywhere;font:12px ui-monospace,monospace;color:#506c7a}.sample{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 16px}.sample code{font-size:12px}@media(max-width:540px){.card{padding:18px}header{padding:28px 20px}}
</style></head><body>
<header><div class="tag">Portable reference system · version 1</div><h1>Evidence can travel.</h1><p>Memory, fixed decision rules, integrity verification and executable code are contained in one local HTML file. This is a bounded proof of portability, not a general-purpose language model.</p></header>
<main>
<section class="card"><h2>01 / Integrity check</h2><div id="integrity-status" class="state">Checking…</div><p id="trust-status"></p><small>Capsule root</small><p id="root-hash" class="hash"></p><label for="anchor">Independent expected root (SHA-256)</label><input id="anchor" type="text" value="__PINNED_ROOT__" maxlength="64" spellcheck="false" autocomplete="off" aria-describedby="anchor-help"><p id="anchor-help"><small>Use the separately recorded expected root. Clearing or changing it blocks supported answers. A hash carried only inside an untrusted capsule is not an independent anchor.</small></p><div class="buttons"><button id="verify-btn">Verify again</button><button id="export-btn">Export capsule JSON</button><label class="upload">Import local capsule<input id="import-input" type="file" accept=".json,application/json"></label><button id="reset-btn">Reset lab</button></div></section>
<section class="card"><h2>02 / Exact-key supported answers</h2><p>This is an <strong>exact-key</strong> lookup. It intentionally refuses paraphrases, missing keys, machine-origin claims, blocked records, ambiguous owners, and altered data.</p><label for="query">Exact key</label><input id="query" type="text" value="kiln-schedule" autocomplete="off" autocapitalize="off" spellcheck="false"><div class="sample"><code>kiln-schedule</code><code>lab-rule</code><code>conflicting-answer</code><code>machine-claim</code><code>blocked-note</code><code>unseen-key</code></div><div class="buttons"><button class="primary" id="ask-btn">Answer or refuse</button></div><h2 style="margin-top:20px">Decision</h2><div id="answer-output" class="output" aria-live="polite"></div></section>
<section class="card"><h2>03 / Deliberate boundaries</h2><p>No cloud account, server, external model, package install or network request is needed to open this file and query the embedded sample. Everything is synthetic. SHA-256 detects changed bytes when the hash is held fixed; it <strong>does not prove authorship, source truth or tamper-resistance</strong> against an adversary who can replace both the data and its declared hashes.</p><p>The independent Python implementation and experiment protocol are in the repository archive.</p></section>
<footer>Mitchell D. McPhetridge · Portable Evidence Runtime · Offline laboratory · No source acquisition or remote calls</footer></main>
<script type="application/json" id="embedded-capsule">__CAPSULE__</script>
<script>__SCRIPT__</script>
</body></html>
'''.replace('__CAPSULE__',embedded).replace('__PINNED_ROOT__',root).replace('__SCRIPT__',js.replace('</script','<\\/script'))
target=R/'web/index.html'
if '--check' in sys.argv:
    if not target.exists() or target.read_text(encoding='utf-8') != html:
        raise SystemExit('web/index.html is stale; run python3 scripts/build_web.py')
    print('PASS: strict web/index.html matches source and fixture')
else:
    target.write_text(html,encoding='utf-8')
    print('built web/index.html',len(html.encode('utf-8')),'bytes',root)
