"""Banc R4 réel, séquentiel, données fictives et seul réseau 127.0.0.1:11435.

Usage : python3 scripts/banc_ollama_r4.py avant|apres [--code CHEMIN]
Le backend tourne dans un processus isolé ; HTTP ASGI sans port supplémentaire.
Les compteurs proviennent des réponses NDJSON réelles, pas d'une estimation.
Sans --journal-fd, le lanceur démarre « ollama serve » sur le port réservé au banc,
avec les modèles déjà présents dans .recette-r4/models, sans téléchargement.
Le port doit être libre. Le serveur et ses runners sont arrêtés à la sortie.
Sa sortie native est capturée par tube anonyme ; un seul appel à la fois permet
d'associer une unique fin de slot à son unique reçu GIN 200 identifié dans l'URL.
Un reçu concurrent ou plusieurs fins invalident la preuve. Un tube fourni par
--journal-fd reste soumis au préfixe request="/api/chat?banc_r4=..." : sans maîtrise
du serveur, une fin anonyme ne prouve rien. Aucun fichier rotatif ne certifie un appel.
"""
import argparse
import asyncio
import hashlib
import json
import os
import re
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from contextlib import ExitStack, contextmanager
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
BANC = ROOT / '.recette-r4'  # MODELE.txt et models : copie locale du modèle fourni.
ADRESSE = 'http://127.0.0.1:11435'
DELAI_JOURNAL = 2.0
DELAI_DEMARRAGE = 10.0
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
        'PATH': f'{ROOT}/.venv/bin:/usr/local/bin:/usr/bin:/bin', 'HOME': str(dossier / 'home'),
        'TMPDIR': str(dossier / 'tmp'), 'XDG_CACHE_HOME': str(dossier / 'home/cache'),
        'XDG_CONFIG_HOME': str(dossier / 'home/config'), 'PYTHONPATH': str(code / 'src/backend'),
        'THERESE_DATA_DIR': donnees, 'THERESE_ENV': 'test',
        'THERESE_SKIP_SERVICES': '1', 'THERESE_SONDE_CATALOGUE': 'off',
        'THERESE_DB_KEY': 'ad' * 32, 'OLLAMA_BASE_URL': ADRESSE,
        'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1',
        'LANG': 'C.UTF-8', 'TZ': 'Europe/Paris',
    }
    serveur = None
    try:
        fd = args.journal_fd
        if fd is None:
            modeles = (BANC / 'models').resolve()
            if not modeles.is_relative_to(ROOT) or not modeles.is_dir():
                raise ValueError('Copie locale des modèles requise dans .recette-r4/models.')
            serveur = subprocess.Popen(['ollama', 'serve'], cwd=code,
                env={**propre, 'OLLAMA_HOST': '127.0.0.1:11435', 'OLLAMA_MODELS': str(modeles),
                     'OLLAMA_DEBUG': '1', 'OLLAMA_NUM_PARALLEL': '1',
                     'OLLAMA_MAX_LOADED_MODELS': '1', 'OLLAMA_NO_CLOUD': '1'},
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
            fd = serveur.stdout.fileno()
        commande = [str(ROOT / '.venv/bin/python'), str(Path(__file__).resolve()),
            args.phase, '--enfant', '--code', str(code), '--journal-fd', str(fd)]
        if serveur is not None:
            commande.append('--journal-natif')
        with (dossier / 'backend.log').open('w') as journal:
            return subprocess.call(commande, pass_fds=(fd,), env=propre, cwd=code,
                stdout=journal, stderr=subprocess.STDOUT)
    finally:
        if serveur is not None:
            try:
                os.killpg(serveur.pid, signal.SIGTERM)
                serveur.wait(timeout=5)
            except ProcessLookupError:
                serveur.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(serveur.pid, signal.SIGKILL)
                serveur.wait(timeout=5)
            finally:
                serveur.stdout.close()


def mesurer(args):
    if args.journal_fd is None:
        raise ValueError('Preuve serveur requise : fournir le tube via --journal-fd.')
    with CaptureJournal(args.journal_fd) as journal:
        if getattr(args, 'journal_natif', False):
            limite = time.monotonic() + DELAI_DEMARRAGE
            while b'Listening on 127.0.0.1:11435' not in (journal.lire() or b''):
                if journal.erreur or time.monotonic() >= limite:
                    raise RuntimeError('Le serveur dédié du banc ne s’est pas déclaré prêt.')
                time.sleep(0.01)
            journal.natif = True
        return mesurer_capture(args, journal)


def mesurer_capture(args, journal_serveur):
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
    position_journal = relever_journal(journal_serveur)
    empreinte = hashlib.sha256()
    for fichier in sorted((code / 'src/backend/app').rglob('*.py')):
        if not fichier.resolve().is_relative_to(code):
            raise ValueError('Source hors du worktree.')
        empreinte.update(str(fichier.relative_to(code)).encode())
        empreinte.update(b'\0' + fichier.read_bytes())
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=code,
        capture_output=True, text=True, check=False)
    resultat = {'empreinte_app': empreinte.hexdigest(), 'preuve_journal_v': 2,
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
    # sauf think=false, température=0 et identifiant HTTP de recette.
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
        async for event in observer_flux_journal(
                flux_original, self, base_url, model, body, appel, journal_serveur):
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
    resultat.update(lire_troncatures(journal_serveur, position_journal))
    resultat['charges_verifiees'] = [{
        'profil_entier': CONTEXTE.strip() in a['systeme'],
        'regle1': 'Règle 1 : Toujours répondre en français et tutoyer Camille.' in a['systeme'],
        'regle3': REGLE in a['systeme'], 'therese_md': TEMOIN in a['systeme'],
    } for a in resultat['appels']]
    raise SystemExit(enregistrer_verdict(resultat, dossier))


class CaptureJournal:
    """Conserver le flux du serveur, sans chemin réouvrable ni octets effaçables.

    Le lanceur conserve l'écriture pour le serveur et transmet exclusivement cette
    extrémité de lecture au banc. Le thread évite de bloquer le serveur si le tube
    se remplit pendant une réponse HTTP ; les relevés drainent aussi les octets
    disponibles pour ne pas dépendre de l'ordonnancement du thread.
    """

    def __init__(self, fd):
        info = os.fstat(fd)
        lecture, ecriture = os.pipe()
        try:
            device_tube = os.fstat(lecture).st_dev
        finally:
            os.close(lecture)
            os.close(ecriture)
        # Linux compte un lien pour un tube anonyme ; son périphérique est
        # celui de pipefs, distinct de celui d'un FIFO nommé dans le worktree.
        if (not stat.S_ISFIFO(info.st_mode) or info.st_dev != device_tube
                or info.st_nlink > 1):
            raise ValueError('La capture exige un tube anonyme, sans lien physique.')
        self.fd = os.dup(fd)
        self.bloquant = os.get_blocking(self.fd)
        os.set_blocking(self.fd, False)
        self.octets = bytearray()
        self.verrou = threading.Lock()
        self.arret = threading.Event()
        self.erreur = False
        self.natif = False
        self.thread = threading.Thread(target=self._collecter, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_args):
        self.arret.set()
        self.thread.join()
        os.set_blocking(self.fd, self.bloquant)
        os.close(self.fd)
        self.erreur = True

    def _collecter(self):
        while not self.arret.wait(0.01):
            self.lire()

    def lire(self):
        with self.verrou:
            if self.erreur:
                return None
            try:
                while bloc := os.read(self.fd, 65536):
                    self.octets.extend(bloc)
            except BlockingIOError:
                pass
            except OSError:
                self.erreur = True
            return None if self.erreur else bytes(self.octets)


@contextmanager
def ouvrir_journal(journal):
    """Ancrer chaque composant au répertoire ouvert ; aucun lien n'est suivi."""
    parties = journal.relative_to(ROOT).parts
    if not parties or '..' in parties:
        raise ValueError('Journal hors du worktree.')
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    with ExitStack() as pile:
        repertoire = os.open(ROOT, flags | os.O_DIRECTORY)
        pile.callback(os.close, repertoire)
        ancres = []
        for nom in parties[:-1]:
            parent = repertoire
            repertoire = os.open(nom, flags | os.O_DIRECTORY, dir_fd=parent)
            pile.callback(os.close, repertoire)
            ancres.append((parent, nom, repertoire))
        fd = os.open(parties[-1], flags, dir_fd=repertoire)
        pile.callback(os.close, fd)
        ancres.append((repertoire, parties[-1], fd))
        ouvert = os.fstat(fd)
        if not stat.S_ISREG(ouvert.st_mode) or ouvert.st_nlink != 1:
            raise OSError('Le journal doit être un fichier ordinaire sans autre lien.')
        with os.fdopen(fd, 'rb', closefd=False) as f:
            yield f
        for parent, nom, enfant in ancres:
            actuel = os.stat(nom, dir_fd=parent, follow_symlinks=False)
            ouvert = os.fstat(enfant)
            if enfant == fd and ouvert.st_nlink != 1:
                raise OSError('Lien physique ajouté pendant la lecture.')
            if (actuel.st_dev, actuel.st_ino, actuel.st_mode) != (
                    ouvert.st_dev, ouvert.st_ino, ouvert.st_mode):
                raise OSError('Journal remplacé pendant la lecture.')


def etat_journal(position):
    # atime peut changer à la simple lecture ; conserver mtime/ctime à la nanoseconde.
    return (position.st_dev, position.st_ino, position.st_size,
            position.st_mtime_ns, position.st_ctime_ns)


def relever_journal(journal):
    if isinstance(journal, CaptureJournal):
        contenu = journal.lire()
        return None if contenu is None else (journal, len(contenu))
    try:
        with ouvrir_journal(journal) as f:
            position = os.fstat(f.fileno())
            empreinte = empreinte_prefixe(f, position.st_size)
            if etat_journal(os.fstat(f.fileno())) == etat_journal(position):
                return position, empreinte
    except (OSError, ValueError):
        pass
    return None


def empreinte_prefixe(f, taille):
    """Une copie suivie d'une troncature peut garder inode et taille finale."""
    empreinte = hashlib.sha256()
    while taille:
        bloc = f.read(min(taille, 65536))
        if not bloc:
            raise OSError('Journal raccourci pendant la lecture.')
        empreinte.update(bloc)
        taille -= len(bloc)
    return empreinte.digest()


async def observer_flux_journal(flux, fournisseur, base_url, modele, body, appel, journal):
    """Rattacher les traces au véritable transport, sans changer le corps envoyé."""
    position = relever_journal(journal)
    identifiant = uuid4().hex
    requete = '/api/chat?banc_r4=' + identifiant
    envoyee = False

    async def marquer(request):
        nonlocal envoyee
        if request.method == 'POST' and str(request.url) == base_url + '/api/chat':
            request.url = request.url.copy_add_param('banc_r4', identifiant)
            envoyee = True

    hooks = fournisseur.client.event_hooks
    precedents = hooks['request']
    hooks['request'] = [*precedents, marquer]
    appel['journal_serveur_lu'] = False
    try:
        async for event in flux(fournisseur, base_url, modele, body):
            yield event
    finally:
        hooks['request'] = precedents
        preuve = lire_troncatures(journal, position, requete=requete)
        if envoyee and isinstance(journal, CaptureJournal) and position is not None:
            boucle = asyncio.get_running_loop()
            limite = boucle.time() + DELAI_JOURNAL
            while not preuve['journal_serveur_lu'] and not journal.erreur:
                restant = limite - boucle.time()
                if restant <= 0:
                    break
                await asyncio.sleep(min(0.01, restant))
                preuve = lire_troncatures(journal, position, requete=requete)
        appel['journal_serveur_lu'] = envoyee and preuve['journal_serveur_lu']
        appel['requete_journal'] = requete


def lire_troncatures(journal, position, requete=None):
    """Lire seulement cette passe, sans sortir du worktree ni ignorer une rotation."""
    resultat = {'troncatures': [], 'journal_serveur_lu': False}
    if position is None:
        return resultat
    capture = isinstance(journal, CaptureJournal)
    if capture:
        origine, debut = position
        contenu = journal.lire()
        if origine is not journal or contenu is None:
            return resultat
        ajout = contenu[debut:]
    else:
        ajout = lire_ajout_fichier(journal, position)
    if not ajout or not ajout.endswith(b'\n'):
        return resultat
    lignes = ajout.decode(errors='replace').splitlines()
    resultat['troncatures'] = [ligne for ligne in lignes if 'truncat' in ligne.lower()]
    resultat['journal_serveur_lu'] = bool(lignes)
    if requete is not None:
        recu = r'\[GIN\].*\|\s*200\s*\|[^|]*\|[^|]*\|\s*POST\s+"' + re.escape(requete) + r'"\s*'
        fin = (r'(?:^|\s)request="' + re.escape(requete)
               + r'"\s+.*\bstop processing:.*\btruncated\s*=\s*\d+\s*$')
        resultat['journal_serveur_lu'] = (capture
            and sum(bool(re.fullmatch(recu, ligne)) for ligne in lignes) == 1
            and sum(bool(re.search(fin, ligne)) for ligne in lignes) == 1)
        if capture and journal.natif:
            fin_native = (r'^slot\s+release:\s+id\s+\d+\s*\|\s*task\s+\d+\s*\|\s*'
                          r'stop processing:.*\btruncated\s*=\s*\d+\s*$')
            resultat['journal_serveur_lu'] = (
                sum('[GIN]' in ligne for ligne in lignes) == 1
                and sum(bool(re.fullmatch(recu, ligne)) for ligne in lignes) == 1
                and sum('stop processing:' in ligne for ligne in lignes) == 1
                and sum(bool(re.fullmatch(fin_native, ligne)) for ligne in lignes) == 1)
    return resultat


def lire_ajout_fichier(journal, position):
    """Lecture diagnostique seulement : un fichier rotatif ne prouve aucun appel."""
    position, empreinte = position
    try:
        with ouvrir_journal(journal) as f:
            actuel = os.fstat(f.fileno())
            if (actuel.st_dev, actuel.st_ino) != (position.st_dev, position.st_ino):
                return None
            if actuel.st_size <= position.st_size:
                return None
            if empreinte_prefixe(f, position.st_size) != empreinte:
                return None
            ajout = f.read(actuel.st_size - position.st_size)
            if (len(ajout) != actuel.st_size - position.st_size
                    or etat_journal(os.fstat(f.fileno())) != etat_journal(actuel)):
                return None
    except (OSError, ValueError):
        return None
    return ajout


def enregistrer_verdict(resultat, dossier):
    textes = [''.join(e.get('content') or '' for e in t['evenements'] if e.get('type') == 'text')
              for t in resultat['tours']]
    # Un compteur nul n'annule ni une alerte ni un autre compteur de la ligne.
    # Retirer seulement ces valeurs bénignes avant de chercher les troncatures.
    effectives = [ligne for ligne in resultat['troncatures']
                  if re.search(r'truncat', re.sub(r'\btruncated\s*=\s*0\b', '', ligne,
                                                flags=re.I), re.I)]
    resultat['reponses'] = textes
    resultat['troncatures_effectives'] = effectives
    resultat['vert'] = (bool(resultat['appels']) and resultat.get('preuve_journal_v') == 2
        and resultat.get('journal_serveur_lu') is True
        and not effectives
        and all(a.get('journal_serveur_lu') is True for a in resultat['appels'])
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
    parser.add_argument('--journal-fd', type=int, help='Descripteur hérité du tube anonyme de sortie du serveur')
    parser.add_argument('--journal-natif', action='store_true', help=argparse.SUPPRESS)
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
