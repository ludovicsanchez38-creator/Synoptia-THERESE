import fs from "node:fs";
import crypto from "node:crypto";
const repo="/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE-c15-codex";
const root=repo+"/.app-loop/cycles/17/qualification/RPC-lot78-chrome-boundary-matrix-20261009";
const digest=b=>crypto.createHash("sha256").update(b).digest("hex");
const pin=p=>{const s=fs.lstatSync(p),b=fs.readFileSync(p);if(!s.isFile()||s.isSymbolicLink()||s.uid!==501||s.nlink!==1)throw Error("file identity: "+p);return {path:p,sha256:digest(b),bytes:b.length};};
const names=["chromium-v1/REPORT.md","chromium-v1/INDEX.json","chromium/REPORT.md","chromium/INDEX.json","MAIN-source-checks.json","MAIN-profile-inventory.json","MAIN-version-source-attempt.json","matrix/MATRIX.md","matrix/PROFILE-INVENTORY.json","matrix/TEXT-CHECK.json","matrix/INDEX.json","review/REVIEW.json","review/INDEX.json"];
const files={};for(const n of names){files[n]=pin(root+"/"+n);if(n.endsWith(".json"))JSON.parse(fs.readFileSync(root+"/"+n));}
const review=JSON.parse(fs.readFileSync(root+"/review/REVIEW.json"));
const inputs=[];for(const r of review.source_refs){const p=pin(r.path);if(p.bytes!==r.bytes||p.sha256!==r.sha256)throw Error("source pin "+r.path);inputs.push(p);}
if(inputs.length!==26)throw Error("review inputs");
const m=JSON.parse(fs.readFileSync(root+"/MAIN-profile-inventory.json"));
const v=JSON.parse(fs.readFileSync(root+"/matrix/PROFILE-INVENTORY.json"));
const p=fs.readFileSync(v.profile_ref.path,"utf8").split("\n");
const matrix=fs.readFileSync(root+"/matrix/MATRIX.md","utf8").split("\n");
if(m.forms.length!==21||v.expressions.length!==21||m.allow_count!==19||v.allow_count!==19)throw Error("count");
for(let i=0;i<21;i++){const a=m.forms[i],b=v.expressions[i];if(a.start_line!==b.start_line||a.end_line!==b.end_line||a.text!==b.literal_source||a.text!==p.slice(a.start_line-1,a.end_line).join("\n"))throw Error("literal form "+i);if(matrix.filter(l=>l.startsWith("| "+b.matrix_id+",")).length!==1)throw Error("P ID");}
for(let i=1;i<=24;i++)if(matrix.filter(l=>l.startsWith("| G"+String(i).padStart(2,"0")+",")).length!==1)throw Error("G ID");
const dirty={"docs/application-map/README.md":"10a24b4eab25e37fe19ac47220554740210446f702da67ddbca4b97db2bbf134","docs/application-map/architecture.md":"a84fb3c6db7864e95bd9003a37dadd80567bc2c9876e6afc5427634484d25fe4","docs/application-map/constats-visuels.md":"094e21dcc76aa3039afde1a183e34fc7adafa0a131e2f184baf2c19bcbf8328c","docs/application-map/couverture.md":"23de3dddc41d574353a067833bfabd6a2ad8d920a10c269b1e9f2046dcf34a7e","docs/application-map/dependances.md":"79ec6502cae73cc14072a6a083aaa800941637903dfb3ab44b6a692afb87e430","docs/application-map/fonctionnalites.md":"e3ccb88c7b91e75133378387998f4a27a3665ca4df9bd06200c4b9ea1c93ccb3","docs/application-map/inconnues.md":"9174af38012989902f55072e8c9fdc783ce2888bdec17eaccfaf746e1a4234b1","docs/application-map/risques.md":"0e307d0be5336f982cff0ace0e3219d51dba99fd4f926f5ef2e67043ae6503b7","docs/releases/v0.77.1-alpha.md":"f0ce0458539fa71116efb775abcf6b780669ffeb41c583364f4bfc23bd24eb8a"};
for(const[n,h]of Object.entries(dirty))if(digest(fs.readFileSync(repo+"/"+n))!==h)throw Error("preexisting dirty "+n);
const state=JSON.parse(fs.readFileSync(repo+"/.app-loop/state.json"));
const budget=JSON.parse(fs.readFileSync(repo+"/.app-loop/budget.json"));
const c=budget.cycles["17"];
console.log(JSON.stringify({schema:"c17-lot78-main-final-text-copy-check-v1",actor:"/root",observed_at_utc:new Date().toISOString(),scope:"literal_copies_and_selected_refs_not_runtime_admission",files,inputs,input_ref_count:inputs.length,main_shared_inventory_literal_equal:true,profile_count:21,allow_count:19,selected_guard_rows:24,unique_P_G_IDs:true,whole_G1_logic_exhaustive:false,dirty_preexisting_pins:dirty,dirty_preexisting_unchanged:true,state_snapshot:{sha256:digest(fs.readFileSync(repo+"/.app-loop/state.json")),status:state.status,phase:state.phase,cycle:state.cycle,zero_bug_rounds:state.zero_bug_rounds,forced_transitions:state.forced_transitions},budget_snapshot:{sha256:digest(fs.readFileSync(repo+"/.app-loop/budget.json")),gpt:c.usage.gpt,last_event:c.events.at(-1),record_chunk:"866be5",check_chunk:"71d10f",budget_check:"PASS",additional_tokens_duration:"unmeasured_not_zero_consumption",limits:budget.limits},preparatory_failure:{chunk:"549cb2",exit_code:1,kind:"Node_inline_literal_backslash_n_SyntaxError_before_evaluation",native:false,source_or_profile_changed:false},SBPL_compiled:false,native_probe_executed:false,Chrome_launched:false,FULL:false,admission:false,product_rounds_validated:0,passed:true},null,2));
