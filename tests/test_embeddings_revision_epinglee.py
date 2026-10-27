"""B-1337 : le modèle de mémoire se charge à une révision épinglée.

Audit bêta du 27/10/2026 (A5) : le modèle d'embeddings est chargé avec
`trust_remote_code=True` sans révision. Son code (`modeling_hf_nomic_bert.py`)
vient du dépôt distant `nomic-ai/nomic-bert-2048` et s'exécute au lancement
avec les droits de l'utilisateur : si ce dépôt tiers est compromis, chaque
installation exécute le code de l'attaquant. Le journal de la 0.81 installée
le dit lui-même : « A new version of the following files was downloaded [...]
you can pin a revision ».

Les révisions épinglées sont celles auditées au cycle 15
(`docs/SECURITE-DEPENDANCES-CYCLE15.md`).
"""
import sys
import types

import pytest

REVISION_MODELE = "e9b6763023c676ca8431644204f50c2b100d9aab"
REVISION_CODE = "7710840340a098cfb869c4f65e87cf2b1b70caca"


@pytest.fixture
def chargeur_espion(monkeypatch):
    appels = []

    class FauxSentenceTransformer:
        def __init__(self, *args, **kwargs):
            appels.append((args, kwargs))

    faux_module = types.ModuleType("sentence_transformers")
    faux_module.SentenceTransformer = FauxSentenceTransformer
    monkeypatch.setitem(sys.modules, "sentence_transformers", faux_module)

    from app.services.embeddings import EmbeddingsService

    service = EmbeddingsService()
    monkeypatch.setattr(service, "_model", None)
    return service, appels


def test_modele_par_defaut_charge_a_la_revision_auditee(chargeur_espion, monkeypatch):
    from app.config import settings

    service, appels = chargeur_espion
    monkeypatch.setattr(settings, "embedding_model", "nomic-ai/nomic-embed-text-v1.5")

    _ = service.model

    (args, kwargs), = appels
    assert kwargs["revision"] == REVISION_MODELE
    assert kwargs["model_kwargs"]["code_revision"] == REVISION_CODE
    assert kwargs["config_kwargs"]["code_revision"] == REVISION_CODE
    assert kwargs["trust_remote_code"] is True


def test_modele_personnalise_ne_recoit_pas_de_code_distant(chargeur_espion, monkeypatch):
    """Un modèle configuré par l'utilisateur n'a pas de révision auditée :
    son code distant n'est pas exécuté."""
    from app.config import settings

    service, appels = chargeur_espion
    monkeypatch.setattr(settings, "embedding_model", "sentence-transformers/all-MiniLM-L6-v2")

    _ = service.model

    (args, kwargs), = appels
    assert kwargs.get("trust_remote_code") is False
    assert "revision" not in kwargs
