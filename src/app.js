(function(){
'use strict';
const E=globalThis.PER;
const $=(s)=>document.querySelector(s);
const STORAGE_KEY='portable_evidence_runtime_v1';
let ledger;
function inputRecord(id,title,body,facts,scope='local',parent=null,supersedes=null,kind='source') {
 return E.makeRecord({id,kind,title,scope,body,facts:facts.map(([subject,predicate,value])=>({subject,predicate,value})),supersedes,parent});
}
function demo(){
 const a=inputRecord('KILN-001','Kiln operating note','Local demo page, authored for the portability experiment. The maximum operating temperature is 900 C.',[['Kiln A','maximum temperature','900 C'],['Kiln A','cooldown rule','Keep closed until below 100 C']]);
 const b=inputRecord('LAB-001','Lab scope note','Demonstration policy: evidence does not establish source truth.',[['This archive','truth guarantee','No; the seal checks consistency, not authenticity or factual truth']]);
 const c=inputRecord('KILN-DER-001','Derived kiln checklist','A derivative pinned to the exact source page. A valid replacement of the parent makes this derivative ineligible.',[['Kiln A','checklist','Check cooling status before opening']], 'local',{id:a.id,seal:a.seal},null,'derived');
 return E.makeLedger([a,b,c]);
}
function save(){
 try{localStorage.setItem(STORAGE_KEY,E.exportLedger(ledger));return true;}catch(e){$('#storage-info').textContent='Browser storage unavailable; export JSON to keep your work.';return false;}
}
function load(){try{const s=localStorage.getItem(STORAGE_KEY);return s?E.importLedger(s):demo();}catch(e){return demo();}}
function fileDownload(name,data,type){const blob=new Blob([data],{type});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function message(t,isBad=false){const e=$('#message');e.textContent=t;e.className='result'+(isBad?' bad':' ok');}
function fieldFacts(s){return s.split(/\r?\n/).filter(x=>x.trim()).map((line,i)=>{const parts=line.split('|');if(parts.length!==3||parts.some(p=>!p.trim()))throw Error('Fact line '+(i+1)+' must be: subject | predicate | value');return parts.map(x=>x.trim());});}
function render(){
 $('#count-pages').textContent=ledger.records.length;
 const current=ledger.records.filter(r=>E.eligible(ledger,r.id).ok).length;
 $('#count-current').textContent=current;
 $('#count-blocked').textContent=ledger.records.length-current;
 const list=$('#records');list.replaceChildren();
 for(const r of ledger.records){const status=E.eligible(ledger,r.id);const wrap=document.createElement('div');wrap.className='record';const head=document.createElement('div');head.className='record-head';const name=document.createElement('strong');name.textContent=r.title||r.id;const pill=document.createElement('span');pill.className='tag'+(status.ok?'':status.reason==='superseded'?' dim':' bad');pill.textContent=status.ok?'ELIGIBLE':status.reason.toUpperCase();head.append(name,pill);wrap.append(head);
 const meta=document.createElement('small');meta.textContent=r.id+' · '+r.kind+' · '+r.scope+' · '+((r.facts||[]).length)+' fact(s)';wrap.append(meta);
 const hash=document.createElement('small');hash.className='mono';hash.textContent='SHA-256 '+String(r.seal||'').slice(0,25)+'…';wrap.append(hash);list.append(wrap);}
 for(const selector of ['#supersedes','#parent','#selected-id']){const node=$(selector);const old=node.value;node.replaceChildren();const first=document.createElement('option');first.value='';first.textContent=selector==='#selected-id'?'Automatic owner search':'None';node.append(first);
 for(const r of ledger.records){if(selector==='#supersedes'&&r.kind!=='source')continue;const o=document.createElement('option');o.value=r.id;o.textContent=r.id+(E.eligible(ledger,r.id).ok?' (eligible)':' (blocked)');node.append(o);}node.value=old;}
}
function add(){try{
 const id=$('#id').value.trim();if(ledger.records.some(r=>r.id===id))throw Error('The ID already exists. Use a new ID to add a revision.');
 const kind=$('#kind').value;const supId=$('#supersedes').value;const parentId=$('#parent').value;
 const ref=(v)=>v?({id:v,seal:ledger.records.find(r=>r.id===v)?.seal}):null;
 const entry=E.makeRecord({id,kind,title:$('#title').value,scope:$('#scope').value,body:$('#body').value,facts:fieldFacts($('#facts').value).map(([subject,predicate,value])=>({subject,predicate,value})),supersedes:ref(supId),parent:ref(parentId)});
 ledger=E.makeLedger(ledger.records.concat([entry]));save();render();ask();message('Page added and sealed. SHA-256: '+entry.seal);$('#id').value='';$('#title').value='';$('#body').value='';$('#facts').value='';
 }catch(e){message(String(e.message),true);}}
function ask(){try{
 const answer=E.query(ledger,$('#q-subject').value,$('#q-predicate').value,$('#selected-id').value);
 const out=$('#answer');out.className='result '+(answer.answer_supported?'ok':'bad');
 out.textContent=answer.answer_supported?('SUPPORTED ANSWER: '+answer.value+'\n\nSource: '+answer.source.id+'\nExact evidence: '+answer.source.exact_fact+'\nSeal: '+answer.source.seal):('REFUSED: '+answer.status+'\nReason: '+answer.reason+(answer.rejected?'\nRejected pages: '+answer.rejected.map(x=>x.id+' ('+x.reason+')').join(', '):''));
 }catch(e){$('#answer').className='result bad';$('#answer').textContent='ERROR: '+e.message;}}
$('#add').addEventListener('click',add);
$('#ask').addEventListener('click',ask);
$('#export').addEventListener('click',()=>{fileDownload('per-ledger.json',E.exportLedger(ledger),'application/json');message('Ledger exported. Reimport it in a fresh browser profile to test recovery.');});
$('#import-button').addEventListener('click',()=>$('#import-file').click());
$('#import-file').addEventListener('change',async(e)=>{const f=e.target.files[0];if(!f)return;try{if(f.size>2_000_000)throw Error('file too large');const imported=E.importLedger(await f.text());ledger=imported;save();render();ask();message('Ledger imported without resealing. Corrupted records remain blocked by verification.');}catch(err){message('Import refused: '+err.message,true);}finally{e.target.value='';}});
$('#reset').addEventListener('click',()=>{if(!confirm('Replace the current ledger with the demonstration pages? Export a backup first.'))return;ledger=demo();save();render();ask();message('Sample ledger restored.');});
$('#kind').addEventListener('change',()=>{const derived=$('#kind').value==='derived';$('#parent-wrap').classList.toggle('hidden',!derived);$('#supersedes-wrap').classList.toggle('hidden',derived);if(derived){$('#supersedes').value='';}else{$('#parent').value='';}});
ledger=load();save();render();ask();
})();
