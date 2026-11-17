"""Banc R4 réel, séquentiel, données fictives et seul réseau 127.0.0.1:11435.

Usage : python3 scripts/banc_ollama_r4.py avant|apres [--code CHEMIN]
Le backend tourne dans un processus isolé ; HTTP ASGI sans port supplémentaire.
Les compteurs proviennent des réponses NDJSON réelles, pas d'une estimation.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANC = ROOT / '.recette-r4'  # MODELE.txt recopié du modèle fourni, sans changer le serveur.
ADRESSE = 'http://127.0.0.1:11435'
REGLE = 'Règle 3 : Toujours nommer les dossiers avec le préfixe LOUTRE-VIOLETTE.'
TEMOIN = 'PAPILLON-CUIVRE'
CONTEXTE = ('Règle 1 : Toujours répondre en français et tutoyer Camille.\n'
    + 'Projet fictif : préparer les ateliers et classer les comptes rendus.\n' * 34)
CONTEXTE = CONTEXTE[:2240] + '\n' + REGLE + '\nProjet : atelier des maquettes imaginaires.'
CONTEXTE += ' ' * (2500 - len(CONTEXTE))
MD = f'# Consignes fictives\nLe mot témoin de THERESE.md est {TEMOIN}.\n'


def lancer(args):
    code = Path(args.code).resolve() if args.code else ROOT
    if not code.is_relative_to(ROOT):
        raise ValueError('Le code doit rester dans le worktree.')
    if (code / '.env').exists():
        raise ValueError('Banc isolé : refuse de démarrer dans un dossier contenant un fichier .env.')
    dossier = ROOT / '.recette-r4' / f'banc-{args.phase}'
    dossier.mkdir(parents=True, exist_ok=True)
    for nom in ('home', 'tmp', 'data'):
        (dossier / nom).mkdir(exist_ok=True)
    donnees = tempfile.mkdtemp(prefix='profil-', dir=dossier / 'data')
    propre = {
        'PATH': f'{ROOT}/.venv/bin:/usr/bin:/bin', 'HOME': str(dossier / 'home'),
        'TMPDIR': str(dossier / 'tmp'), 'XDG_CACHE_HOME': str(dossier / 'home/cache'),
        'XDG_CONFIG_HOME': str(dossier / 'home/config'), 'PYTHONPATH': str(code / 'src/backend'),
        'THERESE_DATA_DIR': donnees, 'THERESE_ENV': 'test',
        'THERESE_SKIP_SERVICES': '1', 'THERESE_SONDE_CATALOGUE': 'off',
        'THERESE_DB_KEY': 'ad' * 32, 'OLLAMA_BASE_URL': ADRESSE,
        'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1',
        'LANG': 'C.UTF-8', 'TZ': 'Europe/Paris',
    }
    with (dossier / 'backend.log').open('w') as journal:
        return subprocess.call([str(ROOT / '.venv/bin/python'), str(Path(__file__).resolve()),
            args.phase, '--enfant', '--code', str(code)], env=propre, cwd=code,
            stdout=journal, stderr=subprocess.STDOUT)


def mesurer(args):
    code = Path(args.code).resolve() if args.code else ROOT
    if not code.is_relative_to(ROOT):
        raise ValueError('Le code doit rester dans le worktree.')
    from contextlib import asynccontextmanager

    # Interdit toute autre destination Python avant d'importer le backend.
    def garde(event, valeurs):
        if event == 'socket.connect':
            adresse = valeurs[1]
            if not isinstance(adresse, tuple) or adresse[:2] != ('127.0.0.1', 11435):
                raise PermissionError('Banc R4 : destination interdite')
        if event == 'socket.getaddrinfo' and valeurs[0] != '127.0.0.1':
            raise PermissionError('Banc R4 : résolution interdite')
    sys.addaudithook(garde)

    import httpx
    from app.main import app
    from app.models.database import close_db, get_session_context, init_db
    from app.models.entities import Preference
    from app.services import llm
    from app.services.providers.base import LLMConfig, LLMProvider
    from app.services.providers.ollama import OllamaProvider
    from fastapi.testclient import TestClient

    dossier = ROOT / '.recette-r4' / f'banc-{args.phase}'
    modele = (BANC / 'MODELE.txt').read_text().strip()
    empreinte = hashlib.sha256()
    for fichier in sorted((code / 'src/backend/app').rglob('*.py')):
        if not fichier.resolve().is_relative_to(code):
            raise ValueError('Source hors du worktree.')
        empreinte.update(str(fichier.relative_to(code)).encode())
        empreinte.update(b'\0' + fichier.read_bytes())
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=code,
        capture_output=True, text=True, check=False)
    resultat = {'empreinte_app': empreinte.hexdigest(),
        'revision_git': revision.stdout.strip() if revision.returncode == 0 else 'archive locale',
        'phase': args.phase, 'modele': modele, 'context_caracteres': len(CONTEXTE),
        'regle3_position': CONTEXTE.index('Règle 3 :'), 'appels': [], 'tours': []}

    @asynccontextmanager
    async def vie(_app):
        await init_db()
        # Une seule requête au modèle : désactiver l'extraction différée par son réglage.
        async with get_session_context() as session:
            session.add(Preference(key='auto_extract_entities', value='false'))
            await session.commit()
        yield
        await close_db()
    app.router.lifespan_context = vie
    app.state.auth_disabled = True
    # Les outils externes restent décrits pour mesurer la vraie sélection,
    # mais leur exécution est doublée : même une bibliothèque HTTP native
    # utilisée par un outil ne doit pas sortir du poste pendant le banc.
    from app.routers import chat as chat_router
    async def outil_reseau_interdit(*_args, **_kwargs):
        raise PermissionError('Banc local : seul le moteur Ollama fourni est autorisé.')
    chat_router.execute_web_search = outil_reseau_interdit
    chat_router.execute_browser_action = outil_reseau_interdit

    # Instrumentation du vrai transport : requête et réponse restent inchangées,
    # sauf think=false et température=0 communs aux deux passes pour le banc.
    flux_original = OllamaProvider._stream_request
    async def observer(self, base_url, model, body):
        assert base_url == ADRESSE
        assert body['options']['num_ctx'] <= 40960
        body['think'] = False
        body['options']['temperature'] = 0
        appel = {'num_ctx': body['options']['num_ctx'], 'outils': len(body.get('tools', [])),
            'octets_payload': len(json.dumps(body, ensure_ascii=False).encode()),
            'systeme': body['messages'][0]['content'],
            'retours_outils': [m.get('content') for m in body['messages'] if m.get('role') == 'tool']}
        resultat['appels'].append(appel)
        with (dossier / f'payload-{len(resultat["appels"])}.json').open('w') as f:
            json.dump(body, f, ensure_ascii=False, indent=2)
        async for event in flux_original(self, base_url, model, body):
            if event.type == 'done':
                appel['prompt_eval_count'] = event.input_tokens
                appel['eval_count'] = event.output_tokens
            yield event
    OllamaProvider._stream_request = observer
    with TestClient(app) as client:
        # Amorcer le cache avant sauvegarde : reproduit le changement depuis l'appli.
        llm.load_therese_md()
        r = client.post('/api/config/profile', json={'name': 'Camille Des Maquettes',
            'location': 'Bretagne imaginaire', 'context': CONTEXTE})
        assert r.status_code == 200, r.text
        r = client.post('/api/config/therese-md', json={'content': MD})
        assert r.status_code == 200, r.text
        resultat['get_profile'] = client.get('/api/config/profile').json()
        resultat['get_therese_md'] = client.get('/api/config/therese-md').json()
        service = llm.LLMService(LLMConfig(LLMProvider.OLLAMA, modele,
            base_url=ADRESSE, context_window=32768, max_tokens=384), bascule_circuit=False)
        llm._llm_service = service
        # /api/show réel, même modèle, aucune modification du banc.
        with httpx.Client(trust_env=False) as http:
            show = http.post(ADRESSE + '/api/show', json={'model': modele}, timeout=30)
            resultat['show'] = show.json()
        from app.services import memory_card_context
        alleger_original = memory_card_context.alleger_outils_locaux
        def observer_outils(context, config, tools):
            resultat.setdefault('groupes_avant', []).append([
                {'nom': t.get('function', {}).get('name'),
                 'octets': len(json.dumps(t, ensure_ascii=False, separators=(',', ':')).encode())}
                for t in tools])
            selection = alleger_original(context, config, tools)
            resultat.setdefault('selection', []).append([t['function']['name'] for t in selection])
            return selection
        memory_card_context.alleger_outils_locaux = observer_outils
        for question in ('qui suis-je ?', 'Quel est mon agenda du jour ?'):
            demande = {'message': question, 'stream': True}

            reponse = client.post('/api/chat/send', json=demande)
            evenements = [json.loads(ligne[6:]) for ligne in reponse.text.splitlines() if ligne.startswith('data: ')]
            resultat['tours'].append({'question': question, 'http': reponse.status_code,
                'evenements': evenements, 'sse': reponse.text})
            (dossier / 'resultat-intermediaire.json').write_text(json.dumps(resultat, ensure_ascii=False, indent=2))
    resultat['troncatures'] = []
    resultat['journal_serveur_lu'] = False  # Aucun journal externe au worktree n'est lu.
    resultat['charges_verifiees'] = [{
        'profil_entier': CONTEXTE.strip() in a['systeme'],
        'regle1': 'Règle 1 : Toujours répondre en français et tutoyer Camille.' in a['systeme'],
        'regle3': REGLE in a['systeme'], 'therese_md': TEMOIN in a['systeme'],
    } for a in resultat['appels']]
    raise SystemExit(enregistrer_verdict(resultat, dossier))


def enregistrer_verdict(resultat, dossier):
    textes = [''.join(e.get('content') or '' for e in t['evenements'] if e.get('type') == 'text')
              for t in resultat['tours']]
    # Le serveur écrit aussi « truncated = 0 » : conserver ces lignes brutes,
    # mais ne pas les compter comme une troncature effective.
    effectives = [ligne for ligne in resultat['troncatures']
                  if not re.search(r'\btruncated\s*=\s*0\b', ligne)]
    resultat['reponses'] = textes
    resultat['troncatures_effectives'] = effectives
    resultat['vert'] = (bool(resultat['appels']) and not effectives
        and all(isinstance(a.get('prompt_eval_count'), int) and a['prompt_eval_count'] > 0
                for a in resultat['appels'])
        and all(all(v.values()) for v in resultat['charges_verifiees'])
        and 'Camille' in textes[0] and 'list_calendar_events' in resultat['selection'][1]
        and any(e.get('type') == 'tool_result' and '[list_calendar_events]' in e.get('content', '')
                for e in resultat['tours'][1]['evenements'])
        and bool(textes[1]))
    (dossier / 'resultat.json').write_text(json.dumps(resultat, ensure_ascii=False, indent=2))
    print(json.dumps({'appels': len(resultat['appels']), 'vert': resultat['vert'],
        'troncatures_effectives': effectives}, ensure_ascii=False))
    return 0 if resultat['vert'] else 1



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['avant', 'apres'])
    parser.add_argument('--code')
    parser.add_argument('--enfant', action='store_true')
    parser.add_argument('--evaluer', action='store_true', help='Réévaluer les résultats sauvés sans requête réseau')
    arguments = parser.parse_args()
    if arguments.evaluer:
        dossier = ROOT / '.recette-r4' / f'banc-{arguments.phase}'
        donnees = json.loads((dossier / 'resultat.json').read_text())
        original = dossier / 'resultat-initial.json'
        if not original.exists():
            original.write_text(json.dumps(donnees, ensure_ascii=False, indent=2))
        raise SystemExit(enregistrer_verdict(donnees, dossier))
    elif arguments.enfant:
        mesurer(arguments)
    else:
        raise SystemExit(lancer(arguments))
