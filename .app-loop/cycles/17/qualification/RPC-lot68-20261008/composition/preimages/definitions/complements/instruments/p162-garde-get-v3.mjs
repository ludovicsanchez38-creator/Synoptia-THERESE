import {preparerContexte} from './contexte-v3.mjs';
const ctx=preparerContexte('P162');
import assert from 'node:assert/strict';
import {writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
const journal={policy:'GET uniquement, Node avant import du helper, navigateur avant navigation',node_requests:[],browser_requests:[],blocked:[],contexts:0};
const allowed=(method,address)=>{const u=new URL(address);return method==='GET'&&u.protocol==='http:'&&u.hostname==='127.0.0.1'&&['5173','17593'].includes(u.port)&&!u.username&&!u.password;};
const clean=address=>{try{const u=new URL(address);return `${u.origin}${u.pathname}`;}catch{return '[adresse invalide]';}};
const rawFetch=globalThis.fetch;
globalThis.fetch=async(input,options={})=>{const address=typeof input==='string'||input instanceof URL?String(input):input.url;const method=(options.method??input.method??'GET').toUpperCase();if(!allowed(method,address)){journal.blocked.push({surface:'node',method,url:clean(address)});throw new Error('Requête Node refusée par garde GET');}journal.node_requests.push({method,url:clean(address)});return rawFetch(input,options);};
process.once('beforeExit',async()=>{journal.status=journal.blocked.length===0?'passed':'failed';await writeFile(resolve(ctx.out,'network-get-proof.json'),JSON.stringify(journal,null,2)+'\n');if(journal.blocked.length)process.exitCode=1;});
const {chromium}=await import(pathToFileURL("/private/tmp/therese-c17-full-suite-ps_tgzy5/source/node_modules/playwright/index.mjs").href);
const realLaunch=chromium.launch.bind(chromium);
chromium.launch=async(...args)=>{const browser=await realLaunch(...args);const realNewContext=browser.newContext.bind(browser);browser.newContext=async(options={})=>{journal.contexts++;const context=await realNewContext({...options,acceptDownloads:false});const realRoute=context.route.bind(context);context.route=(pattern,handler,routeOptions)=>realRoute(pattern,async(route,request)=>{const r=route.request();if(!allowed(r.method(),r.url())){journal.blocked.push({surface:'browser',method:r.method(),url:clean(r.url())});return route.abort('blockedbyclient');}return handler(route,request);},routeOptions);await context.route('**/*',route=>route.fallback());context.on('page',page=>{page.on('request',r=>journal.browser_requests.push({method:r.method(),url:clean(r.url())}));});return context;};return browser;};
assert.equal(journal.blocked.length,0);

process.env.P162_GUARD_PRELOADED='1';
