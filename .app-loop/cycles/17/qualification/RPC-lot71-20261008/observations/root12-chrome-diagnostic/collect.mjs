// Diagnostic ciblé MAIN12 : PID Chrome 40332, 23:21:39–23:21:44 Europe/Paris.
// Dérivé du collecteur MAIN11 ; ne lance ni navigateur, ni service, ni profil.
import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import {spawnSync} from 'node:child_process';

const root='/private/tmp/therese-c17-root12-chrome40332-diagnostic-Bx0LdE';
const argv=['show','--style','json','--start','2026-10-08 23:21:39',
  '--end','2026-10-08 23:21:44','--predicate',
  '(processID == 40332 OR ((process == "kernel" OR process == "sandboxd" OR process == "syspolicyd" OR process == "amfid" OR process == "taskgated") AND eventMessage CONTAINS "40332"))'];
const ref=p=>{const b=fs.readFileSync(p);return {path:p,sha256:crypto.createHash('sha256').update(b).digest('hex'),bytes:b.length};};
const started=new Date().toISOString();
const result=spawnSync('/usr/bin/log',argv,{encoding:'buffer',timeout:15000,maxBuffer:2*1024*1024,
  env:{PATH:'/usr/bin:/bin:/usr/sbin:/sbin',LANG:'en_US.UTF-8'},cwd:root});
for(const [name,bytes] of [['stdout.json',result.stdout||Buffer.alloc(0)],
  ['stderr.log',result.stderr||Buffer.alloc(0)]]){
  fs.writeFileSync(path.join(root,name),bytes,{flag:'wx',mode:0o600});
}
let events=null,parse_error=null;
try{events=JSON.parse((result.stdout||Buffer.alloc(0)).toString('utf8'));}
catch(error){parse_error=String(error);}
const passed=result.status===0&&!result.signal&&!result.error&&!parse_error&&Array.isArray(events);
const selected=passed?events.map(x=>({at:x.timestamp,thread:x.threadID,
  process:x.processImagePath,event:x.eventMessage})):[];
const receipt={schema:'c17-root12-chrome40332-system-log-v1',actor:'/root/environment_routes',
  scope:'PID 40332 and system messages naming only PID 40332, local 23:21:39–23:21:44',
  executable:'/usr/bin/log',argv,started_at:started,completed_at:new Date().toISOString(),
  exit_code:result.status,signal:result.signal,error:result.error?String(result.error):null,
  parse_error,stdout_ref:ref(path.join(root,'stdout.json')),
  stderr_ref:ref(path.join(root,'stderr.log')),script_ref:ref(path.join(root,'collect.mjs')),
  event_count:selected.length,passed,diagnostic_only:true,G1_imported:false,
  profile_changed:false,FULL:false};
fs.writeFileSync(path.join(root,'receipt.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx',mode:0o600});
console.log(JSON.stringify({receipt_ref:ref(path.join(root,'receipt.json')),passed,events:selected},null,2));
process.exitCode=passed?0:1;
