/* Portable Evidence Runtime 1.0: browser/Node reference implementation.
 * Entirely local; no fetch, WebCrypto, imports, network, or external assets.
 * SHA-256 is an integrity checksum, not an authenticated signature.
 */
(function (root) {
  'use strict';
  const FORMAT = 'portable-evidence-capsule/1';
  const POLICY = { answer_mode:'exact-key', allowed_status:['current'], allowed_origin:['human'], ambiguous:'refuse' };
  const BODY_FIELDS = ['id','key','value','status','origin','revision','supersedes'];
  const rot = (v,n) => (v >>> n) | (v << (32-n));
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
  function sha256(str) {
    const orig = new TextEncoder().encode(str);
    const length = orig.length;
    const pad = (64 - ((length + 9) % 64)) % 64;
    const msg = new Uint8Array(length + 9 + pad);
    msg.set(orig); msg[length]=128;
    const bits = BigInt(length) * 8n;
    for (let j=0;j<8;j++) msg[msg.length-1-j]=Number((bits >> BigInt(j*8)) & 255n);
    let h = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
    for (let i=0;i<msg.length;i+=64) {
      const w=new Uint32Array(64);
      for (let t=0;t<16;t++) {
        const o=i+t*4;
        w[t]=((msg[o]<<24)|(msg[o+1]<<16)|(msg[o+2]<<8)|msg[o+3])>>>0;
      }
      for(let t=16;t<64;t++) {
        const a=w[t-15],b=w[t-2];
        const s0=rot(a,7)^rot(a,18)^(a>>>3);
        const s1=rot(b,17)^rot(b,19)^(b>>>10);
        w[t]=(w[t-16]+s0+w[t-7]+s1)>>>0;
      }
      let [a,b,c,d,e,f,g,z]=h;
      for(let t=0;t<64;t++) {
        const s1=rot(e,6)^rot(e,11)^rot(e,25);
        const ch=(e&f)^(~e&g);
        const t1=(z+s1+ch+K[t]+w[t])>>>0;
        const s0=rot(a,2)^rot(a,13)^rot(a,22);
        const maj=(a&b)^(a&c)^(b&c);
        const t2=(s0+maj)>>>0;
        z=g;g=f;f=e;e=(d+t1)>>>0;d=c;c=b;b=a;a=(t1+t2)>>>0;
      }
      const vals=[a,b,c,d,e,f,g,z];
      h=h.map((v,j)=>(v+vals[j])>>>0);
    }
    return h.map(v=>v.toString(16).padStart(8,'0')).join('');
  }
  function ownFields(obj,fields) {
    return obj !== null && typeof obj === 'object' && !Array.isArray(obj) &&
      JSON.stringify(Object.keys(obj)) === JSON.stringify(fields);
  }
  function checkBody(b) {
    if (!ownFields(b,BODY_FIELDS)) throw Error('record body fields/order invalid');
    if (typeof b.id!=='string'||!/^[A-Z0-9_-]{3,80}(?![\s\S])/.test(b.id)) throw Error('invalid record ID');
    if (typeof b.key!=='string'||!/^[a-z0-9-]{2,80}(?![\s\S])/.test(b.key)) throw Error('invalid exact lookup key');
    if (typeof b.value!=='string'||[...b.value].length<1||[...b.value].length>10000 ||
        [...b.value].some(ch=>ch.codePointAt(0)>=0xD800 && ch.codePointAt(0)<=0xDFFF)) throw Error('invalid value');
    if (!['current','retired','blocked'].includes(b.status)) throw Error('invalid status');
    if (!['human','machine','imported'].includes(b.origin)) throw Error('invalid origin');
    if (!Number.isSafeInteger(b.revision)||b.revision<1) throw Error('invalid revision');
    if (b.supersedes !== null && (typeof b.supersedes!=='string'||!/^[A-Z0-9_-]{3,80}(?![\s\S])/.test(b.supersedes)))
      throw Error('invalid supersedes pointer');
  }
  function rootMaterial(c) {
    return {format:c.format,policy:c.policy,records:c.records.map(r=>({id:r.body.id,sha256:r.sha256}))};
  }
  function verifyCapsule(c,expectedRoot=null) {
    if (!ownFields(c,['format','policy','records','root_sha256'])) throw Error('invalid capsule envelope');
    if (c.format !== FORMAT || JSON.stringify(c.policy)!==JSON.stringify(POLICY)) throw Error('unsupported format or changed policy');
    if (!Array.isArray(c.records)||c.records.length<1||c.records.length>10000) throw Error('invalid record count');
    const ids=[], byId=Object.create(null);
    for (const r of c.records) {
      if (!ownFields(r,['body','sha256'])) throw Error('invalid record wrapper');
      checkBody(r.body);
      if (r.sha256!==sha256(JSON.stringify(r.body))) throw Error('record digest mismatch: '+r.body.id);
      ids.push(r.body.id); byId[r.body.id]=r.body;
    }
    const ordered=[...new Set(ids)].sort();
    if (JSON.stringify(ids)!==JSON.stringify(ordered)) throw Error('duplicate or unsorted IDs');
    for (const b of Object.values(byId)) {
      if (b.supersedes===null) continue;
      const old=byId[b.supersedes];
      if (!old||old.key!==b.key||old.revision>=b.revision) throw Error('invalid lineage: '+b.id);
    }
    const rootHash=sha256(JSON.stringify(rootMaterial(c)));
    if (rootHash!==c.root_sha256) throw Error('capsule root mismatch');
    if (expectedRoot !== null && expectedRoot!==rootHash) throw Error('pinned root mismatch');
    return {ok:true,record_count:ids.length,root_sha256:rootHash,
      trust:expectedRoot===null?'self-consistent, not authenticated':'matches supplied anchor; anchor trust is external'};
  }
  function answer(c,key,expectedRoot=null) {
    let result;
    try { result=verifyCapsule(c,expectedRoot); }
    catch(e) {return {status:'integrity_error',answer_supported:false,reason:String(e.message)};}
    if(typeof key!=='string'||!/^[a-z0-9-]{2,80}(?![\s\S])/.test(key))
      return {status:'invalid_key',answer_supported:false,reason:'enter an exact key, not a natural-language question'};
    const owners=c.records.filter(r=>r.body.key===key && r.body.status==='current' && r.body.origin==='human');
    if(owners.length>1) return {status:'ambiguous',answer_supported:false,reason:'multiple eligible owners',owner_count:owners.length};
    if(!owners.length) return {status:'not_in_corpus',answer_supported:false,reason:'no eligible current human-authored record'};
    const r=owners[0],b=r.body;
    return {status:'supported',answer_supported:true,answer:b.value,
      evidence:{id:b.id,key:b.key,revision:b.revision,sha256:r.sha256,root_sha256:result.root_sha256}};
  }
  root.PER = Object.freeze({FORMAT,POLICY,sha256,checkBody,verifyCapsule,answer});

  if (typeof document !== 'undefined') {
    const $=id=>document.getElementById(id);
    const sample=JSON.parse($('embedded-capsule').textContent);
    const PINNED_DEMO_ROOT='__PINNED_ROOT__';
    let active=sample;
    const status=$('integrity-status'), output=$('answer-output'), trust=$('trust-status');
    const currentAnchor=()=>$('anchor').value.trim().toLowerCase();
    function showVerify() {
      try {
        const proof=verifyCapsule(active);
        const anchor=currentAnchor();
        const pinned = /^[0-9a-f]{64}$/.test(anchor) && proof.root_sha256===anchor;
        status.textContent=(pinned?'ANCHORED: ':'UNANCHORED: ')+proof.record_count+' records internally consistent';
        status.className=pinned?'state ok':'state bad';
        trust.textContent=pinned?
           'Matches the supplied expected root. It remains your responsibility to trust how that anchor was obtained.':
           'No matching independent root. Internal consistency is not authentication; answering is blocked.';
        $('root-hash').textContent=proof.root_sha256;
        return true;
      } catch(e) {
        status.textContent='BLOCKED: '+String(e.message);
        status.className='state bad';
        trust.textContent='Do not use this capsule for answering.';
        $('root-hash').textContent='—';
        return false;
      }
    }
    function askNow() {
      const anchor=currentAnchor();
      const r=/^[0-9a-f]{64}$/.test(anchor)?answer(active,$('query').value.trim(),anchor):
        {status:'missing_anchor',answer_supported:false,reason:'A valid independent expected root is required for supported answers.'};
      output.textContent=r.answer_supported?
        'SUPPORTED · '+r.answer+'\n\nEvidence: '+r.evidence.id+' · rev '+r.evidence.revision+'\n'+r.evidence.sha256:
        'REFUSED · '+r.status+'\n'+r.reason;
      output.className=r.answer_supported?'output good':'output';
    }
    $('verify-btn').addEventListener('click',()=>{showVerify();askNow();});
    $('anchor').addEventListener('input',()=>{showVerify();askNow();});
    $('ask-btn').addEventListener('click',askNow);
    $('query').addEventListener('keydown',e=>{if(e.key==='Enter')askNow();});
    $('reset-btn').addEventListener('click',()=>{active=sample;$('anchor').value=PINNED_DEMO_ROOT;$('query').value='kiln-schedule';showVerify();askNow();});
    $('export-btn').addEventListener('click',()=>{
      const blob=new Blob([JSON.stringify(active,null,2)+'\n'],{type:'application/json'});
      const a=document.createElement('a'); a.href=URL.createObjectURL(blob);a.download='portable-capsule.json';a.click();
      setTimeout(()=>URL.revokeObjectURL(a.href),1000);
    });
    $('import-input').addEventListener('change',async e=>{
      const file=e.target.files?.[0];if(!file)return;
      if(file.size>2000000){active=null;showVerify();askNow();status.textContent='BLOCKED: file over 2 MB';e.target.value='';return;}
      try{active=JSON.parse(await file.text());showVerify();askNow();}
      catch(err){active=null;showVerify();output.textContent='Invalid import: '+String(err.message);}
      e.target.value='';
    });
    showVerify();askNow();
  }
})(typeof globalThis!=='undefined'?globalThis:this);
