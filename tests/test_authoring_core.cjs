/* Offline authoring-ledger engine tests, no npm dependencies. */
const fs=require('node:fs');
const assert=require('node:assert/strict');
const path=require('node:path');
const E=require('../src/engine.js');
let n=0;
function test(label,fn){fn();n++;console.log('PASS '+label);}
function record(id,value,parent=null,supersedes=null,kind='source'){
  return E.makeRecord({id,kind,title:'Synthetic '+id,scope:'test',body:'synthetic only',facts:[{subject:'Node A',predicate:'setting',value}],supersedes,parent});
}
const source=record('SRC-001','baseline');
test('source seal verifies',()=>assert.equal(E.verifyRecord(source),true));
test('basic source answer',()=>{
 const l=E.makeLedger([source]);const r=E.query(l,'Node A','setting');
 assert.equal(r.answer_supported,true);assert.equal(r.value,'baseline');
});
test('source mutation refused',()=>{
 const altered=structuredClone(source);altered.facts[0].value='forged';
 const l=E.makeLedger([altered]);const r=E.query(l,'Node A','setting');
 assert.equal(r.answer_supported,false);
});
test('missing fact refused',()=>{
 const r=E.query(E.makeLedger([source]),'Unseen Node','setting');
 assert.equal(r.status,'not_in_corpus');
});
test('ambiguous independent owners refused',()=>{
 const r=E.query(E.makeLedger([source,record('SRC-OTHER','different')]),'Node A','setting');
 assert.equal(r.status,'ambiguous');
});
test('verified successor retires older owner',()=>{
 const newer=record('SRC-002','revised',null,{id:source.id,seal:source.seal});
 const l=E.makeLedger([source,newer]);
 assert.equal(E.eligible(l,source.id).reason,'superseded');
 assert.equal(E.query(l,'Node A','setting').value,'revised');
});
test('derived parent pin becomes stale when source replaced',()=>{
 const newer=record('SRC-002','revised',null,{id:source.id,seal:source.seal});
 const derived=record('DER-001','derived',{id:source.id,seal:source.seal},null,'derived');
 const l=E.makeLedger([source,newer,derived]);
 assert.equal(E.eligible(l,derived.id).ok,false);
});
test('conflicting selected id refused',()=>{
 const r=E.query(E.makeLedger([source]),'Node A','setting','MISSING-ID');
 assert.equal(r.answer_supported,false);
});
test('json import/export round trip',()=>{
 const l=E.makeLedger([source]);const x=E.importLedger(E.exportLedger(l));
 assert.equal(E.query(x,'Node A','setting').value,'baseline');
});
test('browser artifact built and network-free',()=>{
 const html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
 assert.ok(html.includes('Portable Evidence Runtime'));
 assert.ok(html.includes('function sha256'));
 assert.ok(!/<script[^>]*src=|<link[^>]*href=|fetch\s*\(/.test(html));
});
console.log('PASS '+n+' authoring checks');
