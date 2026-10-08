// Préparation documentaire. Le GO effectif reste l'appel externe du constructeur.
import fs from 'node:fs';
import crypto from 'node:crypto';
const out='/private/tmp/therese-c17-root-fresh10-authority-5v3bqKwd';
const root='/private/tmp/therese-c17-wrapper-canary-b90937dbae4845ca9d04b93aa4cdf9aa';
const currentHead='19979e8a5ea9bd8e886d35d54793b3d1a560cd77';
const head='2d69e30c9c6dd18823ee6102271876003a6a67cc';
const need=(x,m)=>{if(!x)throw Error(m);};
need(fs.realpathSync(out)===out&&fs.lstatSync(out).uid===process.getuid()
  &&(fs.lstatSync(out).mode&0o077)===0
  &&fs.readdirSync(out).sort().join(',')==='INDEX.json,README.md,V10-REVIEW-OBSERVATION.md,diffs,preimages,prepare-authority.mjs,verify-prepared-wrapper.mjs'
  &&!fs.existsSync(root),'Autorité privée neuve et future racine absente requises');
const ref=p=>{
  const s=fs.lstatSync(p),b=fs.readFileSync(p);
  need(s.isFile()&&!s.isSymbolicLink()&&fs.realpathSync(p)===p&&s.uid===process.getuid(),'Ref non canonique '+p);
  return {path:p,sha256:crypto.createHash('sha256').update(b).digest('hex'),bytes:b.length};
};
const checked=(p,sha,bytes)=>{
  const r=ref(p);need(r.sha256===sha&&r.bytes===bytes,'Entrée divergente '+p);return r;
};
const save=(n,j)=>{fs.writeFileSync(out+'/'+n,JSON.stringify(j,null,2)+'\n',{flag:'wx',mode:0o600});return ref(out+'/'+n);};
const chrome=checked('/private/tmp/therese-c17-fresh-wrapper-builder-v10-ynPAzC/profile/chrome.sb',
  '19808ee2cac3169e9fb8c71c24385bcbb97f924c5ed785f4651817ecaa179b0c',2067);
const runner=checked('/private/tmp/therese-c17-test-runner-boundary-eUIHsp/INDEX.json',
  '771565210b1ab41ca7e5a43c89fa63a034c57872515a698a12161e47adfe11b7',5567);
const registry=save('identity-registry.json',{
  schema:'c17-wrapper-canary-live-identity-registry-v1',round_id:root.split('/').at(-1),head,
  repo_head_observed:currentHead,historical_product_source_instrument_only:true,chrome_profile_ref:chrome,
  runner_boundary_index_ref:runner,actors:[{
    actor:'/root',observed_by:'Actual collaboration.list_agents: root running immediately before this preparation',
    observed_at_utc:new Date().toISOString(),role:'Root orchestrateur; aucun PID futur ou reviewer historique relabellé'
  }],OS_qualified:false,FULL:false,release:false
});
const authority=save('prepare-go.json',{
  schema:'c17-root-fresh-wrapper-preparation-go-v1',status:'go_prepare_only',scope:'WRAPPER_CANARY',actor:'/root',root,head,
  repo_head_observed:currentHead,historical_source_WRAPPER_only_not_current_FULL:true,
  product_source_root:'/private/tmp/therese-c17-wrapper-source-kGvU1hdx/source',origin_kind:'root_tool_call',
  builder_ref:checked('/private/tmp/therese-c17-fresh-wrapper-builder-v10-ynPAzC/build_fresh_wrapper.py',
    'e697ec7733e691681bb104ffee6e083a251f1779abab895e63e316bcfaf72e2f',80319),
  builder_index_ref:checked('/private/tmp/therese-c17-fresh-wrapper-builder-v10-ynPAzC/INDEX.json',
    'ad4cbc19f3c156f0b0d4ff2e3d36b31eccc9bda109cb18cc6c77194aefce1007',8012),
  web_profile_ref:checked('/private/tmp/therese-c17-web-root-metadata-POjxSafe/web.sb',
    '51ff2e21500393704ea8709fb9bd177dc1f88793d1e92d09c68be70d905807ff',1780),
  chrome_profile_ref:chrome,runner_boundary_index_ref:runner,identity_registry_ref:registry,
  gpu_observation_ref:checked('/private/tmp/therese-c17-wrapper-canary-ea92e9f2c3a9485a88dc906c302f42ff/proofs/system-profiler-displays.raw',
    '92d6e897ef52659540e9497649283da5bd4ff4c443c5d0d07f50bbb37d5bc4d0',186),
  gpu_observation_historical_only_not_native_qualification:true,
  pure_replay_ref:checked('/private/tmp/therese-c17-root-v10-71-replay-v3-zRFPBqd5/receipt.json',
    'c0864b435265a4c485c78837207184d3964e966689eb97785fe3ab4ff9e3f8e5',68793),
  chrome_qa_copy_ref:checked('/private/tmp/therese-c17-chrome-qa-copy-RoZmwsja/v3-receipt.json',
    'f97793cb43454051da734685185cb5d4e5b5ffbabc516580287195ef3d32993c',17160),
  chrome_spctl_assessment_ref:checked('/private/tmp/therese-c17-chrome-policy-assess-WyJvs5Z0/receipt.json',
    '92dbaaed5278671635b2a0d35f8cb4362ea99b589f0892a180c512fd48932c44',1346),
  root8_diagnostic_ref:checked('/private/tmp/therese-c17-root8-system-diagnostic-wFhTKOw6/receipt.json',
    'ca8b417a39d68cda55eea22694806590d2c3999eefd0b187c82654725beee05a',1403),
  rpc_diagnostic_index_ref:checked('/private/tmp/therese-c17-rpc-cause-observability-NRYrmF/INDEX.json',
    '604e4e02062dd37cafbf9e67b2545b7697bad70a7aeac2825598cefaa63d7596',6675),
  rpc_diagnostic_origins_ref:checked('/private/tmp/therese-c17-rpc-cause-observability-NRYrmF/ORIGINS.json',
    '6b1a49683e195f6f35d7456027ca3b03d0d6956c3d220eb3f9b7db94c4ab4846',6591),
  rpc_diagnostic_helper_ref:checked('/private/tmp/therese-c17-rpc-cause-observability-NRYrmF/source/rpc_diagnostics.py',
    'ae86d9b538429ca2f168cc386ea7a6e4d05ddad4e8b9f926a29dfbb4f5533058',6826),
  rpc_diagnostic_pure_receipt_ref:checked('/private/tmp/therese-c17-rpc-cause-pure-root-tLe4Fm0P/receipt.json',
    'e54ec67ce25f22ff88468a9eae2cf9fd7fdaf4e460b3de3057160b264bd75855',11392),
  independent_static_review_ref:ref(out+'/V10-REVIEW-OBSERVATION.md'),independent_static_review_received:true,
  preparation_script_ref:ref(out+'/prepare-authority.mjs'),
  authority_is_exact_next_external_preparation_tool_not_this_JSON:true,native_runtime_GO_still_required:true,FULL:false,release:false
});
console.log(JSON.stringify({root,registry_ref:registry,authority_ref:authority,prepared_only:true,native:false,FULL:false,release:false}));
