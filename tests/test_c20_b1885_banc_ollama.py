"""Un résultat de banc ne prouve pas l'absence de troncature sans journal."""

import importlib.util
import json
import os
import runpy
from pathlib import Path

import httpx
import pytest


@pytest.mark.parametrize(
    ("journal_lu", "troncatures", "attendu"),
    [(False, [], 1), (None, [], 1), (True, [], 0),
     (True, ["truncated = 0"], 0), (True, ["truncated = 42"], 1)],
)
def test_verdict_exige_un_journal_lu(tmp_path, journal_lu, troncatures, attendu):
    banc = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/banc_ollama_r4.py"))
    resultat = {
        "appels": [{"prompt_eval_count": 100, "journal_serveur_lu": True}],
        "tours": [
            {"evenements": [{"type": "text", "content": "Camille"}]},
            {"evenements": [{"type": "tool_result", "content": "[list_calendar_events]"},
                            {"type": "text", "content": "Ton agenda est vide."}]},
        ],
        "selection": [[], ["list_calendar_events"]],
        "charges_verifiees": [{"profil_entier": True}],
        "troncatures": troncatures,
    }
    if journal_lu is not None:
        resultat["journal_serveur_lu"] = journal_lu

    assert banc["enregistrer_verdict"](resultat, tmp_path) == attendu
    assert json.loads((tmp_path / "resultat.json").read_text())["vert"] is (attendu == 0)


@pytest.fixture
def banc_local(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1] / "scripts/banc_ollama_r4.py"
    spec = importlib.util.spec_from_file_location("banc_r4_test", source)
    banc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(banc)
    monkeypatch.setattr(banc, "ROOT", tmp_path)
    return banc


def position_journal(banc, journal):
    # Permet le rejeu du même scénario sur la base qui ne relevait que stat().
    relever = getattr(banc, "relever_journal", lambda fichier: fichier.stat())
    return relever(journal)


def test_journal_ne_lit_que_la_passe_courante(tmp_path, banc_local):
    journal = tmp_path / "serve.log"
    journal.write_text("ancienne passe : truncated = 12\n")
    position = position_journal(banc_local, journal)
    with journal.open("a") as f:
        f.write("requête reçue\ntruncated = 0\ntruncating input prompt\n")
    assert banc_local.lire_troncatures(journal, position) == {
        "journal_serveur_lu": True,
        "troncatures": ["truncated = 0", "truncating input prompt"],
    }


@pytest.mark.parametrize("incident", ["absent", "rotation", "raccourci", "exterieur"])
def test_journal_inexploitable_ne_prouve_rien(tmp_path, banc_local, incident):
    journal = tmp_path / "serve.log"
    journal.write_text("ancienne passe\n")
    position = position_journal(banc_local, journal)
    if incident == "absent":
        journal = tmp_path / "absent.log"
    elif incident == "rotation":
        journal.rename(tmp_path / "archive.log")
        journal.write_text("nouvelle passe\n")
    elif incident == "raccourci":
        journal.write_text("")
    else:
        # Le fichier devient extérieur au périmètre déclaré, sans lecture externe.
        banc_local.ROOT = tmp_path / "autre"
    assert banc_local.lire_troncatures(journal, position) == {
        "journal_serveur_lu": False, "troncatures": [],
    }


def test_journal_inchange_ne_valide_pas_la_passe(tmp_path, banc_local):
    journal = tmp_path / "serve.log"
    journal.write_text("ancienne passe : truncated = 0\n")
    position = position_journal(banc_local, journal)
    resultat = {
        "appels": [{"prompt_eval_count": 100, "journal_serveur_lu": True}],
        "tours": [
            {"evenements": [{"type": "text", "content": "Camille"}]},
            {"evenements": [{"type": "tool_result", "content": "[list_calendar_events]"},
                            {"type": "text", "content": "Ton agenda est vide."}]},
        ],
        "selection": [[], ["list_calendar_events"]],
        "charges_verifiees": [{"profil_entier": True}],
        **banc_local.lire_troncatures(journal, position),
    }

    assert banc_local.enregistrer_verdict(resultat, tmp_path) == 1
    assert resultat["journal_serveur_lu"] is False
    assert json.loads((tmp_path / "resultat.json").read_text())["vert"] is False


@pytest.mark.parametrize("trace", ["complete", "silence", "sans_rapport", "autre_appel",
                                  "sans_diagnostic", "sans_recu", "http_500"])
@pytest.mark.asyncio
async def test_journal_associe_au_transport_de_chaque_appel(tmp_path, banc_local, trace):
    from app.services.providers.base import LLMConfig, LLMProvider
    from app.services.providers.ollama import OllamaProvider

    journal = tmp_path / "serve.log"
    journal.write_text("ancienne passe : truncated = 0\n")
    body = {"model": "fictif", "messages": [{"role": "user", "content": "Bonjour"}],
            "options": {"num_ctx": 8192}, "stream": True}
    requetes = []

    def transport(request):
        requetes.append(request)
        assert json.loads(request.content) == body
        chemin = request.url.raw_path.decode()
        if trace == "autre_appel":
            chemin = "/api/chat?banc_r4=autre"
        statut = 500 if trace == "http_500" else 200
        with journal.open("a") as f:
            if trace == "sans_rapport":
                f.write("vérification périodique du serveur\n")
            elif trace != "silence":
                if trace != "sans_diagnostic":
                    f.write("slot release: id 0 | task 1 | stop processing: n_tokens = 100, truncated = 0\n")
                if trace != "sans_recu":
                    f.write(f'[GIN] date fictive | {statut} | 1s | 127.0.0.1 | POST "{chemin}"\n')
        return httpx.Response(200, json={"message": {"content": "Camille"}, "done": True,
                                        "prompt_eval_count": 100, "eval_count": 1})

    async def hook_existant(request):
        request.headers["X-Recette-Fictive"] = "conserve"

    async with httpx.AsyncClient(transport=httpx.MockTransport(transport),
                                event_hooks={"request": [hook_existant]}) as client:
        hooks = client.event_hooks["request"]
        fournisseur = OllamaProvider(LLMConfig(LLMProvider.OLLAMA, "fictif"), client)
        appels = []
        for _ in range(2):
            appel = {}
            evenements = [e async for e in banc_local.observer_flux_journal(
                OllamaProvider._stream_request, fournisseur, banc_local.ADRESSE,
                "fictif", body, appel, journal)]
            assert client.event_hooks["request"] is hooks
            assert next(e for e in evenements if e.type == "done").input_tokens == 100
            assert appel["journal_serveur_lu"] is (trace == "complete")
            appels.append(appel)
    assert len(requetes) == 2
    assert all(r.headers["X-Recette-Fictive"] == "conserve" for r in requetes)
    assert all(r.url.params["banc_r4"] for r in requetes)
    assert appels[0]["requete_journal"] != appels[1]["requete_journal"]


@pytest.mark.parametrize("preuve", [None, False])
def test_verdict_refuse_un_appel_sans_preuve(tmp_path, banc_local, preuve):
    resultat = {
        "appels": [{"prompt_eval_count": 100, "journal_serveur_lu": True},
                   {"prompt_eval_count": 100}],
        "tours": [
            {"evenements": [{"type": "text", "content": "Camille"}]},
            {"evenements": [{"type": "tool_result", "content": "[list_calendar_events]"},
                            {"type": "text", "content": "Ton agenda est vide."}]},
        ],
        "selection": [[], ["list_calendar_events"]],
        "charges_verifiees": [{"profil_entier": True}],
        "troncatures": [], "journal_serveur_lu": True,
    }
    if preuve is not None:
        resultat["appels"][1]["journal_serveur_lu"] = preuve
    assert banc_local.enregistrer_verdict(resultat, tmp_path) == 1
    assert json.loads((tmp_path / "resultat.json").read_text())["vert"] is False


def test_journal_tronque_puis_regrossi_ne_prouve_pas_la_continuite(tmp_path, banc_local):
    journal = tmp_path / "serve.log"
    journal.write_bytes(b"ancienne passe\n" * 20)
    avant = journal.stat()
    position = position_journal(banc_local, journal)
    journal.write_text("truncating input prompt\n" + "nouvelle passe sans alerte\n" * 40)
    apres = journal.stat()
    assert (apres.st_dev, apres.st_ino) == (avant.st_dev, avant.st_ino)
    assert apres.st_size > avant.st_size

    lecture = banc_local.lire_troncatures(journal, position)

    assert lecture["journal_serveur_lu"] is False


def test_journal_verifie_tout_le_prefixe(tmp_path, banc_local):
    journal = tmp_path / "serve.log"
    journal.write_bytes(b"A" * 150_000 + b"\n")
    position = position_journal(banc_local, journal)
    with journal.open("r+b") as f:
        f.seek(70_000)
        f.write(b"truncating input prompt\n")
        f.seek(0, 2)
        f.write(b"truncated = 0\n")

    assert banc_local.lire_troncatures(journal, position)["journal_serveur_lu"] is False


@pytest.mark.parametrize("ajout", [b"", b"truncated = 0\n"])
def test_journal_initialement_vide(tmp_path, banc_local, ajout):
    journal = tmp_path / "serve.log"
    journal.write_bytes(b"")
    position = position_journal(banc_local, journal)
    with journal.open("ab") as f:
        f.write(ajout)

    assert banc_local.lire_troncatures(journal, position) == {
        "journal_serveur_lu": bool(ajout),
        "troncatures": ["truncated = 0"] if ajout else [],
    }


@pytest.mark.parametrize("cible", ["feuille", "repertoire"])
@pytest.mark.parametrize("etape", ["lecture", "releve"])
def test_journal_refuse_le_lien_substitue_a_l_ouverture(tmp_path, banc_local, monkeypatch, cible, etape):
    arbre = tmp_path / "arbre-fictif"
    dossier = arbre / "logs"
    dossier.mkdir(parents=True)
    exterieur = tmp_path / "hors-perimetre-fictif"
    exterieur.mkdir()
    hors_journal = exterieur / "serve.log"
    hors_journal.write_text("debut\ntruncating DONNEE_FICTIVE_HORS_PERIMETRE\n")
    inode_exterieur = hors_journal.stat().st_ino
    monkeypatch.setattr(banc_local, "ROOT", arbre)
    journal = dossier / "serve.log"
    journal.write_text("debut\n")
    position = position_journal(banc_local, journal)
    with journal.open("a") as f:
        f.write("truncated = 0\n")
    ouvertures_exterieures = []
    substitutions = []

    def substituer():
        if substitutions:
            return
        substitutions.append(cible)
        if cible == "feuille":
            journal.rename(dossier / "archive.log")
            journal.symlink_to(hors_journal)
        else:
            dossier.rename(arbre / "archive")
            dossier.symlink_to(exterieur, target_is_directory=True)

    ouvrir_path = Path.open
    ouvrir_fd = os.open

    def path_piege(chemin, *args, **kwargs):
        if chemin == journal:
            substituer()
        f = ouvrir_path(chemin, *args, **kwargs)
        if os.fstat(f.fileno()).st_ino == inode_exterieur:
            ouvertures_exterieures.append("Path.open")
        return f

    def fd_piege(chemin, *args, **kwargs):
        nom = "serve.log" if cible == "feuille" else "logs"
        if Path(chemin) == journal or Path(chemin).name == nom:
            substituer()
        fd = ouvrir_fd(chemin, *args, **kwargs)
        if os.fstat(fd).st_ino == inode_exterieur:
            ouvertures_exterieures.append("os.open")
        return fd

    monkeypatch.setattr(Path, "open", path_piege)
    monkeypatch.setattr(os, "open", fd_piege)

    if etape == "releve":
        lecture = banc_local.relever_journal(journal)
    else:
        lecture = banc_local.lire_troncatures(journal, position)

    assert substitutions == [cible]
    assert ouvertures_exterieures == []
    assert lecture == (None if etape == "releve" else {
        "journal_serveur_lu": False, "troncatures": [],
    })


@pytest.mark.parametrize("nature", ["repertoire", "fifo", "lien", "erreur_lecture"])
def test_journal_invalide_ferme_tous_les_descripteurs(tmp_path, banc_local, monkeypatch, nature):
    journal = tmp_path / "serve.log"
    if nature == "repertoire":
        journal.mkdir()
    elif nature == "fifo":
        os.mkfifo(journal)
    elif nature == "lien":
        cible = tmp_path / "cible-fictive.log"
        cible.write_text("truncated = 0\n")
        journal.symlink_to(cible)
    else:
        journal.write_text("truncated = 0\n")

        def erreur_lecture(*_args):
            raise OSError("Lecture fictive impossible")

        monkeypatch.setattr(banc_local, "empreinte_prefixe", erreur_lecture)
    ouvrir, fermer = os.open, os.close
    ouverts = set()

    def ouverture(*args, **kwargs):
        fd = ouvrir(*args, **kwargs)
        ouverts.add(fd)
        return fd

    def fermeture(fd):
        fermer(fd)
        ouverts.discard(fd)

    monkeypatch.setattr(os, "open", ouverture)
    monkeypatch.setattr(os, "close", fermeture)
    try:
        assert banc_local.relever_journal(journal) is None
        assert not ouverts
    finally:
        for fd in list(ouverts):
            fermer(fd)


@pytest.mark.asyncio
async def test_observation_restaure_les_hooks_si_le_flux_echoue(tmp_path, banc_local):
    from types import SimpleNamespace

    journal = tmp_path / "serve.log"
    journal.write_text("ancienne passe\n")

    async def echec(*_args):
        raise RuntimeError("Échec fictif du transport")
        yield

    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: pytest.fail("Pas d'appel"))) as client:
        precedents = client.event_hooks["request"]
        appel = {}
        with pytest.raises(RuntimeError, match="Échec fictif"):
            async for _ in banc_local.observer_flux_journal(
                    echec, SimpleNamespace(client=client), banc_local.ADRESSE,
                    "fictif", {}, appel, journal):
                pass
        assert client.event_hooks["request"] is precedents
        assert appel["journal_serveur_lu"] is False
