/* Portable Evidence Runtime - reference engine. No network APIs. Experimental local authoring mode. */
(function (root) {
  'use strict';
  const FORMAT = 'PER-LEDGER-1';
  const MAX_RECORDS = 500;
  const MAX_JSON_BYTES = 2_000_000;
  const ID_RE = /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/;
  const K = [
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
  ];
  function rotr(x, n) { return (x >>> n) | (x << (32-n)); }
  function utf8(input) {
    if (typeof TextEncoder !== 'undefined') return Array.from(new TextEncoder().encode(input));
    const encoded = unescape(encodeURIComponent(input));
    return Array.from(encoded, c => c.charCodeAt(0));
  }
  function sha256(input) {
    if (typeof input !== 'string') throw new TypeError('hash input must be a string');
    const bytes = utf8(input);
    const bitLenHi = Math.floor(bytes.length / 0x20000000);
    const bitLenLo = (bytes.length * 8) >>> 0;
    bytes.push(0x80);
    while (bytes.length % 64 !== 56) bytes.push(0);
    for (let shift = 24; shift >= 0; shift -= 8) bytes.push((bitLenHi >>> shift) & 255);
    for (let shift = 24; shift >= 0; shift -= 8) bytes.push((bitLenLo >>> shift) & 255);
    const H = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
    for (let off = 0; off < bytes.length; off += 64) {
      const w = new Array(64);
      for (let i=0; i<16; i++) {
        const j=off+i*4;
        w[i]=((bytes[j]<<24)|(bytes[j+1]<<16)|(bytes[j+2]<<8)|bytes[j+3])>>>0;
      }
      for(let i=16;i<64;i++) {
        const a=w[i-15], b=w[i-2];
        const s0=rotr(a,7)^rotr(a,18)^(a>>>3);
        const s1=rotr(b,17)^rotr(b,19)^(b>>>10);
        w[i]=(w[i-16]+s0+w[i-7]+s1)>>>0;
      }
      let [a,b,c,d,e,f,g,h]=H;
      for(let i=0;i<64;i++) {
        const s1=rotr(e,6)^rotr(e,11)^rotr(e,25);
        const ch=(e&f)^(~e&g);
        const t1=(h+s1+ch+K[i]+w[i])>>>0;
        const s0=rotr(a,2)^rotr(a,13)^rotr(a,22);
        const maj=(a&b)^(a&c)^(b&c);
        const t2=(s0+maj)>>>0;
        h=g;g=f;f=e;e=(d+t1)>>>0;d=c;c=b;b=a;a=(t1+t2)>>>0;
      }
      [a,b,c,d,e,f,g,h].forEach((x,i)=>{H[i]=(H[i]+x)>>>0;});
    }
    return H.map(x=>x.toString(16).padStart(8,'0')).join('');
  }
  function assertString(v, name, max, allowEmpty=false) {
    if(typeof v!=='string' || v.length>max || (!allowEmpty && !v.trim())) throw new Error('invalid '+name);
    return v;
  }
  function assertRef(ref, name) {
    if(ref===null) return null;
    if(!ref || typeof ref!=='object' || Array.isArray(ref) || Object.keys(ref).sort().join(',')!=='id,seal') throw new Error('invalid '+name);
    if(!ID_RE.test(ref.id) || !/^[0-9a-f]{64}$/.test(ref.seal)) throw new Error('invalid '+name);
    return {id:ref.id, seal:ref.seal};
  }
  function payload(input) {
    if(!input || typeof input!=='object' || Array.isArray(input)) throw new Error('record must be object');
    const keys=['id','kind','title','scope','body','facts','supersedes','parent'];
    const actual=Object.keys(input).filter(k=>k!=='seal').sort().join(',');
    if(actual!==keys.sort().join(',')) throw new Error('record fields must match schema');
    if(!ID_RE.test(input.id)) throw new Error('invalid id');
    if(!['source','derived'].includes(input.kind)) throw new Error('invalid kind');
    const title=assertString(input.title,'title',160);
    const scope=assertString(input.scope,'scope',100);
    const body=assertString(input.body,'body',30000,true);
    if(!Array.isArray(input.facts) || input.facts.length>50) throw new Error('invalid facts');
    const facts=input.facts.map((f)=>{
      if(!f || typeof f!=='object' || Array.isArray(f) || Object.keys(f).sort().join(',')!=='predicate,subject,value') throw new Error('invalid fact');
      return {subject:assertString(f.subject,'subject',140),predicate:assertString(f.predicate,'predicate',140),value:assertString(f.value,'value',1000)};
    });
    const parent=assertRef(input.parent,'parent');
    const supersedes=assertRef(input.supersedes,'supersedes');
    if((input.kind==='derived')!==Boolean(parent)) throw new Error('derived pages require pinned parent; sources cannot have parents');
    if(input.kind==='derived' && supersedes) throw new Error('this reference runtime supports supersession of source records only');
    if(parent && (parent.id===input.id || supersedes?.id===input.id)) throw new Error('self reference');
    if(supersedes && supersedes.id===input.id) throw new Error('self supersession');
    return {id:input.id,kind:input.kind,title,scope,body,facts,supersedes,parent};
  }
  function makeRecord(input) {
    const p=payload(input);
    return Object.assign({},p,{seal:sha256(JSON.stringify(p))});
  }
  function verifyRecord(r) {
    try {
      if(!r || typeof r!=='object' || Object.keys(r).length!==9 || !/^[0-9a-f]{64}$/.test(r.seal)) return false;
      const p=payload(r);
      return sha256(JSON.stringify(p))===r.seal;
    } catch(_e) {return false;}
  }
  function makeLedger(records) {
    if(!Array.isArray(records) || records.length>MAX_RECORDS) throw new Error('too many records');
    const l={format:FORMAT,records:records.slice()};
    validateLedgerShape(l);
    return l;
  }
  function validateLedgerShape(l) {
    if(!l || typeof l!=='object' || Array.isArray(l) || Object.keys(l).sort().join(',')!=='format,records' || l.format!==FORMAT || !Array.isArray(l.records) || l.records.length>MAX_RECORDS) throw new Error('invalid ledger structure');
    const ids=new Set();
    for(const r of l.records){
      if(!r || typeof r.id!=='string' || !ID_RE.test(r.id)) throw new Error('invalid record id');
      if(ids.has(r.id)) throw new Error('duplicate id '+r.id);
      ids.add(r.id);
    }
    return true;
  }
  function importLedger(json) {
    if(typeof json!=='string' || utf8(json).length>MAX_JSON_BYTES) throw new Error('oversize or invalid input');
    const l=JSON.parse(json);
    validateLedgerShape(l);
    // Do not silently reseal a tampered record. Its invalidity remains visible on retrieval.
    return l;
  }
  function exportLedger(l) {validateLedgerShape(l);return JSON.stringify(l,null,2)+'\n';}
  function getRecord(l,id) {return l.records.find(r=>r.id===id)||null;}
  function validChain(l,r,seen=new Set()) {
    if(!r || seen.has(r.id) || !verifyRecord(r)) return false;
    const next=new Set(seen);next.add(r.id);
    for(const ref of [r.parent,r.supersedes]){
      if(!ref) continue;
      const target=getRecord(l,ref.id);
      if(!target || target.seal!==ref.seal || !validChain(l,target,next)) return false;
    }
    return true;
  }
  function validSuccessors(l,r) {
    return l.records.filter(s=>s.kind==='source' && s.supersedes && s.supersedes.id===r.id && s.supersedes.seal===r.seal && validChain(l,s));
  }
  function eligible(l,id,seen=new Set()) {
    const r=getRecord(l,id);
    if(!r) return {ok:false,reason:'missing_record'};
    if(seen.has(id)) return {ok:false,reason:'cycle'};
    if(!validChain(l,r)) return {ok:false,reason:'invalid_seal_or_lineage'};
    if(validSuccessors(l,r).length) return {ok:false,reason:'superseded'};
    if(r.parent){
      const p=eligible(l,r.parent.id,new Set([...seen,id]));
      if(!p.ok) return {ok:false,reason:'stale_parent:'+p.reason};
    }
    return {ok:true,reason:'current',record:r};
  }
  function norm(s) {return s.trim().replace(/\s+/g,' ').toLocaleLowerCase('en');}
  function query(l,subject,predicate,selectedId='') {
    validateLedgerShape(l);
    assertString(subject,'subject',140);assertString(predicate,'predicate',140);
    if(selectedId && !ID_RE.test(selectedId)) throw new Error('invalid selected id');
    const hits=[];const rejected=[];
    const targetRecords=selectedId?[getRecord(l,selectedId)].filter(Boolean):l.records;
    if(selectedId && !targetRecords.length) return {answer_supported:false,status:'return',reason:'missing_selected_record'};
    for(const r of targetRecords){
      const f=Array.isArray(r.facts)?r.facts.filter(f=>f && typeof f.subject==='string' && typeof f.predicate==='string' && norm(f.subject)===norm(subject) && norm(f.predicate)===norm(predicate)):[];
      if(!f.length && !selectedId) continue;
      const state=eligible(l,r.id);
      if(!state.ok) {if(state.reason!=='superseded') rejected.push({id:r.id,reason:state.reason});continue;}
      for(const fact of f) hits.push({record:r,fact});
    }
    if(rejected.length) return {answer_supported:false,status:'return',reason:'invalid_candidate',rejected};
    if(!hits.length) return {answer_supported:false,status:'not_in_corpus',reason:'no_eligible_fact'};
    const owners=new Set(hits.map(h=>h.record.id));
    const values=new Set(hits.map(h=>norm(h.fact.value)));
    if(owners.size!==1 || values.size!==1) return {answer_supported:false,status:'ambiguous',reason:'multiple_owners_or_values',owners:[...owners]};
    const h=hits[0];
    return {answer_supported:true,status:'supported',value:h.fact.value,subject:h.fact.subject,predicate:h.fact.predicate,source:{id:h.record.id,seal:h.record.seal,title:h.record.title,scope:h.record.scope,exact_fact:`${h.fact.subject} | ${h.fact.predicate} | ${h.fact.value}`}};
  }
  function emptyInputs(){return {id:'',kind:'source',title:'',scope:'local',body:'',facts:[],supersedes:null,parent:null};}
  const api={FORMAT,sha256,makeRecord,verifyRecord,makeLedger,validateLedgerShape,importLedger,exportLedger,validChain,eligible,query,emptyInputs};
  if(typeof module!=='undefined' && module.exports) module.exports=api;
  root.PER=api;
})(typeof globalThis!=='undefined'?globalThis:this);
