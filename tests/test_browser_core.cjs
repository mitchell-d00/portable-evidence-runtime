/* Cross-language, no-package parity test for the offline JavaScript engine. */
const fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const ctx={TextEncoder,console};
vm.runInNewContext(fs.readFileSync(path.join(root,'web/source_runtime.js'),'utf8'),ctx);
const js=ctx.PER;
const capsule=JSON.parse(fs.readFileSync(path.join(root,'experiment/fixtures/demo_capsule.json'),'utf8'));
const pin=fs.readFileSync(path.join(root,'experiment/fixtures/demo_root.sha256'),'utf8').trim();
let checks=0;
function check(name,fn){fn();checks++;process.stdout.write('PASS '+name+'\n')}
check('sha empty and unicode',()=>{for(const txt of ['', 'abc','🌎 unit test','a'.repeat(10000)])assert.equal(js.sha256(txt),crypto.createHash('sha256').update(txt).digest('hex'))});
check('cross-language root parity',()=>assert.equal(js.verifyCapsule(capsule,pin).root_sha256,pin));
check('supported answer',()=>assert.equal(js.answer(capsule,'kiln-schedule').status,'supported'));
check('ambiguous refusal',()=>assert.equal(js.answer(capsule,'conflicting-answer').status,'ambiguous'));
check('machine-origin refusal',()=>assert.equal(js.answer(capsule,'machine-claim').status,'not_in_corpus'));
check('blocked refusal',()=>assert.equal(js.answer(capsule,'blocked-note').status,'not_in_corpus'));
check('natural language refusal',()=>assert.equal(js.answer(capsule,'what kiln?').status,'invalid_key'));
check('value mutation refusal',()=>{const c=structuredClone(capsule);c.records[4].body.value='fraud';assert.equal(js.answer(c,'kiln-schedule').status,'integrity_error')});
check('policy mutation refusal',()=>{const c=structuredClone(capsule);c.policy.allowed_status=['current','blocked'];assert.equal(js.answer(c,'lab-rule').status,'integrity_error')});
check('root mutation refusal',()=>{const c=structuredClone(capsule);c.root_sha256='f'.repeat(64);assert.equal(js.answer(c,'lab-rule').status,'integrity_error')});
check('offline HTML is self-contained',()=>{
 const html=fs.readFileSync(path.join(root,'web/index.html'),'utf8');
 assert.ok(html.includes('id="embedded-capsule"'));
 assert.match(html,/id="anchor"[^>]*value="[a-f0-9]{64}"/);
 assert.ok(html.includes('function sha256'));
 assert.ok(!/<script[^>]+src=|<link[^>]+href=|fetch\s*\(|https?:\/\//.test(html));
});
console.log('PASS '+checks+' browser-core checks');
