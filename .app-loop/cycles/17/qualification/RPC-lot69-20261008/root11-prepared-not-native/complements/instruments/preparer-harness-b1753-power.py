"""Lanceur FUTUR préparé, non exécuté : B1753 ou B1760, jamais une restauration.

L'argument --reviewed-contract-sha doit être fourni par root après lecture.
Cette égalité protège contre un lancement périmé ; elle n'authentifie pas root.
La préparation courante n'appelle pas ce script, même sans arguments.
"""
from __future__ import annotations
import argparse
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from nested_capture import capture_nested, reserved_path
import tempfile
import xml.etree.ElementTree as ET

REPO=Path('/private/tmp/therese-c17-wrapper-source-kGvU1hdx/source')
HERE=Path(__file__).resolve().parent
HEAD='2d69e30c9c6dd18823ee6102271876003a6a67cc'
CONTRACT=HERE.parent/'contrats-normalises-proposes.json'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
save=lambda path,value:path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
parser=argparse.ArgumentParser()
parser.add_argument('--group',choices=['B1753'],required=True)
parser.add_argument('--actor',required=True)
parser.add_argument('--round-id',required=True)
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--reviewed-contract-sha',required=True)
args=parser.parse_args()
assert args.reviewed_contract_sha==sha(CONTRACT),'Revue root du contrat exact requise'
contract=json.loads(CONTRACT.read_text())
assert contract['head']==HEAD
registry_path=Path(contract['identity_registry']['path'])
assert sha(registry_path)==contract['identity_registry']['sha256']
registry=json.loads(registry_path.read_text())
assert any(a['actor']==args.actor for a in registry['actors']),'Acteur absent du registre réel'
assert args.round_id and all(c.isalnum() or c in '._-' for c in args.round_id)
head=lambda:subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
assert head()==HEAD
for name,digest in contract['source_snapshot'].items():assert sha(REPO/name)==digest,name
runroot=HERE.parent/'runs';runroot.mkdir(exist_ok=True)
out=args.out.resolve();assert out.is_relative_to(runroot.resolve()) and out!=runroot.resolve()
assert not out.exists(),'Sortie neuve obligatoire, aucun reçu existant écrasé'
out=reserved_path('sql-b1753-power'+'-output',requested=out)
assert out.resolve().is_relative_to(runroot.resolve())
started=datetime.now(UTC).isoformat()
profile=reserved_path('sql-b1753-power'+'-profile')
assert profile.is_relative_to(Path('/private/tmp'))
for part in ['home','data','tmp','checkout']:(profile/part).mkdir()
copy=profile/'checkout'
snapshot={}
# Lire la liste Git et vérifier chaque blob courant avant copie. Aucun tar,
# extraction, checkout original reset ou partage de dossier utilisateur.
tree=subprocess.check_output(['git','ls-tree','-rz','--full-tree',HEAD],cwd=REPO)
for entry in tree.split(b'\0'):
    if not entry:continue
    description,rawname=entry.split(b'\t',1)
    mode,kind,blob=description.decode().split()
    name=os.fsdecode(rawname)
    assert kind=='blob' and not Path(name).is_absolute() and '..' not in Path(name).parts
    original=REPO/name
    payload=os.readlink(original).encode() if mode=='120000' else original.read_bytes()
    git_blob=hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()
    assert git_blob==blob,'Le fichier courant diffère de HEAD : '+name
    target=copy/name;target.parent.mkdir(parents=True,exist_ok=True)
    if mode=='120000':
        link=os.fsdecode(payload);assert not Path(link).is_absolute()
        assert (target.parent/link).resolve().is_relative_to(copy)
        target.symlink_to(link)
    else:target.write_bytes(payload);target.chmod(0o755 if mode=='100755' else 0o644)
    snapshot[name]={'sha256':hashlib.sha256(payload).hexdigest(),'git_blob':blob,'mode':mode}
assert head()==HEAD
# Mutation uniquement dans la copie privée d'un test, jamais dans le produit.
mutated_name='tests/test_actions_traitement.py'
mutated=copy/mutated_name
original=mutated.read_text()
import ast
tree_ast=ast.parse(original)
klass=next(n for n in tree_ast.body if isinstance(n,ast.ClassDef) and n.name=='TestLaRouteHistoriqueEstCanonique')
functions=[n for n in klass.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='test_delete_passe_par_le_traitement_durable']
assert len(functions)==1
function=functions[0]
lines=original.splitlines(keepends=True)
section=''.join(lines[function.lineno-1:function.end_lineno])
needle='            assert reponse.status_code == 200\n'
assert section.count(needle)==1
message='B-1753 : assertion forcée avant libération du flux'
new_section=section.replace(needle,needle+'            assert False, '+repr(message)+'\n')
new_original=''.join(lines[:function.lineno-1])+new_section+''.join(lines[function.end_lineno:])
ast.parse(new_original)
mutated.write_text(new_original)
(out/'test_actions_traitement.before-power.py').write_text(original)
mutation={'source_relative':mutated_name,'source_original_sha256':snapshot[mutated_name]['sha256'],
    'executed_copy':str(mutated),'executed_copy_sha256':sha(mutated),'insertions':1,
    'function':'TestLaRouteHistoriqueEstCanonique.test_delete_passe_par_le_traitement_durable',
    'after':'assert reponse.status_code == 200','inserted':'assert False, '+repr(message),
    'product_source_changed':False,'original_test_source_changed':False}
save(out/'power-mutation.json',mutation)
snapshot[mutated_name]={**snapshot[mutated_name],'sha256':sha(mutated),
    'source_original_sha256':mutation['source_original_sha256'],'intentional_private_test_mutation':True}
tools=copy/'.c16_instruments';tools.mkdir()
names=['trace-b1753.py','test_b1753_frontiere_suivante.py'] if args.group=='B1753' else ['observer-b1760-export.py']
names.append('ipv6-capacity-guard.py')
tools_snapshot={}
for name in names:
    target=tools/name.replace('-','_');shutil.copyfile(HERE/name,target)
    tools_snapshot[target.name]=sha(target)
bootstrap=out/'bootstrap-prive.py'
bootstrap.write_text('''from pathlib import Path
import hashlib,json,os,socket,sys,traceback
copy=Path(os.environ['C16_COPY']).resolve()
profile=copy.parent
assert profile.is_relative_to(Path('/private/tmp'))
assert Path.home().resolve()==profile/'home'
assert not any(n=='app' or n.startswith('app.') for n in sys.modules)
sys.path[:0]=[str(copy/'.c16_instruments'),str(copy/'tests/couverture'),str(copy/'src/backend'),str(copy)]
from backend_offline import installer_garde_socket
installer_garde_socket()
from ipv6_capacity_guard import install_guard
blocked=[]
capacity_probes=[]
install_guard(Path('/private/tmp/therese-c17-full-suite-ps_tgzy5/source/.venv-conforme/lib/python3.13/site-packages/urllib3/util/connection.py'), '412d8dab54efff6c201501e71e66b67c71563272b3ac1b046f85125349a26d2e', blocked, capacity_probes)
import urllib3.util.connection as capacity_module
assert capacity_module.HAS_IPV6 is False
from app.models import database as db
import app
assert Path(app.__file__).resolve().is_relative_to(copy)
assert Path(db.settings.data_dir).resolve()==profile/'data'
assert Path(db.settings.db_path).resolve().is_relative_to(profile/'data')
assert not os.environ.get('THERESE_DB_PLAINTEXT')
import pytest
selectors=json.loads(os.environ['C16_SELECTORS'])
plugins=['-p','trace_b1753'] if os.environ['C16_GROUP']=='B1753' else ['-p','observer_b1760_export']
class C16ModuleReporter:
    @pytest.hookimpl(tryfirst=True)
    def pytest_sessionfinish(self, session, exitstatus):
        Path(os.environ['C16_MODULE_RECEIPT']).write_text(json.dumps({'cycle':17,'actor':os.environ['C16_ACTOR'],'head':os.environ['C16_EXECUTION_HEAD'],'copy':str(copy),'home':str(Path.home()),'data_dir':str(db.settings.data_dir),'app_file':str(Path(app.__file__).resolve()),'database_module':{'path':str(Path(db.__file__).resolve()),'sha256':hashlib.sha256(Path(db.__file__).read_bytes()).hexdigest()},'network_guard_before_product_import':True,'policy':'no IP bind/connect/connect_ex/listen/send ; exact urllib3 IPv6 probe receives EAFNOSUPPORT without native bind ; no app server ; ASGI invoice/action requests inside private test fixtures only','blocked_network':blocked,'ipv6_capacity_probes':capacity_probes,'pytest_exit_code':int(exitstatus),'scope':'harness_private_not_runtimev3_plaintext'},ensure_ascii=False,indent=2)+'\\n')
exit_code=pytest.main(plugins+selectors+['-q','--timeout=60','-p','no:cacheprovider','--junitxml='+os.environ['C16_XML']], plugins=[C16ModuleReporter()])
Path(os.environ['C16_MODULE_RECEIPT']).write_text(json.dumps({'cycle':17,'actor':os.environ['C16_ACTOR'],'head':os.environ['C16_EXECUTION_HEAD'],'copy':str(copy),'home':str(Path.home()),'data_dir':str(db.settings.data_dir),'app_file':str(Path(app.__file__).resolve()),'database_module':{'path':str(Path(db.__file__).resolve()),'sha256':hashlib.sha256(Path(db.__file__).read_bytes()).hexdigest()},'network_guard_before_product_import':True,'policy':'no IP bind/connect/connect_ex/listen/send ; exact urllib3 IPv6 probe receives EAFNOSUPPORT without native bind ; no app server ; ASGI invoice/action requests inside private test fixtures only','blocked_network':blocked,'ipv6_capacity_probes':capacity_probes,'pytest_exit_code':exit_code,'scope':'harness_private_not_runtimev3_plaintext'},ensure_ascii=False,indent=2)+'\\n')
raise SystemExit(exit_code if not blocked else 1)
''')
selectors=(['tests/test_actions_traitement.py::TestLaRouteHistoriqueEstCanonique::test_delete_passe_par_le_traitement_durable',
            '.c16_instruments/test_b1753_frontiere_suivante.py::test_frontiere_suivante_ne_recoit_aucune_tache_du_temoin']
           if args.group=='B1753' else ['tests/test_b1760_echeance_mentions.py'])
env={'PATH':'/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin','HOME':str(profile/'home'),
     'TMPDIR':str(profile/'tmp'),'LANG':'en_US.UTF-8','THERESE_ENV':'test',
     'THERESE_DATA_DIR':str(profile/'data'),'THERESE_SKIP_SERVICES':'1',
     'THERESE_DB_KEY':'ad'*32,'PYTHON_KEYRING_BACKEND':'keyring.backends.null.Keyring',
     'PYTHONDONTWRITEBYTECODE':'1','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1',
     'OLLAMA_BASE_URL':'http://127.0.0.1:9','THERESE_SONDE_CATALOGUE':'off',
     'C16_COPY':str(copy),'C16_GROUP':args.group,'C16_ACTOR':args.actor,'C16_ROUND_ID':args.round_id,
     'C16_EXECUTION_HEAD':HEAD,'C16_SELECTORS':json.dumps(selectors),
     'C16_XML':str(out/'harness.xml'),'C16_MODULE_RECEIPT':str(out/'modules-executes.json'),
     'ENQUETE_REPO':str(copy),'ENQUETE_TRACE':str(out/'frontieres.jsonl'),'ENQUETE_MODE':'controle',
     'B1760_PREUVES':str(out/'exports')}
assert 'THERESE_DB_PLAINTEXT' not in env
command=['/private/tmp/therese-c17-full-suite-ps_tgzy5/source/.venv-conforme/bin/python',str(bootstrap)]
save(out/'commande-environnement.json',{'command':command,'cwd':str(copy),'environment':env,
    'scope':'no original HOME/data ; no server ; no restore ; fixed key for disposable SQLCipher test only'})
result=capture_nested(command,cwd=copy,env=env,timeout=240,stdout_path=out/'harness.stdout',stderr_path=out/'harness.stderr',label='sql-b1753-power')
with (out/'harness.exit').open('x') as stream:stream.write('exit='+str(result.returncode)+'\n')
changed=[]
for name,info in snapshot.items():
    target=copy/name
    payload=os.readlink(target).encode() if info['mode']=='120000' else target.read_bytes()
    if hashlib.sha256(payload).hexdigest()!=info['sha256']:changed.append(name)
def external_guard_valid(modules: dict) -> bool:
    probes=modules.get('ipv6_capacity_probes',[])
    return (modules.get('blocked_network') == [] and len(probes) == 1
        and probes[0].get('kind') == 'urllib3_exact_ipv6_capacity_probe'
        and probes[0].get('address') == ['::1',0]
        and probes[0].get('native_bind_called') is False
        and probes[0].get('listen_called') is False
        and probes[0].get('connect_called') is False
        and probes[0].get('packet_sent') is False
        and probes[0].get('bind_succeeded') is False
        and probes[0].get('closed_before_return') is True
        and modules.get('pytest_exit_code') == 1)
modules=json.loads((out/'modules-executes.json').read_text())
external_guard_ok=external_guard_valid(modules)
cases=list(ET.parse(out/'harness.xml').getroot().iter('testcase'))
bad=[{'classname':c.get('classname'),'name':c.get('name')} for c in cases if any(c.find(k) is not None for k in ['failure','error','skipped'])]
expected=2 if args.group=='B1753' else 19
def power_case_contract(cases: list) -> bool:
    forced=[c for c in cases if c.get('classname')=='tests.test_actions_traitement.TestLaRouteHistoriqueEstCanonique'
        and c.get('name')=='test_delete_passe_par_le_traitement_durable']
    sentinel=[c for c in cases if c.get('name')=='test_frontiere_suivante_ne_recoit_aucune_tache_du_temoin']
    if len(cases)!=2 or len(forced)!=1 or len(sentinel)!=1:
        return False
    if any(c.find(t) is not None for c in cases for t in ['error','skipped']):
        return False
    failure=forced[0].find('failure')
    expected='B-1753 : assertion forcée avant libération du flux'
    return (failure is not None and len(forced[0].findall('failure'))==1
        and expected in (failure.get('message') or '')
        and 'AssertionError: '+expected in (failure.text or '')
        and sentinel[0].find('failure') is None)
power_contract_ok=power_case_contract(cases)
pdfs=list((out/'exports').glob('pdf-*/piece.pdf')) if args.group=='B1760' else []
species=[]
if args.group=='B1760':
    for pdf in pdfs:
        origin=json.loads((pdf.parent/'c16-nodeid.json').read_text())
        assert origin['actor']==args.actor and origin['round_id']==args.round_id and origin['head']==HEAD
        species.append(origin['test_nodeid'])
    definition=json.loads((HERE.parent/'b1760-identites-historiques-completes.json').read_text())
    required={s['nodeid'] for s in definition['current_species_required_per_round']}
    assert len(pdfs)==10 and len(set(species))==10 and set(species)==required
else:
    events=[json.loads(line) for line in (out/'frontieres.jsonl').read_text().splitlines()]
    bounds=[e for e in events if e['evenement'] in ['debut_test','fin_test']]
    assert len(bounds)==4 and [e['evenement'] for e in bounds]==['debut_test','fin_test','debut_test','fin_test']
    assert bounds[1]['registre']==bounds[2]['registre']==[] and bounds[1]['fonds']==[]
receipt={'cycle':17,'head':HEAD,'head_after':head(),'actor':args.actor,'round_id':args.round_id,
    'group':args.group,'status':'passed' if result.returncode==1 and power_contract_ok and not changed and external_guard_ok and head()==HEAD else 'failed',
    'proof_domain':contract['relations'][args.group],'started_at':started,'completed_at':datetime.now(UTC).isoformat(),
    'profile':str(profile),'copy':str(copy),'unit_case_count':len(cases),'bad_cases':bad,
    'pdf_exports':len(pdfs),'pdf_nodeids':species,'source_snapshot':snapshot,'instrument_snapshot':tools_snapshot,
    'files_changed_by_tests':changed,'raw':str(out/'harness.xml'),'exit_code':result.returncode,
    'power_contract_ok':power_contract_ok,'expected_failure_count':1,'expected_error_skip_count':0,'private_test_mutation':mutation,'external_guard_ok':external_guard_ok,'modules_receipt':{'path':str(out/'modules-executes.json'),'sha256':sha(out/'modules-executes.json')},
    'plateau_accepted':False,'state_changed':False,
    'test_count_limit':'B1760 19 cas répétés à fin d’exports ; B1753 témoin répété + sentinelle ; ne pas ajouter aux7780 succès distincts.',
    'actor_provenance_limit':'La réalité de l’acteur est vérifiée par root via appels collaboration, pas par ce champ ou son hash.'}
save(out/'harness-receipt.json',receipt)
save(out/'sha256-artifacts.json',{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()})
print(json.dumps({k:receipt[k] for k in ['group','status','unit_case_count','pdf_exports','actor','round_id']},ensure_ascii=False))
raise SystemExit(0 if receipt['status']=='passed' else 1)
