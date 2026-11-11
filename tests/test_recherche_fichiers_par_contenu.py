"""`search_files` ne rend plus zéro pour un mot qui figure dans un fichier.

Signalement d'un testeur (11/11/2026, 0.83) : l'outil de l'agent rendait
`found: false` pour un mot présent mot pour mot dans un fichier indexé, et
pour une demande formulée en phrase (« le fichier de veille des
subventions »). Le catalogue ne comparait que la demande ENTIÈRE au NOM du
fichier ; le contenu indexé n'était jamais consulté, alors que la route
`/api/memory/search` le fait depuis B-1040. Un petit modèle local qui reçoit
zéro invente un contenu plausible.

Le rapprochement par mots ne joue que si le nom entier n'a rien donné, garde
la cloison du catalogue et ne fouille le contenu que si les documents peuvent
partir vers le fournisseur du tour (même accord que `read_file`).
"""
import json

import pytest
from app.config import settings
from app.models.entities import FileMetadata
from app.services import memory_tools
from app.services.memory_tools import execute_memory_tool
from app.services.providers.base import LLMConfig, LLMProvider
from app.services.qdrant import QdrantService
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

LOCAL = LLMConfig(LLMProvider.OLLAMA, "local")


def _index_en_memoire(taille: int = 1) -> QdrantService:
    service = object.__new__(QdrantService)
    service._client = QdrantClient(location=":memory:")
    service._initialized = True
    service._client.create_collection(
        settings.qdrant_collection,
        vectors_config=VectorParams(size=taille, distance=Distance.COSINE),
    )
    return service


@pytest.fixture
def index(monkeypatch):
    service = _index_en_memoire()
    monkeypatch.setattr(memory_tools, "get_qdrant_service", lambda: service)
    yield service
    service._client.close()


_compteur = iter(range(1, 10_000))


async def _fichier(db_session, index, *, nom, textes, scope="global", scope_id=None, chunks=None):
    fichier = FileMetadata(
        path=f"/depot/{scope}/{scope_id or 'general'}/{nom}", name=nom,
        extension="." + nom.rsplit(".", 1)[-1], size=1024,
        chunk_count=len(textes) if chunks is None else chunks,
        scope=scope, scope_id=scope_id,
    )
    db_session.add(fichier)
    await db_session.commit()
    if textes:
        index._client.upsert(settings.qdrant_collection, points=[
            PointStruct(id=next(_compteur), vector=[1.0], payload={
                "type": "file", "entity_id": fichier.id, "text": texte,
                "scope": scope, "scope_id": scope_id,
            })
            for texte in textes
        ])
    return fichier.id


async def _chercher(db_session, query, config=LOCAL, **perimetre) -> dict:
    brut = await execute_memory_tool(
        "search_files", {"query": query}, db_session, llm_config=config, **perimetre
    )
    return json.loads(brut)


VEILLE = [
    "VEILLE SUBVENTIONS - relevé automatique. Appel à projets régional Occitanie.",
    "Le dossier concerne la modernisation des bâtiments et l'irrigation économe.",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("demande", ["irrigation", "Occitanie", "IRRIGATION", "irrigation econome"])
async def test_un_mot_du_contenu_retrouve_le_fichier(db_session, index, demande):
    """Le cas du signalement : le mot est dans le fichier, pas dans son nom."""
    identifiant = await _fichier(db_session, index, nom="veille-subventions.txt", textes=VEILLE)
    await _fichier(db_session, index, nom="contexte.md", textes=["Une ferme dans le Tarn."])

    r = await _chercher(db_session, demande)

    assert r["found"] is True
    assert [d["id"] for d in r["documents"]] == [identifiant]
    assert r["documents"][0]["trouve_dans"] == "contenu"
    assert r["total"] == 1
    # Aucun extrait : le contenu se lit par `read_file`, sous son enveloppe.
    assert "irrigation" not in json.dumps(r["documents"], ensure_ascii=False).lower()


@pytest.mark.asyncio
@pytest.mark.parametrize("demande", [
    "fichier de veille des subventions",
    "le document veille subventions du Tarn",
    "subventions veille",
])
async def test_une_demande_en_phrase_retrouve_le_fichier_par_les_mots_de_son_nom(
    db_session, index, demande
):
    """Un modèle local écrit une phrase, pas un nom de fichier."""
    identifiant = await _fichier(db_session, index, nom="veille-subventions.txt", textes=VEILLE)
    await _fichier(db_session, index, nom="regles.md", textes=["Toujours répondre en français."])

    r = await _chercher(db_session, demande)

    assert r["documents"][0]["id"] == identifiant
    assert r["documents"][0]["trouve_dans"] == "nom"
    assert "regles.md" not in [d["nom"] for d in r["documents"]]


@pytest.mark.asyncio
async def test_le_nom_passe_devant_le_contenu_et_le_plus_de_mots_devant_le_moins(db_session, index):
    par_contenu = await _fichier(db_session, index, nom="notes.md",
                                 textes=["La veille du Tarn est faite chaque lundi."])
    un_mot = await _fichier(db_session, index, nom="veille-concurrence.txt", textes=["Rien à signaler."])
    deux_mots = await _fichier(db_session, index, nom="veille-subventions.txt", textes=VEILLE)

    r = await _chercher(db_session, "veille des subventions du Tarn")

    assert [d["id"] for d in r["documents"]] == [deux_mots, un_mot, par_contenu]
    assert [d["trouve_dans"] for d in r["documents"]] == ["nom", "nom", "contenu"]
    assert r["total"] == 3 and r["affiches"] == 3


@pytest.mark.asyncio
async def test_le_contenu_d_un_autre_projet_ne_sort_pas(db_session, index):
    """La cloison est celle du catalogue : SQL, jamais le payload vectoriel."""
    du_projet = await _fichier(db_session, index, nom="contrat.md", scope="project",
                               scope_id="p-a", textes=["Clause zéphyr : acompte de 30 %."])
    await _fichier(db_session, index, nom="piece.md", scope="conversation",
                   scope_id="c-9", textes=["La clause zéphyr en pièce jointe."])

    dans_le_projet = await _chercher(db_session, "zéphyr", scope="project", scope_id="p-a")
    assert [d["id"] for d in dans_le_projet["documents"]] == [du_projet]

    for perimetre in ({}, {"scope": "project", "scope_id": "p-b"}, {"scope": "global"},
                      {"conversation_id": "c-1"}):
        r = await _chercher(db_session, "zéphyr", **perimetre)
        assert r["documents"] == [] and r["total"] == 0, perimetre
        assert "zéphyr" not in json.dumps(r, ensure_ascii=False).replace('"query"', "")


@pytest.mark.asyncio
async def test_sans_accord_documents_le_contenu_n_est_pas_fouille(db_session, index, monkeypatch):
    """Dire « ce fichier contient ce mot » à un fournisseur en ligne, c'est
    déjà lui parler du contenu : même accord que `read_file` (B-1201)."""
    identifiant = await _fichier(db_session, index, nom="veille-subventions.txt", textes=VEILLE)
    en_ligne = LLMConfig(LLMProvider.ANTHROPIC, "modele-fictif")

    monkeypatch.setattr("app.services.consentements.accord_valide", lambda finalite, fournisseur: False)
    refuse = await _chercher(db_session, "irrigation", config=en_ligne)
    assert refuse["documents"] == [] and refuse["found"] is False
    # Le nom, lui, reste un catalogue : il sortait déjà avant ce correctif.
    par_nom = await _chercher(db_session, "le fichier de veille", config=en_ligne)
    assert [d["id"] for d in par_nom["documents"]] == [identifiant]

    monkeypatch.setattr("app.services.consentements.accord_valide",
                        lambda finalite, fournisseur: (finalite, fournisseur) == ("documents", "anthropic"))
    accorde = await _chercher(db_session, "irrigation", config=en_ligne)
    assert [d["id"] for d in accorde["documents"]] == [identifiant]


@pytest.mark.asyncio
async def test_un_index_en_panne_laisse_le_catalogue_repondre(db_session, monkeypatch):
    from unittest.mock import AsyncMock, MagicMock

    en_panne = MagicMock()
    en_panne.async_fichiers_contenant = AsyncMock(side_effect=RuntimeError("index fictif en panne"))
    monkeypatch.setattr(memory_tools, "get_qdrant_service", lambda: en_panne)
    db_session.add(FileMetadata(path="/depot/veille.txt", name="veille.txt", extension=".txt",
                                size=10, chunk_count=2, scope="global"))
    await db_session.commit()

    absent = await _chercher(db_session, "irrigation")
    assert absent["found"] is False and absent["documents"] == []
    present = await _chercher(db_session, "ma veille hebdomadaire")
    assert [d["nom"] for d in present["documents"]] == ["veille.txt"]
    assert en_panne.async_fichiers_contenant.await_count == 2


@pytest.mark.asyncio
async def test_un_nom_entier_garde_le_comportement_du_catalogue(db_session, index):
    """Le rapprochement ne joue que si le nom entier n'a rien donné."""
    exact = await _fichier(db_session, index, nom="veille-subventions.txt", textes=VEILLE)
    await _fichier(db_session, index, nom="notes.md", textes=["La veille subventions est à jour."])

    r = await _chercher(db_session, "veille subventions")

    assert [d["id"] for d in r["documents"]] == [exact]
    assert "trouve_dans" not in r["documents"][0] and "note" not in r


@pytest.mark.asyncio
@pytest.mark.parametrize("demande", ["%", "le de la", "xy", "introuvable-nulle-part"])
async def test_une_demande_sans_mot_utile_ne_rend_rien(db_session, index, demande):
    await _fichier(db_session, index, nom="rapport.md", textes=["Le rapport de la semaine."])

    r = await _chercher(db_session, demande)

    assert r["found"] is False and r["documents"] == []


@pytest.mark.asyncio
async def test_un_fichier_sans_fragment_consigne_ne_sort_pas_par_son_contenu(db_session, index):
    """`chunk_count = 0` : la base dit que l'index est vide, on la croit."""
    await _fichier(db_session, index, nom="casse.txt", textes=["Un zéphyr orphelin."], chunks=0)

    r = await _chercher(db_session, "zéphyr")

    assert r["documents"] == []


def test_fichiers_contenant_compte_les_termes_en_un_seul_parcours():
    from unittest.mock import patch

    service = _index_en_memoire()
    try:
        service._client.upsert(settings.qdrant_collection, points=[
            PointStruct(id=1, vector=[1.0], payload={"type": "file", "entity_id": "a", "text": "Irrigation économe."}),
            PointStruct(id=2, vector=[1.0], payload={"type": "file", "entity_id": "a", "text": "Plafond des aides."}),
            PointStruct(id=3, vector=[1.0], payload={"type": "file", "entity_id": "b", "text": "Les tarifsuffixe et l'aide."}),
            PointStruct(id=4, vector=[1.0], payload={"type": "contact", "entity_id": "c", "text": "Irrigation."}),
            PointStruct(id=5, vector=[1.0], payload={"type": "file", "entity_id": "d", "text": "Irrigation\n  econome."}),
        ])
        with patch.object(service._client, "scroll", wraps=service._client.scroll) as parcours:
            trouves = service.fichiers_contenant(["irrigation econome", "irrigation", "aides", "tarif"])
        assert parcours.call_count == 1
        # Accents et casse repliés, frontières de mot gardées (« tarif » n'est
        # pas « tarifsuffixe », « aides » n'est pas « aide »), fiches écartées.
        assert trouves == {"a": 3, "d": 2}
        assert service.fichiers_contenant(["irrigation"], parmi={"d"}) == {"d": 1}
        assert service.fichiers_contenant(["irrigation"], parmi=set()) == {}
        assert service.fichiers_contenant(["  ", ""]) == {}
        service._client.upsert(settings.qdrant_collection, points=[
            PointStruct(id=6, vector=[1.0], payload={"type": "file", "entity_id": "e", "text": "客户在北京工作。"}),
        ])
        assert service.fichiers_contenant(["北京"]) == {"e": 1}
    finally:
        service._client.close()


@pytest.mark.asyncio
async def test_chemin_reel_indexation_puis_outil(db_session, tmp_path, monkeypatch):
    """Écriture réelle (découpage, payload, base) puis lecture par l'outil :
    seul le calcul d'embeddings est factice."""
    from app.routers import files
    from app.services import indexation, qdrant

    service = _index_en_memoire(taille=4)
    monkeypatch.setattr(qdrant, "embed_text", lambda texte: [1.0, 0.0, 0.0, 0.0])
    monkeypatch.setattr(qdrant, "embed_texts", lambda textes: [[1.0, 0.0, 0.0, 0.0] for _ in textes])
    monkeypatch.setattr(indexation, "get_qdrant_service", lambda: service)
    monkeypatch.setattr(memory_tools, "get_qdrant_service", lambda: service)
    chemin = tmp_path / "veille-subventions.txt"
    chemin.write_text(
        "\n\n".join(
            f"Dispositif {i} : la veille relève les aides ouvertes, le plafond et le guichet "
            f"instructeur. Le dossier {i} concerne l'irrigation économe des exploitations du Tarn."
            for i in range(1, 40)
        ),
        encoding="utf-8",
    )
    try:
        indexe = await files.index_payload(path=str(chemin))
        assert indexe.chunk_count > 1

        par_contenu = await _chercher(db_session, "guichet instructeur")
        assert [d["id"] for d in par_contenu["documents"]] == [indexe.id]
        assert par_contenu["documents"][0]["trouve_dans"] == "contenu"
        par_phrase = await _chercher(db_session, "le fichier de veille des subventions")
        assert [d["id"] for d in par_phrase["documents"]] == [indexe.id]
    finally:
        service._client.close()
