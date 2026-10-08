/** Préparation seulement. Ce module ne sera importé que par un lancement relu root. */
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {existsSync,mkdirSync,readFileSync,realpathSync,writeFileSync} from 'node:fs';
import {dirname,resolve,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
const here=dirname(fileURLToPath(import.meta.url));
const preparation=resolve(here,'../contrats-normalises-proposes.json');
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const repo='/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE-c15-codex';
let context;
export function preparerContexte(group){
  if(context){assert.equal(context.group,group);return context;}
  // Root fournit le SHA de la définition après sa lecture. Cela empêche un
  // lancement accidentel, sans prétendre authentifier root par une chaîne.
  const bytes=readFileSync(preparation), contract=JSON.parse(bytes);
  assert.equal(process.env.C16_REVIEWED_SHA256,hash(bytes),'revue root du contrat exact requise');
  assert(contract.groups.includes(group));
  const actor=process.env.C16_ACTOR, round=process.env.C16_ROUND_ID;
  const registryBytes=readFileSync(resolve(repo,contract.identity_registry.path));
  assert.equal(hash(registryBytes),contract.identity_registry.sha256,'registre réel modifié');
  const registry=JSON.parse(registryBytes);
  assert(registry.actors.some(a=>a.actor===actor),'acteur réel enregistré requis');
  assert(round&&/^[a-zA-Z0-9._-]+$/.test(round),'identité de ronde explicite requise');
  const head=()=>execFileSync('git',['rev-parse','HEAD'],{cwd:repo,encoding:'utf8'}).trim();
  assert.equal(head(),contract.head,'préparation périmée');
  const stackPath=resolve(repo,contract.runtime_manifest.path);
  assert.equal(hash(readFileSync(stackPath)),contract.runtime_manifest.sha256,'manifeste runtime modifié : nouvelle revue nécessaire');
  const stack=JSON.parse(readFileSync(stackPath));
  assert.equal(stack.cycle,17);assert.equal(stack.status,'running');
  assert.equal(stack.repo,repo);assert.equal(stack.head_at_start,contract.head);
  assert.equal(stack.backend.host,'127.0.0.1');assert.equal(stack.backend.port,17593);
  assert.equal(stack.vite.host,'127.0.0.1');assert.equal(stack.vite.port,5173);
  const privateRoot=realpathSync('/private/tmp');
  const temporaryRoot=realpathSync(stack.temporary_root);
  assert(temporaryRoot.startsWith(privateRoot+sep));
  for(const key of ['home','data_dir'])assert(realpathSync(stack[key]).startsWith(temporaryRoot+sep));
  assert.equal(realpathSync(process.env.HOME),realpathSync(stack.home),'HOME privé du runtime requis');
  const helper=resolve(repo,contract.helper_v3.path);
  assert.equal(hash(readFileSync(helper)),contract.helper_v3.sha256);
  const snapshot={};
  for(const [file,expected]of Object.entries(contract.source_snapshot)){
    const current=hash(readFileSync(resolve(repo,file)));assert.equal(current,expected,file);snapshot[file]=current;
  }
  const out=resolve(process.env.C16_OUT??'');
  const evidenceRoot=resolve(here,'../runs');mkdirSync(evidenceRoot,{recursive:true});
  assert(process.env.C16_OUT&&out.startsWith(evidenceRoot+sep),'sortie16 explicite requise');
  assert(!existsSync(out),'sortie neuve obligatoire, aucun reçu antérieur écrasé');mkdirSync(out,{recursive:true});
  assert(realpathSync(out).startsWith(realpathSync(evidenceRoot)+sep));
  const metadata={cycle:17,runtime_revision:'v3',actor,round_id:round,head:contract.head,
    group,prepared_by:contract.prepared_by,contract_sha256:hash(bytes),
    started_at:new Date().toISOString(),source_snapshot:snapshot,
    helper:{path:contract.helper_v3.path,sha256:contract.helper_v3.sha256},
    runtime_manifest:contract.runtime_manifest,identity_registry:contract.identity_registry,home:stack.home,data_dir:stack.data_dir,
    expected_front:'http://127.0.0.1:5173/?port=17593',expected_backend:'http://127.0.0.1:17593',
    browser_kind:'Google_Chrome_macOS_headed_sandbox',plateau_accepted:false,
    database_scope:'runtime-v3 SQLite plaintext; aucune attestation SQLCipher par ce parcours'};
  const logPath=stack.backend.log, logOffset=readFileSync(logPath).length;
  const guard={revision:'v3',node_requests:[],blocked:[],real_profile_access:false,real_port_access:false};
  const fetchOriginal=globalThis.fetch;
  let verifierListener;
  const ownershipReady=import(new URL('./ownership-only.mjs',import.meta.url).href).then(module=>{verifierListener=module.verifierListenerPossede;});
  globalThis.fetch=async(input,options={})=>{
    const address=typeof input==='string'||input instanceof URL?String(input):input.url;
    const method=(options.method??input.method??'GET').toUpperCase();
    const u=new URL(address);
    const local=u.protocol==='http:'&&u.hostname==='127.0.0.1'&&['http://127.0.0.1:5173','http://127.0.0.1:17593'].includes(u.origin)&&!u.username&&!u.password&&!u.hash;
    const excluded=/\/(?:auth\/callback|sync\/callback)|\/api\/crm\/google-sheets\/|\/models\/openrouter/.test(u.pathname);
    const safeRead=['GET','HEAD','OPTIONS'].includes(method);
    const permittedWrite=group==='P160'&&u.origin==='http://127.0.0.1:17593'&&!u.search&&
      ((method==='POST'&&['/api/crm/contacts','/api/invoices'].includes(u.pathname))||
       (method==='PUT'&&/^\/api\/invoices\/[^/]+$/.test(u.pathname)));
    if(!(local&&!excluded&&(safeRead||permittedWrite))){
      guard.blocked.push({method,url:u.origin+u.pathname});guard.real_port_access||=u.port==='17293';
      throw new Error('Requête Node hors périmètre borné');
    }
    guard.node_requests.push({method,url:u.origin+u.pathname});
    await ownershipReady;
    await verifierListener(Number(u.port));
    return fetchOriginal(input,{...options,redirect:'error',signal:options.signal??AbortSignal.timeout(10000)});
  };
  process.once('exit',()=>{
    const after={};for(const file of Object.keys(snapshot))after[file]=hash(readFileSync(resolve(repo,file)));
    const log=readFileSync(logPath);assert(log.length>=logOffset,'journal tronqué pendant le parcours');
    const delta=log.subarray(logOffset).toString('utf8');
    writeFileSync(resolve(out,'backend-delta.log'),delta);
    const errors=delta.split('\n').filter(l=>/\bERROR\b|Traceback \(most recent call last\)|\bException\b/.test(l));
    const receipt={...metadata,completed_at:new Date().toISOString(),head_after:head(),source_snapshot_after:after,
      sources_unchanged:Object.entries(snapshot).every(([p,d])=>after[p]===d),guard,
      backend_errors:errors,backend_log_scope:{path:logPath,start_byte:logOffset,end_byte:log.length,delta_sha256:hash(Buffer.from(delta))},
      instrumentation_limit:'Extraction de lignes candidates, pas remplacement du lecteur/calibrateur de logs. HEAD/SHA des fichiers ne prouvent pas seuls les modules chargés par le serveur.',
      process_exit_code:process.exitCode??0,plateau_accepted:false};
    writeFileSync(resolve(out,'contexte-execution.json'),JSON.stringify(receipt,null,2)+'\n');
    if(!receipt.sources_unchanged||receipt.head_after!==receipt.head||errors.length||guard.blocked.length)process.exitCode=1;
  });
  context={group,repo,out,stack,helper,metadata};return context;
}
