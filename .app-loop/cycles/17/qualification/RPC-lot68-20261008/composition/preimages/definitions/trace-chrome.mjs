import {connectOwnedChrome} from './auxiliary-ports/runtime/aux_node.mjs';
// Instrumentation neuve : collecte les gestes de la future execution, jamais de resultats historiques.
import {readFileSync,writeFileSync} from 'node:fs';
import {join} from 'node:path';
import {chromium} from "/private/tmp/therese-c17-full-suite-ps_tgzy5/source/node_modules/playwright/index.mjs";
const destination=process.env.C16_ACTION_TRACE;
if(!destination)throw new Error('Destination explicite de trace requise');
const config=JSON.parse(readFileSync(new URL('./prepared-config.json',import.meta.url),'utf8'));
const trace={cycle:17,actor:config.actor,round_id:config.round_id,head:config.head,
  started_at:new Date().toISOString(),status:'observing',launches:[],pages:[],events:[],
  source_imported:import.meta.url,limits:'Trace DOM des gestes de Playwright ; ne se presente pas comme une lecture AX native.'};
const originalLaunch=options=>connectOwnedChrome(chromium,options);
chromium.launch=async(options={})=>{
  if(options.channel!=='chrome'||options.headless!==false||options.chromiumSandbox!==true)
    throw new Error('Le lanceur attendu est Chrome Mac visible avec sandbox explicite');
  const browser=await originalLaunch(options);
  trace.launches.push({options,version:browser.version(),at:new Date().toISOString()});
  const originalNewContext=browser.newContext.bind(browser);
  browser.newContext=async(...arguments_)=>{
    const context=await originalNewContext(...arguments_);
    await context.exposeBinding('__c16ObservedTrustedAction',(source,value)=>{
      const u=new URL(source.page.url());
      trace.events.push({page:u.origin+u.pathname,...value});
    });
    await context.addInitScript(()=>{
      for(const type of ['pointerdown','click','keydown','focusin'])
        document.addEventListener(type,event=>{
          const target=event.target;
          if(!(target instanceof Element))return;
          const data={type,trusted:event.isTrusted,key:event.key??null,
            name:(target.getAttribute('aria-label')??target.textContent??'').trim().slice(0,200),
            tag:target.tagName,id:target.id,role:target.getAttribute('role'),
            testid:target.getAttribute('data-testid'),
            at:new Date().toISOString(),visible:document.visibilityState,
            timeline:document.timeline.currentTime};
          void window.__c16ObservedTrustedAction(data);
        },true);
    });
    context.on('page',page=>{
      page.on('domcontentloaded',()=>{
        const u=new URL(page.url());
        trace.pages.push({origin:u.origin,path:u.pathname,at:new Date().toISOString()});
      });
    });
    return context;
  };
  return browser;
};
process.once('exit',()=>{
  trace.completed_at=new Date().toISOString();
  trace.process_exit_code=process.exitCode??0;
  trace.status='observations_collected_not_semantic_verdict';
  writeFileSync(destination,JSON.stringify(trace,null,2)+'\n');
});
