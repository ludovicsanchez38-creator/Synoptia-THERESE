// C16 : copie préparée, jamais exécutée par le préparateur. Revue root préalable.
import {preparerContexte} from './contexte-v3.mjs';
/** P162, préparation non exécutée. Entrée uniquement via executer-native.py. */
import assert from 'node:assert/strict';
import {ownedGitHead} from '../../auxiliary-ports/runtime/aux_node.mjs';
import {createHash} from 'node:crypto';
import {mkdir, readFile, writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

const ctx=preparerContexte('P162');const {repo,out}=ctx;
assert(repo && out && process.env.P162_GUARD_PRELOADED==='1','garde GET préalable requise');
const mode='vert';
const hash=(bytes)=>createHash('sha256').update(bytes).digest('hex');
const source='src/frontend/src/components/invoices/InvoicesPanel.tsx';
const snapshot={};
for(const file of [source,'src/frontend/src/components/invoices/InvoicesPanel.debordement.p162.test.tsx','tests/couverture/couverture-ecran.mjs','src/frontend/index.html','.agents-sync-paused']) {
  snapshot[file]=hash(await readFile(resolve(repo,file)));
}
const head=ownedGitHead(repo);
const stack=ctx.stack;
const {chromium}=await import(pathToFileURL("/private/tmp/therese-c17-full-suite-ps_tgzy5/source/node_modules/playwright/index.mjs").href);
const {verifierPileJetable,installerGardeReseau}=await import(pathToFileURL(ctx.helper).href);
const base='http://127.0.0.1:5173/?port=17593', back='http://127.0.0.1:17593';
const proof={...ctx.metadata,version:3,mode,agent:ctx.metadata.actor,head,status:'running',scope:'P162, vrai scroller et indice passif, GET seul, sans activation métier',source_snapshot:snapshot,combinations:[],captures:[],console_errors:[],network_errors:[],checks:[]};
let browser, readFixtures;

const canonical=(value)=>Array.isArray(value)?value.map(canonical):value&&typeof value==='object'?Object.fromEntries(Object.keys(value).sort().map(k=>[k,canonical(value[k])])):value;
const check=(name,condition,detail={})=>{proof.checks.push({name,status:condition?'pass':'fail',...detail});assert(condition,name);};
const active=(page)=>page.evaluate(()=>{const e=document.activeElement;return {tag:e.tagName,id:e.id,role:e.getAttribute('role'),name:e.getAttribute('aria-label'),text:e.textContent?.trim().slice(0,160),tabindex:e.getAttribute('tabindex')};});

try {
  assert.equal(stack.status,'running');assert.equal(stack.repo,repo);assert.equal(stack.head_at_start,head);
  proof.stack=await verifierPileJetable(base,stack.data_dir);
  const auth=await fetch(`${back}/api/auth/token`,{method:'GET',redirect:'error',signal:AbortSignal.timeout(5000)});
  assert(auth.ok);const {token}=await auth.json();assert(typeof token==='string'&&token);
  // Le jeton ne sort pas du helper et n’est jamais sauvegardé dans la preuve.
  const fixtures=async()=>{
    const rows=[];
    for(let skip=0;skip<10000;skip+=100){
      const response=await fetch(`${back}/api/invoices?skip=${skip}&limit=100`,{method:'GET',redirect:'error',signal:AbortSignal.timeout(5000),headers:{'X-Therese-Token':token}});
      assert(response.ok);const page=await response.json();assert(Array.isArray(page));rows.push(...page);
      if(page.length<100){
        const ids=rows.map(r=>r.id);assert.equal(new Set(ids).size,ids.length,'pagination sans doublons');
        rows.sort((a,b)=>String(a.id).localeCompare(String(b.id)));
        return {count:rows.length,sha256:hash(JSON.stringify(canonical(rows)))};
      }
    }
    throw new Error('Fixture trop grande pour cette recette bornée, aucune écriture');
  };
  readFixtures=fixtures;
  proof.fixtures_before=await fixtures();assert(proof.fixtures_before.count>0,'fixture factures existante');
  browser=await chromium.launch({headless: false, channel: 'chrome', chromiumSandbox: true, args: ['--disable-background-networking','--disable-component-update','--disable-sync']});proof.chromium=browser.version();

  for(const width of [800,1440]) for(const theme of ['light','dark']) {
    const label=`${width}-${theme}`, folder=resolve(out,label);await mkdir(folder);
    const combination={width,height:900,theme,status:'running',measures:[],tab_path:[],arrow_path:[],wheel_path:[],captures:[],checks:[]};proof.combinations.push(combination);
    const context=await browser.newContext({viewport:{width,height:900},colorScheme:theme,locale:'fr-FR',timezoneId:'Europe/Paris',reducedMotion:'reduce',serviceWorkers:'block',acceptDownloads:false});
    const guard={bloquees:[],websockets_bloques:[],telechargements:[],popups:[],portReel:false};combination.guard=guard;
    await installerGardeReseau(context,guard);
    await context.addInitScript(themeWanted=>{
      try {sessionStorage.clear();localStorage.setItem('therese-accessibility',JSON.stringify({state:{theme:themeWanted},version:0}));}catch{}
    },theme);
    const page=await context.newPage();
    page.on('pageerror',e=>proof.console_errors.push({combination:label,error:String(e)}));
    page.on('console',m=>{if(m.type()==='error')proof.console_errors.push({combination:label,error:m.text()});});
    page.on('response',r=>{if(r.status()>=400)proof.network_errors.push({combination:label,path:new URL(r.url()).pathname,status:r.status()});});
    page.on('download',d=>{guard.telechargements.push('download');void d.cancel();});
    page.on('popup',p=>{guard.popups.push('popup');void p.close();});
    await page.goto(base,{waitUntil:'networkidle'});
    await page.waitForFunction(()=>window.__thereseMonte&&window.__therese?.runAction);
    check(`${label}: thème réellement affiché`,await page.evaluate(()=>document.documentElement.dataset.theme)===theme);
    await page.evaluate(()=>window.__therese.runAction('invoices.open'));
    // Rouge : l’ancien cadre est mesuré sans lui ajouter rôle, focus ou indice.
    // L’assertion porte ensuite sur le repère absent, avec capture déjà sauvée.
    const frame=page.getByRole('region',{name:'Tableau des devis et factures',exact:true});
    await frame.waitFor({state:'visible'});await frame.locator('tbody tr').first().waitFor({state:'visible'});

    const measure=async(name)=>{
      const state=await frame.evaluate((e,label)=>{
        const rect=n=>{const r=n.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height};};
        const r=e.getBoundingClientRect(), clip={left:r.left+e.clientLeft,right:r.left+e.clientLeft+e.clientWidth,top:Math.max(0,r.top+e.clientTop),bottom:Math.min(innerHeight,r.top+e.clientTop+e.clientHeight)};
        const ancestors=[];
        for(let p=e.parentElement;p;p=p.parentElement){const c=getComputedStyle(p),b=p.getBoundingClientRect();ancestors.push({tag:p.tagName,id:p.id,scrollTop:p.scrollTop,scrollLeft:p.scrollLeft,overflowX:c.overflowX,overflowY:c.overflowY,rect:rect(p)});if(c.overflowX!=='visible'){clip.left=Math.max(clip.left,b.left+p.clientLeft);clip.right=Math.min(clip.right,b.left+p.clientLeft+p.clientWidth);}if(c.overflowY!=='visible'){clip.top=Math.max(clip.top,b.top+p.clientTop);clip.bottom=Math.min(clip.bottom,b.top+p.clientTop+p.clientHeight);}}
        const header=e.querySelector('thead tr'), row=e.querySelector('tbody tr');
        const stickyHeader=header.lastElementChild,stickyCell=row.lastElementChild;
        const textRects=n=>{const range=document.createRange();range.selectNodeContents(n);return Array.from(range.getClientRects()).filter(r=>r.width>0&&r.height>0).map(r=>({left:r.left,right:r.right,top:r.top,bottom:r.bottom}));};
        const whollyVisible=(rs,right=clip.right)=>rs.length>0&&rs.every(b=>b.left>=clip.left-1&&b.right<=right+1&&b.top>=clip.top-1&&b.bottom<=clip.bottom+1);
        const verticallyVisible=rs=>rs.length>0&&rs.every(b=>b.top>=clip.top-1&&b.bottom<=clip.bottom+1);
        const columns=[2,3,4].map(i=>{const th=header.children[i],td=row.children[i],hr=textRects(th),vr=textRects(td);return {name:th.textContent.trim(),header_rects:hr,value_rects:vr,header_vertical_visible:verticallyVisible(hr),first_value_vertical_visible:verticallyVisible(vr),header_fully_visible:whollyVisible(hr,Math.min(clip.right,stickyHeader.getBoundingClientRect().left)),first_value_fully_visible:whollyVisible(vr,Math.min(clip.right,stickyCell.getBoundingClientRect().left))};});
        const described=(e.getAttribute('aria-describedby')??'').split(/\s+/).filter(Boolean).map(id=>document.getElementById(id)).filter(Boolean);
        const indicators=described.map(n=>({id:n.id,text:n.textContent.trim(),role:n.getAttribute('role'),tag:n.tagName,rect:rect(n),focusable:n.tabIndex>=0,before_table:Boolean(n.compareDocumentPosition(e)&Node.DOCUMENT_POSITION_FOLLOWING)}));
        const css=getComputedStyle(e),focus=document.activeElement;
        const amount=stickyCell.querySelector('span.font-semibold');
        return {name:label,role:e.getAttribute('role'),accessible_name:e.getAttribute('aria-label'),scrollLeft:e.scrollLeft,scrollWidth:e.scrollWidth,clientWidth:e.clientWidth,limit:Math.max(0,e.scrollWidth-e.clientWidth),overflowX:css.overflowX,tabIndex:e.tabIndex,focused:focus===e,focus_visible:e.matches(':focus-visible'),box_shadow:css.boxShadow,outline_style:css.outlineStyle,outline_width:css.outlineWidth,frame:rect(e),clip,ancestors,indicators,columns,sticky:{header:rect(stickyHeader),cell:rect(stickyCell),position:getComputedStyle(stickyCell).position,right:getComputedStyle(stickyCell).right,amount_rects:amount?textRects(amount):[],amount_visible:amount?whollyVisible(textRects(amount)):false,buttons:Array.from(stickyCell.querySelectorAll('button')).map(b=>({text:b.textContent.trim(),rect:rect(b),visible:whollyVisible([rect(b)])}))},first_client:row.children[1].querySelector('button')?.getAttribute('aria-label')};
      },name);
      combination.measures.push(state);return state;
    };
    const shot=async(name)=>{const path=resolve(folder,`${name}.png`);await page.screenshot({path,animations:'disabled'});const capture={path,sha256:hash(await readFile(path))};combination.captures.push(capture);proof.captures.push(capture);};
    const assertIndicators=(state)=>{
      const left=state.scrollLeft>1,right=state.limit-state.scrollLeft>1;
      const text=state.indicators.map(i=>i.text).join(' ');
      check(`${label}/${state.name}: indication gauche conforme`,/\bgauche\b/i.test(text)===left,{position:state.scrollLeft,limit:state.limit,text});
      check(`${label}/${state.name}: indication droite conforme`,/\bdroite\b/i.test(text)===right);
      check(`${label}/${state.name}: aucun indice focalisable`,state.indicators.every(i=>!i.focusable&&i.tag!=='BUTTON'));
      check(`${label}/${state.name}: indice avant les lignes`,state.indicators.every(i=>i.before_table));
      check(`${label}/${state.name}: pas d’indice si tout tient`,state.limit>1||state.indicators.length===0);
      check(`${label}/${state.name}: montant et actions collés visibles`,state.sticky.position==='sticky'&&state.sticky.right==='0px'&&state.sticky.amount_visible&&state.sticky.buttons.length===2&&state.sticky.buttons.every(b=>b.visible));
      for(const column of state.columns)check(`${label}/${state.name}: ${column.name} et première valeur restent visibles verticalement`,column.header_vertical_visible&&column.first_value_vertical_visible);
    };
    let state=await measure('initial');await shot('initial');assertIndicators(state);
    check(`${label}: le vrai scroller est focalisable`,state.tabIndex===0&&['auto','scroll'].includes(state.overflowX));
    if(width===800)check(`${label}: fixture exerce un vrai débordement`,state.limit>2);

    // Tab natif seulement, depuis le focus laissé par l’ouverture réelle.
    for(let i=0;i<96&&!await frame.evaluate(e=>document.activeElement===e);i++){
      await page.keyboard.press('Tab');combination.tab_path.push(await active(page));
    }
    state=await measure('tab-scroller');
    check(`${label}: Tab natif rejoint le vrai scroller`,state.focused&&combination.tab_path.length>0);
    check(`${label}: anneau de focus visible au clavier`,state.focus_visible&&(state.box_shadow!=='none'||(state.outline_style!=='none'&&parseFloat(state.outline_width)>0)));
    await shot('tab-scroller');assertIndicators(state);

    if(state.limit>2){
      const start=state.scrollLeft;
      await page.keyboard.press('ArrowRight');await page.waitForTimeout(180);
      state=await measure('arrow-right');combination.arrow_path.push(state.scrollLeft);
      check(`${label}: flèche native déplace le tableau`,state.scrollLeft>start+1);
      check(`${label}: flèche conserve le focus`,state.focused&&state.focus_visible);assertIndicators(state);await shot('arrow-right');
      const box=await frame.boundingBox();assert(box);await page.mouse.move(box.x+box.width/2,Math.min(850,box.y+75));
      await page.mouse.wheel(-10000,0);await page.waitForTimeout(200);
      state=await measure('retour-molette-debut');assertIndicators(state);check(`${label}: retour réel au début`,state.scrollLeft<=1);
      const middleDelta=Math.min(100,state.limit/2);
      await page.mouse.wheel(middleDelta,0);await page.waitForTimeout(200);
      state=await measure('molette-intermediaire');combination.wheel_path.push(state.scrollLeft);assertIndicators(state);
      check(`${label}: position intermédiaire exercée`,state.scrollLeft>1&&state.scrollLeft<state.limit-1);check(`${label}: indice ne vole pas le focus pendant la molette`,state.focused);await shot('molette-intermediaire');
      // Le scroll suivant part d’un autre focus réel : l’indice ne le vole pas.
      await page.keyboard.press('Shift+Tab');const otherFocus=await active(page);
      check(`${label}: un autre élément a le focus`,!await frame.evaluate(e=>document.activeElement===e));
      await page.mouse.wheel(10000,0);await page.waitForTimeout(250);
      state=await measure('molette-bord-autre-focus');combination.wheel_path.push(state.scrollLeft);assertIndicators(state);
      check(`${label}: molette atteint le bord`,Math.abs(state.limit-state.scrollLeft)<=1);
      check(`${label}: aucun vol du focus externe`,JSON.stringify(await active(page))===JSON.stringify(otherFocus));
      for(const column of state.columns)check(`${label}: ${column.name} entier hors du sticky au bord`,column.header_fully_visible&&column.first_value_fully_visible);
      await shot('molette-bord-autre-focus');
      await page.keyboard.press('Tab');state=await measure('tab-scroller-au-bord');
      check(`${label}: retour Tab natif au scroller`,state.focused&&state.focus_visible);assertIndicators(state);await shot('tab-scroller-au-bord');
      const beforeTab=await active(page);await page.keyboard.press('Tab');const afterTab=await active(page);
      check(`${label}: Tab poursuit vers la commande client`,afterTab.tag==='BUTTON'&&afterTab.name===state.first_client&&JSON.stringify(beforeTab)!==JSON.stringify(afterTab));
      combination.after_tab_client=afterTab;
    }else{
      combination.no_overflow=true;await page.keyboard.press('ArrowRight');await page.waitForTimeout(100);
      state=await measure('sans-debordement-arrow');assertIndicators(state);check(`${label}: flèche garde le focus sans débordement`,state.focused);
      for(const column of state.columns)check(`${label}: ${column.name} lisible sans défilement`,column.header_fully_visible&&column.first_value_fully_visible);
    }
    // Vérification de recalcul au resize, sans modifier style ni scrollLeft.
    await page.setViewportSize({width:width===800?1440:800,height:900});await page.waitForTimeout(250);
    state=await measure('redimensionnement');assertIndicators(state);await shot('redimensionnement');
    await page.setViewportSize({width,height:900});await page.waitForTimeout(250);
    state=await measure('retour-largeur');assertIndicators(state);await shot('retour-largeur');
    check(`${label}: garde propre`,!Object.values(guard).some(v=>Array.isArray(v)?v.length:v));
    combination.status='passed';await context.close();
  }
  proof.fixtures_after=await fixtures();
  check('nombre de pièces conservé',proof.fixtures_before.count===proof.fixtures_after.count);
  check('empreinte canonique de toutes les pièces conservée',proof.fixtures_before.sha256===proof.fixtures_after.sha256);
  check('aucune erreur console',proof.console_errors.length===0);check('aucune réponse réseau en erreur',proof.network_errors.length===0);
  for(const [path,expected]of Object.entries(snapshot))assert.equal(hash(await readFile(resolve(repo,path))),expected,`source intacte ${path}`);
  proof.status='passed';
}catch(error){proof.status='failed';proof.error=String(error);}
finally{
  if(browser)await browser.close();
  // La préservation est attestée également sur un rouge attendu, sans
  // transformer son assertion manquante en résultat vert.
  if(readFixtures&&proof.fixtures_before&&!proof.fixtures_after){
    try{proof.fixtures_after=await readFixtures();}catch(error){proof.preservation_error=String(error);}
  }
  proof.fixtures_unchanged=Boolean(proof.fixtures_before&&proof.fixtures_after&&proof.fixtures_before.count===proof.fixtures_after.count&&proof.fixtures_before.sha256===proof.fixtures_after.sha256);
  proof.source_after={};
  for(const path of Object.keys(snapshot))proof.source_after[path]=hash(await readFile(resolve(repo,path)));
  proof.sources_unchanged=Object.entries(snapshot).every(([path,digest])=>proof.source_after[path]===digest);
  proof.guard={bloquees:[],websockets_bloques:[],telechargements:[],popups:[],portReel:false};
  for(const combination of proof.combinations){
    for(const key of ['bloquees','websockets_bloques','telechargements','popups'])proof.guard[key].push(...(combination.guard?.[key]??[]));
    proof.guard.portReel||=Boolean(combination.guard?.portReel);
  }
  if(Object.values(proof.guard).some(value=>Array.isArray(value)?value.length:value))proof.status='failed';
  if(!proof.fixtures_unchanged||!proof.sources_unchanged)proof.status='failed';
  await writeFile(resolve(out,'recette.json'),JSON.stringify(proof,null,2)+'\n');
}
console.log(JSON.stringify({status:proof.status,error:proof.error,proof:resolve(out,'recette.json')}));
process.exitCode=proof.status==='passed'?0:1;
