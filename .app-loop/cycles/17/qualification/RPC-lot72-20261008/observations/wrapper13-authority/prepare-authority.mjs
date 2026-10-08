// Préparation neuve ; seul l'appel outil MAIN exact autorise la construction.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
const out = '/private/tmp/therese-c17-root-fresh13-controls-qRMkWUPg';
const root = '/private/tmp/therese-c17-wrapper-canary-8612f55886284332a3ac6a7bc9615021';
const repo = '/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE-c15-codex';
const currentHead = 'd1486c2ad1d1879b1c10196fe269e16b35b85e6e';
const head = '2d69e30c9c6dd18823ee6102271876003a6a67cc';
const gel = '/private/tmp/therese-c17-wrapper13-dirhelper-P5WQpQ';
const need = (value, why) => {if (!value) throw new Error(why);};
function ref(p) {
  const before = fs.lstatSync(p);
  need(before.isFile() && !before.isSymbolicLink() && fs.realpathSync(p) === p
    && before.uid === process.getuid() && before.nlink === 1, `Noncanonical input: ${p}`);
  const bytes = fs.readFileSync(p), after = fs.lstatSync(p);
  need(before.ino === after.ino && before.dev === after.dev && before.size === after.size
    && before.mtimeMs === after.mtimeMs && before.ctimeMs === after.ctimeMs, `Changing input: ${p}`);
  return {path:p, sha256:crypto.createHash('sha256').update(bytes).digest('hex'), bytes:bytes.length};
}
function checked(r) {
  const actual = ref(r.path);
  need(JSON.stringify(actual) === JSON.stringify({path:r.path, sha256:r.sha256, bytes:r.bytes}), `Changed pin: ${r.path}`);
  return actual;
}
need(!fs.existsSync(root) && fs.realpathSync(out) === out && fs.lstatSync(out).uid === process.getuid()
  && (fs.lstatSync(out).mode & 0o077) === 0 && fs.readdirSync(out).join(',') === 'prepare-authority.mjs',
  'Private unused control directory and absent QA root required');
need(execFileSync('/Applications/Xcode.app/Contents/Developer/usr/bin/git', ['rev-parse','HEAD'],
  {cwd:repo, encoding:'utf8'}).trim() === currentHead, 'Current repository HEAD changed');
const template = checked({path:'/private/tmp/therese-c17-root-fresh11-controls-5eCuk7hB/prepare-go.json',
  sha256:'17382f10805491b8e73401533392e377ef204309fc6ea971f1196ecdb0e40c9f', bytes:5071});
const body = JSON.parse(fs.readFileSync(template.path,'utf8'));
need(body.scope === 'WRAPPER_CANARY' && body.head === head && body.FULL === false && body.release === false,
  'Historical template is source only, not inherited authority');
const proposal = checked({path:gel+'/PLAN-INDEX.json',
  sha256:'0956da6b74598f64639c4dd491cdaf21378247b14316a5ac7e2084cd018529e9', bytes:4918});
const plan = JSON.parse(fs.readFileSync(proposal.path,'utf8'));
need(plan.future_root === root && plan.future_root_created === false && plan.pure_tests.tests === 10
  && plan.pure_tests.exit_code === 0 && plan.delta.CDP_seconds_unchanged === 5
  && plan.delta.Chrome_startup_seconds_unchanged === 50 && plan.delta.cleanup_seconds_unchanged === 8,
  'Unexpected WRAPPER13 scope');
for (const row of plan.refs) checked(row);
const chrome = checked(plan.candidate_chrome_profile), builder = checked(plan.candidate_builder);
const reviewRef = JSON.parse(process.argv[2] ?? 'null');
need(reviewRef && typeof reviewRef.path === 'string', 'Actual independent review pin required');
const review = checked(reviewRef);
const runner = checked(body.runner_boundary_index_ref);
for (const [name,value] of Object.entries(body)) {
  if (name.endsWith('_ref') && value && name !== 'identity_registry_ref'
      && name !== 'independent_static_review_ref' && name !== 'preparation_script_ref') checked(value);
}
const save = (name,value) => {
  fs.writeFileSync(out+'/'+name, JSON.stringify(value,null,2)+'\n', {flag:'wx', mode:0o600});
  return ref(out+'/'+name);
};
const registry = save('identity-registry.json', {
  schema:'c17-wrapper-canary-live-identity-registry-v1', round_id:root.split('/').at(-1), head,
  repo_head_observed:currentHead, historical_product_source_instrument_only:true,
  chrome_profile_ref:chrome, runner_boundary_index_ref:runner,
  actors:[{actor:'/root', observed_by:'Actual collaboration.list_agents immediately before this MAIN preparation',
    observed_at_utc:new Date().toISOString(), role:'Root orchestrateur ; aucun PID futur ou reviewer historique relabellé'}],
  OS_qualified:false, FULL:false, release:false,
});
Object.assign(body, {
  root, repo_head_observed:currentHead, builder_ref:builder, chrome_profile_ref:chrome,
  builder_proposal_index_ref:proposal, identity_registry_ref:registry,
  profile_derivation_pure_ref:checked({path:gel+'/proofs/pure-tests-returned.log',
    sha256:'bb83fcc74bdc1ec7fb586466a75e7350fbddb4d4702c29c36d66aeb885f4e806', bytes:1477}),
  profile_derivation_pure_ref_is_transcription_not_raw:true,
  independent_MAIN_pure_test_observation:{tool_chunk:'1c8b53', tests:10, exit_code:0,
    G1_imported:false, native_executed:false, output_not_fabricated_or_written_here:true},
  independent_static_review_ref:review, preparation_script_ref:ref(out+'/prepare-authority.mjs'),
  historical_template_ref:template, historical_template_not_authority:true,
});
const authority = save('prepare-go.json',body);
console.log(JSON.stringify({root, registry_ref:registry, authority_ref:authority,
  prepared_only:true, native:false, FULL:false, release:false}));
