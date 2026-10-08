// Audit statique root réutilisable : aucun processus enfant ni réseau.
import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
const root=process.argv[2];
const need=(x,m)=>{if(!x)throw Error(m);};
need(root==='/private/tmp/therese-c17-wrapper-canary-8612f55886284332a3ac6a7bc9615021'
  &&/^\/private\/tmp\/therese-c17-wrapper-canary-[a-f0-9]{32}$/.test(root),'Racine WRAPPER13 exacte requise');
function sameRef(a,b){
  const exact=x=>x!==null&&typeof x==='object'&&!Array.isArray(x)
    &&Object.keys(x).sort().join(',')==='bytes,path,sha256'
    &&typeof x.path==='string'&&x.path.startsWith('/')
    &&typeof x.sha256==='string'&&/^[a-f0-9]{64}$/.test(x.sha256)
    &&Number.isSafeInteger(x.bytes)&&x.bytes>=0;
  return exact(a)&&exact(b)&&a.path===b.path&&a.sha256===b.sha256&&a.bytes===b.bytes;
}
const qa='/private/tmp/therese-c17-wrapper-source-kGvU1hdx/source';
const head='2d69e30c9c6dd18823ee6102271876003a6a67cc';
need(process.getuid()===501,'UID utilisateur 501 exact requis');
const systemProfiles=new Map([
  ['/System/Library/Sandbox/Profiles/com.apple.GameOverlayUI.sb',
    {sha256:'6320ed0b8a6933b3c62cbfc8c3149a9f1dcc0a968cbfbc6f99a1270ab2c99257',bytes:10845}],
  ['/System/Library/Sandbox/Profiles/com.apple.gputoolsserviced.sb',
    {sha256:'fb1381764287e32128b8d6db40353059667ca4a2a64e7b778d1ef5773bb51841',bytes:7234}],
  ['/System/Library/Sandbox/Profiles/appsandbox-common.sb',
    {sha256:'b9ffebd2141aca32c609f4a707f5a6b980ae4be45299ee3f3c18534b69cb7cea',bytes:32355}],
]);
const ref=p=>{
  const s=fs.lstatSync(p),b=fs.readFileSync(p);
  const sha256=crypto.createHash('sha256').update(b).digest('hex');
  const expectedSystem=systemProfiles.get(p);
  const ownerExact=expectedSystem
    ? s.uid===0&&s.gid===0&&s.mode===0o100644&&s.nlink===1
      &&sha256===expectedSystem.sha256&&b.length===expectedSystem.bytes
    : s.uid===501;
  need(s.isFile()&&!s.isSymbolicLink()&&ownerExact&&fs.realpathSync(p)===p,'Ref non canonique ou propriétaire non admis '+p);
  return {path:p,sha256,bytes:b.length};
};
const builderRef=ref('/private/tmp/therese-c17-wrapper13-dirhelper-P5WQpQ/build_fresh_wrapper.py');
const builderProposalIndexRef=ref('/private/tmp/therese-c17-wrapper13-dirhelper-P5WQpQ/PLAN-INDEX.json');
const historicalBuilderIndexRef=ref('/private/tmp/therese-c17-fresh-wrapper-builder-v10-ynPAzC/INDEX.json');
need(builderRef.sha256==='f76830c89475c58ea63599d7633d9a5031777a0655b2c0c3a838bdea96fe5719'
  &&builderRef.bytes===90352
  &&builderProposalIndexRef.sha256==='0956da6b74598f64639c4dd491cdaf21378247b14316a5ac7e2084cd018529e9'
  &&builderProposalIndexRef.bytes===4918
  &&historicalBuilderIndexRef.sha256==='ad4cbc19f3c156f0b0d4ff2e3d36b31eccc9bda109cb18cc6c77194aefce1007'
  &&historicalBuilderIndexRef.bytes===8012,'Constructeur/proposition WRAPPER13 différents');
const read=p=>JSON.parse(fs.readFileSync(p));
const refs=new Map(),pending=[],historicalObservations=[];
const historicalG1ReceiptPaths=new Set([
  '/private/tmp/therese-c17-g1-26-pure-rgpjt79j/receipt.json',
  '/private/tmp/therese-c17-g1-26-pure-bmy35r8g/receipt.json',
  '/private/tmp/therese-c17-g1-26-pure-we_pel56/receipt.json',
]);
const historicalCrashIndex='/private/tmp/therese-c17-chrome-rootdomain-h5whIv/INDEX.json';
const historicalCrashRef={
  path:'/Users/synoptia/Library/Logs/DiagnosticReports/Google Chrome-2026-10-08-143832.000.ips',
  sha256:'2e1d81e295a1a75af7498e1698b4284c53206f7a031058ebd3331aad6fc8a3b3',
  bytes:31835,
};
const historicalCrashOrigins=new Map([
  [historicalCrashIndex,{pointer:'/origin_refs/4',
    sha256:'c0f542c377d37efd8e88103e2d760fdc126b785793f167755a319f0f5fb8d3c6',
    bytes:2605,kind:'diagnostic_index'}],
  ['/private/tmp/therese-c17-root-v10-71-replay-v3-zRFPBqd5/receipt.json',
    {pointer:'/source_refs/267',
      sha256:'c0864b435265a4c485c78837207184d3964e966689eb97785fe3ab4ff9e3f8e5',
      bytes:68793,kind:'pure_replay_green',source_refs:307,passed:true,errors:0}],
  ['/private/tmp/therese-c17-root-v10-71-replay-v2-eaECHtDi/receipt.json',
    {pointer:'/source_refs/267',
      sha256:'1955d363f88493a62d6423baeed094f10ab53fbb6ced7eaac94251ba73cdfb57',
      bytes:66947,kind:'pure_replay_red',source_refs:303,passed:false,errors:3}],
]);
const archivalCrashPath='/private/tmp/therese-c17-root-close6-I9BhiHpZ/chrome25577.ips';
const pointerChild=(pointer,key)=>pointer+'/'+String(key).replace(/~/g,'~0').replace(/\//g,'~1');
const collect=(x,origin='direct',pointer='')=>{
  if(Array.isArray(x))x.forEach((y,i)=>collect(y,origin,pointerChild(pointer,i)));
  else if(x&&typeof x==='object'){
    if(x.schema==='c17-g1-26-pure-tests-v1'&&historicalG1ReceiptPaths.has(origin)){
      // Ce reçu observe le passé : son contenu est pinné, ses snapshots ne sont
      // pas des exigences sur les mêmes chemins physiques après le successeur.
      need(x.pins_before.length===11&&JSON.stringify(x.pins_before)===JSON.stringify(x.pins_after)
        &&x.pins_unchanged===true&&x.passed===true&&x.native_OS_qualification===false
        &&x.FULL_admission===false,'Reçu historique G1 inattendu '+JSON.stringify({origin,count:x.pins_before?.length,unchanged:x.pins_unchanged,passed:x.passed,native:x.native_OS_qualification,FULL:x.FULL_admission,equal:JSON.stringify(x.pins_before)===JSON.stringify(x.pins_after)}));
      historicalObservations.push({origin,kind:'pure_test_observation',refs:x.pins_before.length});
      for(const [k,v] of Object.entries(x))if(!['pins_before','pins_after'].includes(k))collect(v,origin,pointerChild(pointer,k));
    }else if(historicalCrashOrigins.has(origin)&&pointer===historicalCrashOrigins.get(origin).pointer){
      const expectedOrigin=historicalCrashOrigins.get(origin);
      need(sameRef(x,historicalCrashRef),'Rapport historique non exactement épinglé');
      const originRef=ref(origin);
      need(originRef.sha256===expectedOrigin.sha256&&originRef.bytes===expectedOrigin.bytes,
        'Origine historique non exacte');
      let evidenceRef=null;
      if(expectedOrigin.kind==='diagnostic_index'){
        const index=read(origin);
        need(index.origin_refs?.length===5&&sameRef(index.origin_refs[4],historicalCrashRef),
          'Pointeur du rapport historique non exact');
        evidenceRef=ref('/private/tmp/therese-c17-chrome-rootdomain-h5whIv/EVIDENCE.json');
        need(evidenceRef.sha256==='57253794719541add1642bc011ff0437248eb922eb798ec4b6132a8ff81c5f6a'
          &&evidenceRef.bytes===803,'Preuve historique non exacte');
        const evidence=read(evidenceRef.path);
        need(evidence.diagnostic_only===true&&evidence.chrome_pid===25577
          &&evidence.origin_crash_report===historicalCrashRef.path,'Observation historique hors diagnostic');
      }else{
        const receipt=read(origin);
        need(receipt.schema==='c17-root-v10-71-pure-replay-v1'&&receipt.actor==='/root'
          &&receipt.tests===71&&receipt.unchanged===true
          &&receipt.passed===expectedOrigin.passed&&receipt.errors===expectedOrigin.errors
          &&receipt.failures===0&&receipt.skipped===0
          &&receipt.root_built===false&&receipt.G1_imported===false
          &&receipt.native_workload_executed===false&&receipt.FULL===false&&receipt.release===false
          &&Array.isArray(receipt.forbidden_attempts)&&receipt.forbidden_attempts.length===0
          &&receipt.source_refs?.length===expectedOrigin.source_refs
          &&sameRef(receipt.source_refs[267],historicalCrashRef),
          'Reçu de tests purs historique inattendu ou réétiqueté');
        if(expectedOrigin.kind==='pure_replay_green'){
          need(Array.isArray(receipt.fixture_entries_after_cleanup)
            &&receipt.fixture_entries_after_cleanup.length===0
            &&sameRef(receipt.earlier_red_receipt_ref,{
              path:'/private/tmp/therese-c17-root-v10-71-replay-v2-eaECHtDi/receipt.json',
              sha256:'1955d363f88493a62d6423baeed094f10ab53fbb6ced7eaac94251ba73cdfb57',
              bytes:66947}),
            'Reçu vert historique détaché du rouge');
        }
      }
      let oldPathAbsent=false;
      try{fs.lstatSync(historicalCrashRef.path);}catch(error){oldPathAbsent=error?.code==='ENOENT';}
      need(oldPathAbsent,'Rapport historique non absent avec ENOENT');
      const archivedStat=fs.lstatSync(archivalCrashPath);
      need(archivedStat.isFile()&&!archivedStat.isSymbolicLink()
        &&archivedStat.uid===501&&archivedStat.gid===0&&archivedStat.mode===0o100600
        &&archivedStat.nlink===1&&fs.realpathSync(archivalCrashPath)===archivalCrashPath,
        'Copie archivale non canonique ou métadonnées inattendues');
      const archivedRef=ref(archivalCrashPath);
      need(archivedRef.sha256===historicalCrashRef.sha256&&archivedRef.bytes===historicalCrashRef.bytes,
        'Copie archivale différente du rapport historique');
      const old=refs.get(archivedRef.path);
      need(!old||sameRef(old,archivedRef),'Pins contradictoires copie archivale');
      if(!old){refs.set(archivedRef.path,archivedRef);pending.push(archivedRef);}
      historicalObservations.push({kind:'historical_crash_report_archival_byte_match',
        origin:originRef,origin_kind:expectedOrigin.kind,origin_pointer:pointer,evidence:evidenceRef,
        pure_replay_passed:expectedOrigin.passed??null,pure_replay_errors:expectedOrigin.errors??null,
        original_ref:historicalCrashRef,original_path_absent_ENOENT:oldPathAbsent,
        archival_ref:archivedRef,archival_metadata:{uid:archivedStat.uid,gid:archivedStat.gid,
          mode:archivedStat.mode,nlink:archivedStat.nlink},measured_at:new Date().toISOString(),
        close6_receipt_provenance_claimed:false});
    }else if(typeof x.path==='string'&&x.path.startsWith('/')&&/^[a-f0-9]{64}$/.test(x.sha256)&&Object.keys(x).every(k=>['path','sha256','bytes','git_blob'].includes(k))){
      const old=refs.get(x.path);need(!old||old.sha256===x.sha256,'Pins contradictoires '+x.path+' origine='+origin+' '+JSON.stringify({old,new:x}));
      if(!old){refs.set(x.path,x);pending.push(x);}
    }else for(const [k,v] of Object.entries(x))collect(v,origin,pointerChild(pointer,k));
  }
};
const construction=read(root+'/fresh-wrapper-construction.json');
need(construction.head===head&&construction.root===root&&construction.source_refs_count===79
  &&construction.runtime_executed===false&&construction.G1_imported===false&&construction.FULL===false,'Construction hors préparation');
need(Array.isArray(construction.historical_ips_observations)
  &&construction.historical_ips_observations.length===3
  &&new Set(construction.historical_ips_observations.map(o=>o.origin+'#'+o.pointer)).size===3
  &&construction.historical_ips_observations.every(o=>o.old_path===historicalCrashRef.path
    &&o.old_sha256===historicalCrashRef.sha256&&o.old_bytes===historicalCrashRef.bytes
    &&o.old_path_absent===true&&o.archive_path===archivalCrashPath
    &&o.archive_sha256===historicalCrashRef.sha256&&o.archive_bytes===historicalCrashRef.bytes
    &&o.runtime_qualification===false&&o.close6_receipt_provenance_claimed===false)
  &&construction.historical_ips_observations.some(o=>o.kind==='pure_replay_red'
    &&o.passed===false&&o.errors===3),
  'Trois observations IPS archivales exactes/rouge V2 absents');
const table=read(construction.source_refs_ref.path);
need(table.source_refs.length===79&&new Set(table.source_refs.map(x=>x.path)).size===79,'Table79 invalide');
need(construction.deltas.length===6&&construction.runner_boundary_definition_refs.length===7,'Deltas6/preuves7 absents');
collect(construction);collect(table);collect(ref(root+'/fresh-wrapper-construction.json'));
for(const [key,count] of [['base11_ref',11],['support8_ref',8],['overlay28_ref',28]]){
  const j=read(construction[key].path);need(Object.keys(j.outputs).length===count,'Sorties '+key);collect(j);
}
const core=read(construction.core18_ref.path);need(core.copies.length===18,'Core18 absent');
for(const row of core.copies)if(row.derivation==='byte_exact')need(ref(row.input.path).sha256===ref(row.output.path).sha256,'Copie non byte-exacte');
const authority=read(construction.authority_ref.path);
const chromeV10Ref=ref('/private/tmp/therese-c17-fresh-wrapper-builder-v10-ynPAzC/profile/chrome.sb');
const chromeMain11Ref=ref('/private/tmp/therese-c17-wrapper-profile-three-builder-G8n4Ef/profile/chrome.sb');
const chromeMain12Ref=ref('/private/tmp/therese-c17-wrapper12-metadata-parent-MtcoJZ/profile/chrome.sb');
const chromeMain12IndexRef=ref('/private/tmp/therese-c17-wrapper12-metadata-parent-MtcoJZ/PLAN-INDEX.json');
const chromeCandidateRef=ref('/private/tmp/therese-c17-wrapper13-dirhelper-P5WQpQ/profile/chrome.sb');
const getconfProfileRef=ref('/private/tmp/therese-c17-getconf-dirhelper-XeZCB9/profiles/dirhelper.sb');
const getconfIndexRef=ref('/private/tmp/therese-c17-getconf-dirhelper-XeZCB9/INDEX.json');
const chromeProposalRef=ref('/private/tmp/therese-c17-chrome-targeted-three-McWh5vFc/INDEX.json');
const builderProposal=read(builderProposalIndexRef.path);
const chromeProposal=read(chromeProposalRef.path);
need(chromeV10Ref.sha256==='19808ee2cac3169e9fb8c71c24385bcbb97f924c5ed785f4651817ecaa179b0c'
  &&chromeV10Ref.bytes===2067
  &&chromeMain11Ref.sha256==='bee3c2e780e58cbc80ed7e37d64115adf08997aab39dae8f11b56050785633a9'
  &&chromeMain11Ref.bytes===2375
  &&chromeMain12Ref.sha256==='980b12368975718d33dba1572ce94da04ca378ca827df1be10a1ed15a7104cdb'
  &&chromeMain12Ref.bytes===2439
  &&chromeMain12IndexRef.sha256==='e7ab1ad86f5ba0dde5dde38bb2feeb3dd31b1d53d18981ac3a9d34aa29f12a15'
  &&chromeMain12IndexRef.bytes===4788
  &&chromeCandidateRef.sha256==='2ecae3a24ec871a44827b3f712ced1ef5e84d8f778906c37b3a5b51bb374dcdf'
  &&chromeCandidateRef.bytes===2499
  &&getconfProfileRef.sha256===chromeCandidateRef.sha256
  &&getconfProfileRef.bytes===chromeCandidateRef.bytes
  &&getconfIndexRef.sha256==='72a3724edd8687408184b9a0a425247f0c152a17373e602e655ef2281b66cb9c'
  &&getconfIndexRef.bytes===2141
  &&chromeProposalRef.sha256==='499ed6c8c75ba66857e6797728b0c1a39a2fb93bff6f96827049639195b6d966'
  &&sameRef(builderProposal.candidate_chrome_profile,chromeCandidateRef)
  &&sameRef(builderProposal.historical_main11_builder_index,
    ref('/private/tmp/therese-c17-wrapper-profile-three-builder-G8n4Ef/PLAN-INDEX.json'))
  &&sameRef(builderProposal.historical_main12_builder_index,chromeMain12IndexRef)
  &&sameRef(builderProposal.getconf_preparation_index,getconfIndexRef)
  &&builderProposal.schema==='c17-wrapper13-dirhelper-static-proposal-v1'
  &&builderProposal.future_root===root&&builderProposal.future_root_created===false
  &&builderProposal.status==='prepared_static_pure_only_not_native_qualified'
  &&chromeProposal.preimage.sha256===chromeV10Ref.sha256
  &&chromeProposal.candidate.sha256===chromeMain11Ref.sha256
  &&chromeProposal.status==='prepared_static_only_unexecuted_profile_not_admitted',
  'Chaîne proposition Chrome non exacte ou admise');
const threeRuleSuffix=[
  '; ROOT10 diagnostic_only : refus ciblés, causalité non prouvée, profil non admis.',
  '(allow mach-lookup (global-name "com.apple.CARenderServer"))',
  '(allow iokit-open-user-client (iokit-user-client-class "IOSurfaceRootUserClient"))',
  '(allow iokit-open-user-client (iokit-user-client-class "AGXDeviceUserClient"))',
].join('\n')+'\n';
need(fs.readFileSync(chromeMain11Ref.path).equals(Buffer.concat([
  fs.readFileSync(chromeV10Ref.path),Buffer.from(threeRuleSuffix)])),
  'Préimage MAIN11 autre que V10 suivi des trois règles exactes');
const parentRule='(allow file-read-metadata (literal (param "AUXILIARY_PARENT")))\n';
need(fs.readFileSync(chromeMain12Ref.path).equals(Buffer.concat([
  fs.readFileSync(chromeMain11Ref.path),Buffer.from(parentRule)])),
  'Profil MAIN12 autre que MAIN11 suivi du seul parent auxiliaire metadata');
const dirhelperRule='(allow mach-lookup (global-name "com.apple.bsd.dirhelper"))\n';
need(fs.readFileSync(chromeCandidateRef.path).equals(Buffer.concat([
  fs.readFileSync(chromeMain12Ref.path),Buffer.from(dirhelperRule)]))
  &&fs.readFileSync(chromeCandidateRef.path).equals(fs.readFileSync(getconfProfileRef.path)),
  'Profil WRAPPER13 autre que MAIN12 suivi du seul lookup dirhelper exact');
const chromeCoreRows=core.copies.filter(r=>r.output.path===root+'/g1/chrome.sb');
need(chromeCoreRows.length===1
  &&chromeCoreRows[0].derivation==='pinned_chrome_ui_exact_successor'
  &&sameRef(chromeCoreRows[0].output,ref(root+'/g1/chrome.sb'))
  &&sameRef(core.chrome_profile_ref,chromeCandidateRef)
  &&sameRef(construction.chrome_profile_ref,chromeCandidateRef)
  &&sameRef(authority.chrome_profile_ref,chromeCandidateRef)
  &&ref(root+'/g1/chrome.sb').sha256===chromeCandidateRef.sha256,
  'Profil Chrome physique/core/autorité divergent');
const runtime=fs.readFileSync(root+'/g1/runtime_session.py','utf8');
const parentParam='extra.extend(["-D", "AUXILIARY_PARENT=" + str(auxiliary_parent)])';
need(runtime.split(parentParam).length===2
  &&runtime.includes('auxiliary_parent = root / "auxiliary"')
  &&runtime.includes('child_path(root, auxiliary_parent) == auxiliary_parent'),
  'Paramètre G1 du parent auxiliaire Chrome absent ou dupliqué');
need(sameRef(construction.builder_ref,builderRef),'Builder autre que WRAPPER13');
need(sameRef(authority.builder_index_ref,historicalBuilderIndexRef)
  &&sameRef(authority.builder_proposal_index_ref,builderProposalIndexRef)
  &&sameRef(authority.builder_ref,builderRef)
  &&authority.repo_head_observed==='d1486c2ad1d1879b1c10196fe269e16b35b85e6e'
  &&authority.historical_source_WRAPPER_only_not_current_FULL===true,'Autorité V10 ou périmètre historique divergent');
const diagnostic='/private/tmp/therese-c17-rpc-cause-observability-NRYrmF';
const diagnosticIndex=ref(diagnostic+'/INDEX.json'),diagnosticOrigins=ref(diagnostic+'/ORIGINS.json');
need(diagnosticIndex.sha256==='604e4e02062dd37cafbf9e67b2545b7697bad70a7aeac2825598cefaa63d7596'
  &&diagnosticOrigins.sha256==='6b1a49683e195f6f35d7456027ca3b03d0d6956c3d220eb3f9b7db94c4ab4846'
  &&sameRef(construction.rpc_diagnostic_origin_index_ref,diagnosticIndex)
  &&sameRef(core.diagnostic_origin_ref,diagnosticOrigins)
  &&sameRef(authority.rpc_diagnostic_index_ref,diagnosticIndex)
  &&sameRef(authority.rpc_diagnostic_origins_ref,diagnosticOrigins),
  'Gel/origines diagnostic non joints');
const origins=read(diagnosticOrigins.path),diagnosticNames=['rpc_protocol.py','rpc_client.py','rpc_dispatcher.py','session_rpc_adapter.py'];
need(origins.scope==='WRAPPER_ROOT9_transport_diagnostic_only'
  &&origins.no_AB_composite_used===true&&origins.origin_byte_exact.length===4
  &&origins.static_diff_reconstruction.length===4,'Quatre origines diagnostic absentes');
const proofRows=construction.rpc_diagnostic_derivation_refs;
need(Array.isArray(proofRows)&&proofRows.length===8,'Huit préimages/diffs diagnostic non copiés');
for(const name of diagnosticNames){
  const origin=origins.origin_byte_exact.find(r=>r.candidate.path===diagnostic+'/source/'+name);
  need(origin&&ref(origin.baseline.path).sha256===origin.baseline.sha256
    &&ref(origin.ROOT9.path).sha256===origin.ROOT9.sha256
    &&ref(origin.preimage.path).sha256===origin.preimage.sha256
    &&ref(origin.candidate.path).sha256===origin.candidate.sha256
    &&new Set([origin.baseline.sha256,origin.ROOT9.sha256,origin.preimage.sha256]).size===1,
    'Préimage/ROOT9/candidat diagnostic divergents '+name);
  const diff=origins.static_diff_reconstruction.find(r=>r.path===diagnostic+'/diffs/'+name+'.diff');
  need(diff&&sameRef(ref(diff.path),diff),'Diff diagnostic non épinglé '+name);
  const row=core.copies.find(r=>r.output.path===root+'/source/'+name);
  need(row&&row.derivation==='diagnostic_only_exact_delta'
    &&sameRef(row.input,origin.baseline)
    &&sameRef(row.preimage_ref,origin.preimage)
    &&sameRef(row.candidate_source_ref,origin.candidate)
    &&sameRef(row.diagnostic_diff_ref,diff)
    &&row.output.sha256===origin.candidate.sha256
    &&sameRef(ref(row.output.path),row.output),
    'Source active diagnostic non reliée '+name);
  for(const [kind,expected] of [['preimage',origin.preimage],['diff',diff]]){
    const suffix=kind==='diff'?name+'.diff':name;
    const dest=root+'/proofs/rpc-diagnostic-'+kind+'/'+suffix;
    const proof=proofRows.find(r=>r.output.path===dest);
    need(proof&&sameRef(proof.origin,expected)
      &&proof.output.sha256===expected.sha256
      &&sameRef(ref(dest),proof.output),
      'Preuve brute diagnostic non copiée '+kind+'/'+name);
  }
}
const helperSource=ref(diagnostic+'/source/rpc_diagnostics.py');
need(helperSource.sha256==='ae86d9b538429ca2f168cc386ea7a6e4d05ddad4e8b9f926a29dfbb4f5533058'
  &&helperSource.bytes===6826
  &&sameRef(authority.rpc_diagnostic_helper_ref,helperSource),
  'Helper diagnostic externe non exact');
const helperPureRef=ref('/private/tmp/therese-c17-rpc-cause-pure-root-tLe4Fm0P/receipt.json');
const helperPure=read(helperPureRef.path);
need(helperPureRef.sha256==='e54ec67ce25f22ff88468a9eae2cf9fd7fdaf4e460b3de3057160b264bd75855'
  &&helperPureRef.bytes===11392
  &&sameRef(authority.rpc_diagnostic_pure_receipt_ref,helperPureRef)
  &&helperPure.schema==='c17-root-rpc-exception-observability-pure-tests-v1'
  &&helperPure.tests_run===34&&helperPure.passed===true
  &&helperPure.failures===0&&helperPure.errors===0&&helperPure.skips===0
  &&helperPure.native_executed===false&&helperPure.runtime_admission===false
  &&helperPure.G1_imported===false&&helperPure.FULL===false,
  'Reçu pur diagnostic34 différent ou promu en qualification OS');
const helperPaths=[root+'/source/rpc_diagnostics.py',
  root+'/auxiliary-ports/runtime/rpc_diagnostics.py',
  root+'/auxiliary-ports/complements/instruments/rpc_diagnostics.py'];
for(const p of helperPaths)need(sameRef(ref(p),table.source_refs.find(r=>r.path===p))
  &&ref(p).sha256===helperSource.sha256,'Helper physique absent/muté '+p);
const helperCore=core.copies.find(r=>r.output.path===helperPaths[0]);
need(helperCore?.derivation==='diagnostic_helper_byte_exact'
  &&sameRef(helperCore.input,helperSource)
  &&sameRef(helperCore.output,ref(helperPaths[0])),
  'Helper core18 non lié');
const overlay=read(construction.overlay28_ref.path);
need(overlay.script_outputs&&Object.keys(overlay.script_outputs).length===19
  &&overlay.diagnostic_derivations.length===4
  &&sameRef(overlay.diagnostic_origin_index_ref,diagnosticIndex),
  'Overlay28 diagnostic incomplet');
for(const folder of ['runtime','complements/instruments'])for(const name of diagnosticNames.slice(0,2)){
  const p=root+'/auxiliary-ports/'+folder+'/'+name;
  const origin=origins.origin_byte_exact.find(r=>r.candidate.path===diagnostic+'/source/'+name);
  const deriv=overlay.diagnostic_derivations.find(r=>r.new_output.path===p);
  need(deriv&&sameRef(deriv.old_output,origin.preimage)
    &&sameRef(deriv.candidate_source,origin.candidate)
    &&sameRef(deriv.new_output,ref(p))
    &&sameRef(overlay.script_outputs[folder+'/'+name],deriv.new_output),
    'Overlay diagnostic non relié '+p);
}
const helper=core.copies.filter(r=>r.output.path===root+'/source/chrome_contract.py');
need(helper.length===1&&helper[0].derivation==='CHROME_QA_exact_constant_only'
  &&helper[0].input.sha256==='26e8374a23b7f67a5c45cbc457156bfd15735cd2578ca0fd7990b3df989630db'
  &&helper[0].output.sha256==='7922a13bdc239338ea9dedf37bf06ef1c91931b77a5275a2db6007d89a9a42ba'
  &&helper[0].derivation_source_ref.sha256===helper[0].output.sha256
  &&JSON.stringify(helper[0].derivation_diff_ref)===JSON.stringify(construction.chrome_contract_delta_ref),'Helper QA non lié exactement');
need(JSON.stringify(construction.chrome_contract_qa_ref)===JSON.stringify(helper[0].output)
  &&table.source_refs.some(r=>JSON.stringify(r)===JSON.stringify(helper[0].output)),'Helper QA absent des79');
const copyProof=construction.chrome_qa_copy_ref;
need(copyProof.sha256==='f97793cb43454051da734685185cb5d4e5b5ffbabc516580287195ef3d32993c'&&copyProof.bytes===17160,'Autre reçu copie Chrome');
const observations=[construction.chrome_copy_fresh_before_ref,construction.chrome_copy_fresh_after_ref].map(r=>read(r.path));
for(const o of observations)need(o.schema==='c17-chrome-copy-fresh-filesystem-observation-v1'
  &&o.source==='/Applications/Google Chrome.app'&&o.target==='/private/tmp/therese-c17-chrome-qa-copy-RoZmwsja/Google Chrome.app'
  &&o.entries===1339&&o.types.file===697&&o.types.directory===635&&o.types.symlink===7
  &&o.source_manifest_equal===true&&o.copy_manifest_equal===true&&o.all_bytes_modes_UID_GID_links_equal===true
  &&o.source_and_copy_inodes_match_archived_snapshots===true&&o.no_hardlinks_to_source===true
  &&o.codesign_reexecuted===false&&o.xattrs_currently_measured===false&&o.runtime_qualified===false
  &&JSON.stringify(o.root_copy_receipt_ref)===JSON.stringify(copyProof),'Observation physique Chrome invalide');
need(observations[0].source_snapshot_sha256===observations[1].source_snapshot_sha256
  &&observations[0].copy_snapshot_sha256===observations[1].copy_snapshot_sha256
  &&Date.parse(observations[0].observed_at_utc)<=Date.parse(observations[1].observed_at_utc),'Observations Chrome discordantes');
const go=read(construction.root_go_ref.path),auxiliary=read(go.auxiliary_ref.path);
need(sameRef(go.chrome_profile_origin_ref,chromeCandidateRef)
  &&sameRef(go.chrome_profile_ref,ref(root+'/g1/chrome.sb')),
  'GO Chrome non relié à la proposition exacte');
for(const key of ['chrome_contract_qa_ref','chrome_contract_delta_ref','chrome_copy_fresh_before_ref','chrome_copy_fresh_after_ref','chrome_qa_copy_ref'])
  need(JSON.stringify(go[key])===JSON.stringify(construction[key]),'GO non joint '+key);
const executable='/private/tmp/therese-c17-chrome-qa-copy-RoZmwsja/Google Chrome.app/Contents/MacOS/Google Chrome';
need(Object.keys(auxiliary.auxiliary_descriptors).length===5,'Chrome jobs autre que5');
for(const row of Object.values(auxiliary.auxiliary_descriptors)){
  const defaults=read(row.launch_defaults_ref.path);
  need(row.executable===executable&&row.argv[0]===executable&&defaults.executable===executable
    &&JSON.stringify(defaults.argv)===JSON.stringify(row.argv)&&row.port===17594
    &&row.profile.startsWith(root+'/auxiliary/'),'Descripteur/defaults Chrome divergents');
}
const sql=read(construction.sql_contract_ref.path);
need(sql.head===head&&sql.round_id===path.basename(root)&&sql.root_reviewed===false&&sql.root_review_required===true,'Contrat SQL incorrect');
const historical=read(sql.historical_contract_definition.path);
need(JSON.stringify(Object.keys(sql.relations).sort())==='["B1753","B1760"]','Groupes SQL différents');
for(const n of ['B1753','B1760'])need(JSON.stringify(sql.relations[n])===JSON.stringify(historical.relations[n]),'Relations historiques SQL réécrites '+n);
need(Object.keys(sql.source_snapshot).length===36,'SQL sources36 absentes');
for(const [n,s] of Object.entries(sql.source_snapshot))need(ref(qa+'/'+n).sha256===s,'Source SQL changée '+n);
collect(sql);
const manifestPath='/private/tmp/therese-c17-wrapper-source-kGvU1hdx/proofs/qa-source-files.json';
need(ref(manifestPath).sha256==='0904574e2b35b523b8454b33156f595f05a62e21609453a65db59ae516423b89','Manifest QA différent');
const manifest=read(manifestPath);
need(manifest.head===head&&manifest.files.length===3579&&manifest.symlinks.length===0,'Tree3579/symlinks');
need(fs.readFileSync(qa+'/.git/HEAD','utf8').trim()===head,'HEAD physique différent');
for(const r of manifest.files){
  const a=ref(r.path),raw=fs.readFileSync(r.path),n=r.path.slice(qa.length+1),mode=manifest.modes[r.path];
  need(a.sha256===r.sha256&&a.bytes===r.bytes,'Blob physique changé '+n);
  need(crypto.createHash('sha1').update(Buffer.concat([Buffer.from('blob '+raw.length+'\0'),raw])).digest('hex')===r.git_blob,'Git blob différent '+n);
  need(['100644','100755'].includes(mode)&&((fs.statSync(r.path).mode&0o111)!==0)===(mode==='100755'),'Mode Git différent '+n);
}
for(let i=0;i<pending.length;i++){
  need(pending.length<6000,'Références hors borne');
  const r=pending[i],a=ref(r.path);need(a.sha256===r.sha256&&(r.bytes===undefined||a.bytes===r.bytes),'Ref changée '+r.path);
  if(r.path.endsWith('.json')&&r.path!==sql.historical_contract_definition.path)collect(read(r.path),r.path);
}
for(const name of ['binding.json','decision.json','runtime/readiness.json','runtime/pile-reprise.json','runtime/services-running.json','wrapper-canary-result.json'])need(!fs.existsSync(root+'/'+name),'État natif prématuré '+name);
need(ref(root+'/g1/web.sb').sha256==='51ff2e21500393704ea8709fb9bd177dc1f88793d1e92d09c68be70d905807ff'
  &&ref(root+'/g1/chrome.sb').sha256==='2ecae3a24ec871a44827b3f712ced1ef5e84d8f778906c37b3a5b51bb374dcdf','Profils autres successeurs');
console.log(JSON.stringify({status:'prepared_only_static_verified',root,refs:refs.size,historical_observations:historicalObservations,sources:79,core_copies:18,overlay_outputs:28,diagnostic_origins:4,diagnostic_helpers:3,git_tree_files:3579,git_modes:true,git_blobs:true,SQL_sources:36,SQL_relations_unchanged:true,original11:true,deltas:6,witness_copies:7,native:false,FULL:false,release:false}));
