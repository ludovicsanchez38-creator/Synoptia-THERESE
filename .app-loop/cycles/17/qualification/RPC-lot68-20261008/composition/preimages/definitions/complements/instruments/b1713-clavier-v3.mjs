// C16 : copie préparée, jamais exécutée par le préparateur. Revue root préalable.
import {preparerContexte} from './contexte-v3.mjs';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import {ownedGitHead} from '../../auxiliary-ports/runtime/aux_node.mjs';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const here = dirname(fileURLToPath(import.meta.url));
const ctx = preparerContexte('B1713');
const {repo,out}=ctx;

const stack = ctx.stack;
const { chromium } = await import(pathToFileURL("/private/tmp/therese-c17-full-suite-ps_tgzy5/source/node_modules/playwright/index.mjs").href);
const { verifierPileJetable, installerGardeReseau } = await import(pathToFileURL(ctx.helper).href);
const paths = ['src/frontend/src/components/prototype/IndiceDeDefilement.tsx', 'src/frontend/src/components/prototype/ConversationCanvasPrototype.tsx', 'src/frontend/src/components/prototype/IndiceDeDefilement.test.tsx', 'src/frontend/src/components/crm/PipelineView.tsx', 'src/frontend/src/components/crm/CRMPanel.tsx', '.agents-sync-paused'];
const hash = b => createHash('sha256').update(b).digest('hex');
const source_snapshot = {};
for (const p of paths) source_snapshot[p] = hash(await readFile(resolve(repo, p)));
const proof = {...ctx.metadata,head: ownedGitHead(repo), status: 'running', scope: 'Complément clavier de première ronde, lecture et preuves seulement', viewport: {width: 800, height: 1000}, source_snapshot, source_script_sha256: hash(await readFile(fileURLToPath(import.meta.url))), checks: [], captures: [], console_errors: [], network_errors: [], guard: {bloquees: [], websockets_bloques: [], telechargements: [], popups: [], portReel: false}};
const base = 'http://127.0.0.1:5173/?port=17593';
const focusAndScroll = () => {
 const e = document.activeElement;
 const zone = document.querySelector('[data-testid="prototype-conversation-scroll"]');
 const composer = document.querySelector('[data-testid="prototype-composer-backdrop"]');
 const indicator = [...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'Voir la suite');
 const rect = e?.getBoundingClientRect();
 return {active: {tag: e?.tagName, id: e?.id, testid: e?.getAttribute('data-testid'), role: e?.getAttribute('role'), aria_label: e?.getAttribute('aria-label'), text: e?.textContent?.trim().slice(0, 160), is_body: e === document.body, connected: Boolean(e?.isConnected), in_scroll: Boolean(zone?.contains(e)), in_composer: Boolean(composer?.contains(e)), focus_visible: Boolean(e?.matches(':focus-visible')), rectangle: rect ? {x: rect.x,y: rect.y,width: rect.width,height: rect.height} : null}, indicator_present: Boolean(indicator), scroll: {top: zone.scrollTop,height: zone.scrollHeight,client: zone.clientHeight,max: zone.scrollHeight-zone.clientHeight}, events: window.__clavierEvents ?? []};
};
let browser;
try {
 proof.stack = await verifierPileJetable(base, stack.data_dir);
 assert.equal(stack.head_at_start, proof.head);
 browser = await chromium.launch({headless: false, channel: 'chrome', chromiumSandbox: true, args: ['--disable-background-networking','--disable-component-update','--disable-sync']});
 proof.chromium = browser.version();
 for (let repetition=1;repetition<=2;repetition++) {
  const context = await browser.newContext({viewport: proof.viewport,locale: 'fr-FR',timezoneId: 'Europe/Paris',serviceWorkers: 'block',acceptDownloads:false});
  await installerGardeReseau(context, proof.guard);
  const page = await context.newPage();
  page.on('pageerror',e=>proof.console_errors.push(String(e)));
  page.on('console',m=>{if(m.type()==='error')proof.console_errors.push(m.text());});
  page.on('response',r=>{if(r.status()>=400)proof.network_errors.push({path:new URL(r.url()).pathname,status:r.status()});});
  const check={repetition,status:'running'};proof.checks.push(check);
  const shot=async step=>{
   const path=resolve(out,step+'-'+repetition+'.png');
   await page.screenshot({path,animations:'disabled'});
   proof.captures.push({path,sha256:hash(await readFile(path))});
  };
  try {
   await page.goto(base,{waitUntil:'domcontentloaded'});
   await page.waitForFunction(()=>Boolean(window.__therese?.runAction));
   await page.evaluate(()=>window.__therese.runAction('home.open'));
   await page.waitForTimeout(1000);
   await page.evaluate(()=>document.fonts.ready);
   await page.evaluate(()=>{
    window.__clavierEvents=[];
    document.addEventListener('keydown',e=>window.__clavierEvents.push({type:e.type,key:e.key,isTrusted:e.isTrusted,tag:e.target.tagName,text:e.target.textContent?.trim().slice(0,80)}));
    document.addEventListener('focusin',e=>window.__clavierEvents.push({type:e.type,tag:e.target.tagName,label:e.target.getAttribute('aria-label'),text:e.target.textContent?.trim().slice(0,80)}));
   });
   const button=page.getByRole('button',{name:'Voir la suite',exact:true});
   await button.waitFor({state:'visible',timeout:5000});
   await button.focus();
   check.before=await page.evaluate(focusAndScroll);
   assert.equal(check.before.active.tag,'BUTTON');
   assert.equal(check.before.active.text,'Voir la suite');
   await shot('avant-entree');
   await page.keyboard.press('Enter');
   await button.waitFor({state:'hidden',timeout:5000});
   await page.waitForFunction(()=>{
    const z=document.querySelector('[data-testid="prototype-conversation-scroll"]');
    return Math.abs(z.scrollHeight-z.clientHeight-z.scrollTop)<=1;
   },{},{timeout:5000});
   await page.waitForTimeout(150);
   check.after_enter=await page.evaluate(focusAndScroll);
   await shot('apres-entree');
   await page.keyboard.press('Tab');
   check.after_tab=await page.evaluate(focusAndScroll);
   await shot('apres-tab');
   check.observation={lost_to_body:check.after_enter.active.is_body,tab_returns_to_composer:check.after_tab.active.in_composer,tab_returns_to_scroll:check.after_tab.active.in_scroll,tab_target:check.after_tab.active};
   assert.equal(check.after_enter.active.is_body,true,'identité historique B1713 après Enter');
   assert.equal(check.after_tab.active.text,'Écrire un e-mail');
   assert(check.after_tab.active.in_composer && check.after_tab.active.focus_visible);
   check.status='observed';
  }catch(e){check.status='failed';check.error=String(e);}
  await context.close();
 }
 assert.equal(proof.console_errors.length,0);
 assert.equal(proof.network_errors.length,0);
 assert(!proof.guard.portReel);
 assert.equal(proof.guard.bloquees.length,0);
 assert.equal(proof.guard.websockets_bloques.length,0);
 proof.status=proof.checks.every(c=>c.status==='observed')?'observed':'failed';
}catch(e){proof.status='failed';proof.error=String(e);}
finally{
 await browser?.close();
 proof.checkout_unchanged=true;
 for(const [p,sha] of Object.entries(source_snapshot)) if(hash(await readFile(resolve(repo,p)))!==sha)proof.checkout_unchanged=false;
 await writeFile(resolve(out,'recette.json'),JSON.stringify(proof,null,2)+'\n');
 await writeFile(resolve(out,'controle-clavier.mjs'),await readFile(fileURLToPath(import.meta.url)));
 console.log(JSON.stringify({status:proof.status,proof:resolve(out,'recette.json'),checks:proof.checks.map(c=>({repetition:c.repetition,status:c.status,observation:c.observation,error:c.error}))}));
}
process.exitCode=proof.status==='observed'?0:1;
