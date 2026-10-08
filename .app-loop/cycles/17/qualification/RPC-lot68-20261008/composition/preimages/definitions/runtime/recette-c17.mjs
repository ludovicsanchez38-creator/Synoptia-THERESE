// Recette UI ciblée, moteur local et jeux de données synthétiques uniquement.
import {createHash} from 'node:crypto';
import {ownedGitHead} from '../auxiliary-ports/runtime/aux_node.mjs';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {dirname,resolve} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const here=dirname(fileURLToPath(import.meta.url)),repo="/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE-c15-codex";
const manifest=JSON.parse(await readFile(resolve(here,'pile-reprise.json'),'utf8'));
const out=resolve(here,`recette-${new Date().toISOString().replaceAll(':','-').replaceAll('.','-')}`);await mkdir(out);
const {chromium}=await import(pathToFileURL(resolve(repo,'node_modules/playwright/index.mjs')).href);
const {verifierPileJetable,installerGardeReseau}=await import(pathToFileURL(resolve(here,'couverture-ecran-c16.mjs')).href);
const base='http://127.0.0.1:5173/?port=17493',back='http://127.0.0.1:17493';
const proof={head:ownedGitHead(repo),status:'running',checks:[],console_errors:[],network_errors:[],captures:[]};
let browser;
try {
 proof.stack=await verifierPileJetable(base,manifest.data_dir);
 const auth=await fetch(`${back}/api/auth/token`);const {token}=await auth.json();assert(token);
 async function api(path,body){const response=await fetch(`${back}${path}`,{method:'POST',headers:{'content-type':'application/json','X-Therese-Token':token},body:JSON.stringify(body)});assert(response.ok,`${path}: ${response.status}`);return response.json();}
 // Les identifiants du domaine sont lus dans le contrat frontend, pas inventés.
 const source=await readFile(resolve(repo,'src/frontend/src/components/crm/pipelineEtapes.ts'),'utf8');
 const tableau=source.split('export const PIPELINE_ETAPES = [')[1].split('] as const;')[0];
 const ids=[...tableau.matchAll(/id:\s*'([^']+)'/g)].map(m=>m[1]);assert(ids.length===8);
 for(const [i,stage] of ids.entries())await api('/api/crm/contacts',{first_name:`Témoin C16 ${i+1}`,company:'Entreprise synthétique',stage});
 const title='Relance du devis de la boulangerie Témoin C16, vitrine réfrigérée et planning de pose sur trois semaines';
 const conversation=await api('/api/chat/conversations',{title});
 await api('/api/chat/send',{conversation_id:conversation.id,message:'{action: ouvrir crm}',stream:false,include_memory:false});
 browser=await chromium.launch({headless: false, channel: 'chrome', chromiumSandbox: true, args: ['--disable-background-networking','--disable-component-update','--disable-sync']});proof.chromium=browser.version();
 const context=await browser.newContext({viewport:{width:800,height:900},locale:'fr-FR',timezoneId:'Europe/Paris',reducedMotion:'reduce',serviceWorkers:'block',acceptDownloads:false});
 const guard={bloquees:[],websockets_bloques:[],telechargements:[],popups:[],portReel:false};proof.guard=guard;
 await installerGardeReseau(context,guard);const page=await context.newPage();
 page.on('pageerror',e=>proof.console_errors.push(String(e)));
 page.on('console',m=>{if(m.type()==='error')proof.console_errors.push(m.text());});
 page.on('response',r=>{if(r.status()>=400)proof.network_errors.push({url:new URL(r.url()).pathname,status:r.status()});});
 await page.goto(base,{waitUntil:'networkidle'});await page.waitForFunction(()=>window.__thereseMonte&&window.__therese?.runAction);
 const shot=async name=>{const path=resolve(out,name+'.png');await page.screenshot({path,animations:'disabled'});proof.captures.push({path,sha256:createHash('sha256').update(await readFile(path)).digest('hex')});};
 await page.evaluate(()=>window.__therese.runAction('crm.open'));
 const grid=page.getByRole('region',{name:'Étapes du pipeline'});await grid.waitFor({state:'visible'});
 assert.equal(await grid.locator('[data-colonne]').count(),8);
 const right=page.getByRole('button',{name:/étapes? à droite/});await right.waitFor({state:'visible'});await shot('pipeline-800-debut');
 for(let i=0;i<10&&await right.count();i++) {await right.focus();await page.keyboard.press('Enter');await page.waitForTimeout(650);}
 assert.equal(await right.count(),0);assert(await grid.evaluate(e=>document.activeElement===e));
 proof.checks.push({name:'P157/B1742 défilement réel 800 px et focus au bord',status:'pass',geometry:await grid.evaluate(e=>({scrollLeft:e.scrollLeft,clientWidth:e.clientWidth,scrollWidth:e.scrollWidth}))});await shot('pipeline-800-fin');
 await page.setViewportSize({width:1440,height:900});await page.evaluate(()=>window.__therese.runAction('conversations.toggle'));
 const drawer=page.getByTestId('prototype-conversation-drawer');await drawer.waitFor({state:'visible'});
 const entry=drawer.getByRole('button',{name:new RegExp('Relance du devis de la boulangerie Témoin C16')}).first();await entry.waitFor({state:'visible'});await entry.focus();
 const label=entry.locator('b');assert.equal(await entry.getAttribute('title'),title);
 const css=await label.evaluate(e=>({whiteSpace:getComputedStyle(e).whiteSpace,overflow:getComputedStyle(e).overflow,text:e.textContent,height:e.getBoundingClientRect().height}));
 assert.equal(css.text,title);assert.notEqual(css.whiteSpace,'nowrap');assert(css.height>20);await shot('titre-long-focus');
 await entry.hover();assert.notEqual(await label.evaluate(e=>getComputedStyle(e).whiteSpace),'nowrap');
 proof.checks.push({name:'B1738 titre intégral au focus et survol dans le vrai tiroir',status:'pass',css,drawerWidth:await drawer.evaluate(e=>e.getBoundingClientRect().width)});
 await entry.click();await page.waitForTimeout(700);
 // Témoin de contrat UI : le calcul et la persistance HTTP du bilan sont
 // couverts séparément par les tests du moteur, sans fournisseur payant.
 await page.evaluate(async ({id,title})=>{const {useChatStore}=await import('/src/stores/chatStore.ts');useChatStore.setState({conversations:[{id,title,synced:true,createdAt:new Date(),updatedAt:new Date(),messages:[{id:'temoin-p159',role:'assistant',content:'Réponse synthétique C16.',timestamp:new Date(),contexte:{messages_relus:50,messages_transmis:30,caracteres_retires:752}}]}],currentConversationId:id});},{id:conversation.id,title});
 const bilan=page.getByText('Contexte raccourci : 30 messages sur 50. Ton message a été raccourci pour tenir dans le modèle (752 caractères retirés).',{exact:true});await bilan.waitFor({state:'visible'});await bilan.focus();assert(await bilan.evaluate(e=>document.activeElement===e));await shot('contexte-p159');
 proof.checks.push({name:'P159 rendu UI réel des deux comptes et de la coupe courante',status:'pass',limit:'Métadonnées synthétiques posées dans le store ; calcul et rechargement HTTP prouvés par la suite moteur.'});
 assert.equal(proof.console_errors.length,0);assert.equal(proof.network_errors.length,0);assert.equal(guard.bloquees.length,0);assert.equal(guard.websockets_bloques.length,0);assert(!guard.portReel);
 proof.status='passed';await context.close();
} catch(error){proof.status='failed';proof.error=String(error);} finally{if(browser)await browser.close();await writeFile(resolve(out,'recette.json'),JSON.stringify(proof,null,2)+'\n');}
console.log(JSON.stringify({status:proof.status,error:proof.error,proof:resolve(out,'recette.json')}));process.exitCode=proof.status==='passed'?0:1;
