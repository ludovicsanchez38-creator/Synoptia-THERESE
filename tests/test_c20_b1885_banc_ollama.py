"""Un résultat de banc ne prouve pas l'absence de troncature sans journal."""

import importlib.util
import json
import runpy
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("journal_lu", "troncatures", "attendu"),
    [(False, [], 1), (None, [], 1), (True, [], 0),
     (True, ["truncated = 0"], 0), (True, ["truncated = 42"], 1)],
)
def test_verdict_exige_un_journal_lu(tmp_path, journal_lu, troncatures, attendu):
    banc = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/banc_ollama_r4.py"))
    resultat = {
        "appels": [{"prompt_eval_count": 100}],
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


def test_journal_ne_lit_que_la_passe_courante(tmp_path, banc_local):
    journal = tmp_path / "serve.log"
    journal.write_text("ancienne passe : truncated = 12\n")
    position = journal.stat()
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
    position = journal.stat()
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
