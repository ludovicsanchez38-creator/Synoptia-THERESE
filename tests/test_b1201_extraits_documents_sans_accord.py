"""B-1201 : un extrait de document indexé ne part pas sans l'accord « documents ».

Audit du cycle 13 (renfort RGPD), confirmé par l'audit bêta du 27/10/2026 :
l'interface fait de l'envoi d'un document une finalité distincte (« un devis
client, un contrat, un dossier médical »). Mais avec la mémoire activée,
_get_memory_context injectait dans le prompt système l'extrait de tout fichier
indexé jugé pertinent. Accord « llm » donné pour Anthropic, aucun accord
« documents », un contrat indexé depuis la vue Fichiers : la question « quelles
conditions de paiement pour Dupont ? » envoyait un extrait du contrat chez
Anthropic.

Règle posée : vers un fournisseur en ligne, les extraits de fichiers ne sont
injectés qu'avec l'accord « documents » pour CE fournisseur. Les contacts et
projets restent régis par l'accord du chat ; un modèle local reçoit tout.
"""
import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

TEXTE_CONTRAT = "Conditions de paiement Dupont : 45 jours fin de mois, pénalités 12 %."


def _config(fournisseur: str, modele: str = "modele", base_url: str | None = None):
    return SimpleNamespace(provider=SimpleNamespace(value=fournisseur), model=modele, base_url=base_url)


class TestLaRegle:
    def test_un_modele_local_recoit_les_documents(self):
        from app.services.memory_card_context import documents_autorises

        assert documents_autorises(_config("ollama", "mistral-nemo"), []) is True

    def test_un_fournisseur_en_ligne_sans_accord_documents_ne_les_recoit_pas(self):
        from app.services.memory_card_context import documents_autorises

        assert documents_autorises(_config("anthropic"), ["llm:anthropic"]) is False

    def test_l_accord_documents_du_bon_fournisseur_les_ouvre(self):
        from app.services.memory_card_context import documents_autorises

        assert documents_autorises(_config("anthropic"), ["llm:anthropic", "documents:anthropic"]) is True

    def test_l_accord_documents_d_un_autre_fournisseur_ne_suffit_pas(self):
        from app.services.memory_card_context import documents_autorises

        assert documents_autorises(_config("openai"), ["documents:anthropic"]) is False

    def test_un_ollama_distant_compte_comme_un_fournisseur_en_ligne(self):
        from app.services.memory_card_context import documents_autorises

        distant = _config("ollama", "mistral-nemo", "https://ollama.exemple.fr")
        assert documents_autorises(distant, []) is False
        assert documents_autorises(distant, ["documents:ollama-cloud"]) is True

    def test_une_configuration_incomplete_ne_casse_pas_le_message(self):
        """Constat des portes du 27/10 : un faux fournisseur sans base_url faisait échouer le chat."""
        from app.services.memory_card_context import documents_autorises

        sans_url = SimpleNamespace(provider=SimpleNamespace(value="ollama"), model="test")
        assert documents_autorises(sans_url, []) is True, "Ollama sans adresse = local par défaut"
        illisible = SimpleNamespace(provider=None)
        assert documents_autorises(illisible, ["documents:anthropic"]) is False

    def test_sans_liste_d_accords_rien_ne_part(self):
        from app.services.memory_card_context import documents_autorises

        assert documents_autorises(_config("mistral"), None) is False


def _faux_qdrant(monkeypatch, chat_router):
    resultats = [
        {"type": "file", "text": TEXTE_CONTRAT, "score": 0.8,
         "metadata": {"name": "contrat-dupont.pdf", "chunk_index": 0, "total_chunks": 1}},
        {"type": "contact", "text": "Jean Dupont, gérant", "score": 0.7, "metadata": {"name": "Jean Dupont"}},
    ]

    async def faux_search(**_kwargs):
        return resultats

    faux = type("Faux", (), {"async_search": staticmethod(faux_search)})()
    monkeypatch.setattr(chat_router, "get_qdrant_service", lambda: faux)


class TestLeContexteMemoire:
    @pytest.mark.asyncio
    async def test_sans_accord_documents_l_extrait_du_contrat_n_est_pas_injecte(self, monkeypatch):
        from app.routers import chat as chat_router

        _faux_qdrant(monkeypatch, chat_router)

        contexte = await chat_router._get_memory_context(
            "quelles conditions de paiement pour Dupont ?", inclure_fichiers=False
        )

        assert TEXTE_CONTRAT not in (contexte or "")
        assert "contrat-dupont.pdf" not in (contexte or ""), "même le nom du document est une donnée"
        assert "Jean Dupont" in (contexte or ""), "les contacts restent régis par l'accord du chat"

    @pytest.mark.asyncio
    async def test_avec_accord_documents_l_extrait_est_injecte(self, monkeypatch):
        from app.routers import chat as chat_router

        _faux_qdrant(monkeypatch, chat_router)

        contexte = await chat_router._get_memory_context(
            "quelles conditions de paiement pour Dupont ?", inclure_fichiers=True
        )

        assert TEXTE_CONTRAT in (contexte or "")


def _appels(nom_fonction: str) -> list[ast.Call]:
    source = Path(__file__).resolve().parents[1] / "src/backend/app/routers/chat.py"
    arbre = ast.parse(source.read_text(encoding="utf-8"))
    return [
        n for n in ast.walk(arbre)
        if isinstance(n, ast.Call) and getattr(n.func, "id", getattr(n.func, "attr", "")) == nom_fonction
    ]


def test_les_deux_chemins_du_chat_decident_selon_l_accord_documents():
    """Flux et non-flux : chaque appel transmet la décision, aucun ne garde le défaut."""
    appels = _appels("_get_memory_context")
    assert len(appels) == 2
    for appel in appels:
        mots = {k.arg: k.value for k in appel.keywords}
        assert "inclure_fichiers" in mots, f"ligne {appel.lineno} : l'appel garde le défaut"
        valeur = ast.unparse(mots["inclure_fichiers"])
        assert "documents_autorises" in valeur, f"ligne {appel.lineno} : {valeur}"
