// Préparé pour un rejeu ultérieur, NON exécuté dans ce lot.
// Aucun import de G1, lsof, navigateur, socket ou source produit.
export async function runPure({ownershipSource,traceSource,coverageSource,auxiliarySource}) {
  const cases=[];
  const check=(condition,message)=>{if(!condition)throw new Error(message);};
  const run=async(name,body)=>{
    try {await body();cases.push({name,passed:true});}
    catch(error){cases.push({name,passed:false,error:String(error)});}
  };
  const slice=(source,start,end)=>{
    check(source.split(start).length===2&&source.split(end).length===2,'Ancres JS uniques');
    return source.slice(source.indexOf(start),source.indexOf(end));
  };

  await run('ownership_api_refuse_port_tiers_et_delegue',async()=>{
    const body=ownershipSource.replace(/^import .*;\n/m,'').replace('export async function','async function');
    const calls=[];
    const verifier=new Function('requestOwnedListener',body+';return verifierListenerPossede;')
      (async port=>{calls.push(port);});
    await verifier(17593);
    check(calls.length===1&&calls[0]===17593,'Rendez-vous parent absent');
    let refused=false;
    try {await verifier(17293);} catch {refused=true;}
    check(refused&&calls.length===1,'Port réel envoyé au parent');
  });

  await run('fetch_node_attend_observation_avant_emission',async()=>{
    const body=slice(traceSource,'const directFetchStages=','const originalLaunch=');
    let release,emissions=0,observations=0;
    const pending=new Promise(resolve=>{release=resolve;});
    const globalDouble={fetch:async()=>{emissions++;return {ok:true};}};
    new Function('process','globalThis','requestOwnedListener','URL',body)
      ({env:{C17_SESSION_STAGE:'coverage'}},globalDouble,async()=>{observations++;await pending;},URL);
    const fetchPending=globalDouble.fetch('http://127.0.0.1:17593/__couverture/offline');
    check(observations===1&&emissions===0,'Fetch émis avant observation');
    release();await fetchPending;
    check(emissions===1,'Fetch non repris après owned');
  });

  await run('fetch_node_refus_tiers_ou_birth_ne_transmet_rien',async()=>{
    const body=slice(traceSource,'const directFetchStages=','const originalLaunch=');
    let emissions=0,observations=0;
    const globalDouble={fetch:async()=>{emissions++;}};
    new Function('process','globalThis','requestOwnedListener','URL',body)
      ({env:{C17_SESSION_STAGE:'recipe-general'}},globalDouble,async()=>{observations++;throw new Error('birth diverge');},URL);
    for(const url of ['http://127.0.0.1:17593/api/auth/token','http://127.0.0.1:17293/api/auth/token']){
      let refused=false;try{await globalDouble.fetch(url);}catch{refused=true;}
      check(refused,'Fetch hors preuve accepté');
    }
    check(emissions===0&&observations===1,'Émission ou scan du port réel');
  });

  await run('route_http_ws_attendent_observation',async()=>{
    const body=slice(coverageSource,'export function installerGardeReseau','\nfunction idDAnomalie').replace('export function','function');
    let owner=async()=>{},emissions=0,aborts=0,closes=0;
    const routes={};
    const contexte={route:async(_,handler)=>{routes.http=handler;},routeWebSocket:async(_,handler)=>{routes.ws=handler;}};
    const guard={bloquees:[],websockets_bloques:[],portReel:false};
    const allowed=(method,url)=>method==='GET'&&url==='http://127.0.0.1:5173/';
    const installer=new Function('requestOwnedListener','requeteAutorisee','adresseSansSecrets','PORT_REEL',
      body+';return installerGardeReseau;')
      (port=>owner(port),allowed,url=>url,17293);
    await installer(contexte,guard);
    const http={request:()=>({method:()=> 'GET',url:()=> 'http://127.0.0.1:5173/'}),
      continue:async()=>{emissions++;},abort:async()=>{aborts++;}};
    const ws={url:()=> 'ws://127.0.0.1:5173/',connectToServer:async()=>{emissions++;},close:async()=>{closes++;}};
    owner=async()=>{throw new Error('foreign listener');};
    await routes.http(http);await routes.ws(ws);
    check(emissions===0&&aborts===1&&closes===1&&guard.bloquees.length===1&&guard.websockets_bloques.length===1,
      'Refus parent transmis au navigateur');
    owner=async port=>{check([5173].includes(port),'Port hors QA');};
    await routes.http(http);await routes.ws(ws);
    check(emissions===2,'Routes owned non continuées');
  });

  const constants=slice(auxiliarySource,'export const JOBS','export function regular').replace(/^export /gm,'');
  const create=slice(auxiliarySource,'export function createAuxiliary','\nlet auxiliary;').replace(/^export /gm,'');
  const make=new Function('process','createHash','randomUUID','published','publish','reference','checked',
    constants+create+';return createAuxiliary;');
  const birth={pid:901,ppid:800,uid:501,pgid:901,birth_sec:1,birth_usec:2};
  const root='/private/tmp/therese-c17-direct-round-a-123456789abc';
  const base={scope:'runtime78_exact_round',stage:'coverage',root,actor:'/root',
    round_id:'c17-direct-round-a-123456789abc',head:'a'.repeat(40),decision_id:'pure-only',
    binding_sha256:'b'.repeat(64),services:{backend:{port:17593,birth_identity:birth}}};
  const makeCase=(mutate=observation=>observation)=>{
    let nonce=0,publishedCount=0,request,requestRef;
    const ref=path=>({path,sha256:'0'.repeat(64),bytes:1});
    const factory=make({hrtime:{bigint:()=>1000000000n}},()=>{},()=>String(++nonce).padStart(32,'0'),
      ()=>{},()=>{},ref,()=>{});
    const auxiliary=factory(base,{clock:()=>0,wallClock:()=>1700000000,pause:async()=>{},
      referenceOf:ref,publishNew:(path,value)=>{publishedCount++;request=value;requestRef=ref(path);return requestRef;},
      readPublished:()=>({schema:'c17-runtime78-owned-listener-response-v1',status:'owned',request:requestRef,
        observation:ref(root+'/observation.json'),actor:base.actor,round_id:base.round_id,head:base.head,
        qa_root:root,stage:base.stage,port:request.port}),
      checkedRef:()=>JSON.stringify(mutate({schema:'c17-runtime78-owned-listener-observation-v1',status:'owned',
        actor:base.actor,round_id:base.round_id,head:base.head,qa_root:root,stage:base.stage,port:17593,
        journal:root+'/ownership-traces.jsonl',root_identity:birth,pid:901,identity:birth,
        scans:[{pids:[901]},{pids:[901]}]})),});
    return {auxiliary,count:()=>publishedCount};
  };
  await run('concurrents_un_scan_en_vol_sequentiels_deux_scans_frais',async()=>{
    const item=makeCase();
    await Promise.all([item.auxiliary.listener(17593),item.auxiliary.listener(17593)]);
    check(item.count()===1,'Concurrents non coalescés');
    await item.auxiliary.listener(17593);
    check(item.count()===2,'TTL/cache inter-requêtes interdit');
  });
  await run('observation_tiers_ou_birth_divergente_refusee',async()=>{
    for(const mutate of [x=>({...x,pid:902}),x=>({...x,root_identity:{...birth,birth_usec:3}}),x=>({...x,status:'absent'})]){
      const item=makeCase(mutate);let refused=false;
      try{await item.auxiliary.listener(17593);}catch{refused=true;}
      check(refused&&item.count()===1,'Observation étrangère acceptée');
    }
  });
  return {schema:'c17-ab-listener-port-pure-v1',status:cases.every(c=>c.passed)?'pass':'fail',cases};
}
