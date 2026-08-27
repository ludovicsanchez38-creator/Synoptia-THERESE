"""D6 : le modèle doit pouvoir distinguer « rien ne correspond » de
« rien n'est consultable ici ».

Quand une conversation n'est rattachée à aucun projet, elle applique le
moindre privilège : seuls les documents généraux sont consultables. Les
fichiers d'un dossier synchronisé, eux, portent un périmètre de projet et
restent hors de portée.

Jusqu'ici, les deux situations produisaient exactement le même silence : le
bloc de contexte disparaissait, et Thérèse répondait comme si ces documents
n'existaient pas. Quelqu'un qui a indexé mille fichiers mérite mieux qu'une
réponse à côté.

La mention porte sur le PÉRIMÈTRE, jamais sur le contenu : elle ne franchit
pas la cloison qu'elle décrit.
"""
import pytest
from app.models.entities import Conversation, FileMetadata
from app.routers.chat import _get_memory_context


async def _conversation_non_rattachee(db_session) -> str:
    """Le cas réel : une conversation ordinaire, qu'on n'a rattachée à rien.

    Sans conversation, le périmètre vaut (None, None) — aucune cloison, donc
    rien n'est hors de portée. Le parcours qui nous intéresse est celui d'une
    vraie conversation au moindre privilège.
    """
    conversation = Conversation(title="Sans projet")
    db_session.add(conversation)
    await db_session.commit()
    return conversation.id


@pytest.mark.asyncio
async def test_le_modele_apprend_que_des_documents_sont_hors_perimetre(
    db_session, monkeypatch
):
    async def _rien(*args, **kwargs):
        return []

    monkeypatch.setattr(
        "app.services.qdrant.get_qdrant_service",
        lambda: type("Q", (), {"async_search": staticmethod(_rien)})(),
    )

    db_session.add(
        FileMetadata(
            path="/dossier/index.html",
            name="index.html",
            extension="html",
            size=120,
            chunk_count=3,
            scope="project",
            scope_id="projet-a",
        )
    )
    await db_session.commit()

    contexte = await _get_memory_context(
        "les documents indexés",
        conversation_id=await _conversation_non_rattachee(db_session),
        session=db_session,
    )

    assert contexte is not None, "le modèle ne doit pas rester sans explication"
    assert "hors du périmètre" in contexte or "hors de portée" in contexte
    # La mention décrit la cloison, elle ne la franchit pas.
    assert "index.html" not in contexte


@pytest.mark.asyncio
async def test_aucune_mention_quand_rien_nest_hors_perimetre(db_session, monkeypatch):
    async def _rien(*args, **kwargs):
        return []

    monkeypatch.setattr(
        "app.services.qdrant.get_qdrant_service",
        lambda: type("Q", (), {"async_search": staticmethod(_rien)})(),
    )

    contexte = await _get_memory_context(
        "bonjour",
        conversation_id=await _conversation_non_rattachee(db_session),
        session=db_session,
    )

    assert contexte is None


@pytest.mark.asyncio
async def test_un_fichier_dont_lindexation_a_echoue_ne_compte_pas(
    db_session, monkeypatch
):
    """`chunk_count = 0` signale une indexation qui n'a rien écrit dans Qdrant.

    Le compter reviendrait à promettre des documents introuvables.
    """
    async def _rien(*args, **kwargs):
        return []

    monkeypatch.setattr(
        "app.services.qdrant.get_qdrant_service",
        lambda: type("Q", (), {"async_search": staticmethod(_rien)})(),
    )

    db_session.add(
        FileMetadata(
            path="/dossier/casse.html",
            name="casse.html",
            extension="html",
            size=10,
            chunk_count=0,
            scope="project",
            scope_id="projet-a",
        )
    )
    await db_session.commit()

    contexte = await _get_memory_context(
        "les documents indexés",
        conversation_id=await _conversation_non_rattachee(db_session),
        session=db_session,
    )

    assert contexte is None


@pytest.mark.asyncio
async def test_un_perimetre_illisible_ne_fait_pas_tomber_le_chat(
    db_session, monkeypatch
):
    """Relevé par la relecture : `scope` était affecté DANS le try et lu dehors.

    Un échec de lecture du périmètre partait alors en UnboundLocalError, et
    c'est tout le message qui tombait — pour une mention accessoire.
    """
    async def _explose(*args, **kwargs):
        raise RuntimeError("base illisible")

    monkeypatch.setattr("app.routers.chat._perimetre_de_conversation", _explose)

    contexte = await _get_memory_context(
        "les documents indexés",
        conversation_id=await _conversation_non_rattachee(db_session),
        session=db_session,
    )

    assert contexte is None


@pytest.mark.asyncio
async def test_pas_de_mention_quand_la_conversation_est_rattachee(
    db_session, monkeypatch
):
    """Rattachée à son projet, elle consulte ses documents : rien à signaler."""
    async def _rien(*args, **kwargs):
        return []

    monkeypatch.setattr(
        "app.services.qdrant.get_qdrant_service",
        lambda: type("Q", (), {"async_search": staticmethod(_rien)})(),
    )

    from app.models.entities import Project

    projet = Project(name="Site egrenne")
    db_session.add(projet)
    await db_session.commit()

    conversation = Conversation(title="Avec projet", project_id=projet.id)
    db_session.add(conversation)
    db_session.add(
        FileMetadata(
            path="/d/i.html", name="i.html", extension="html", size=1,
            chunk_count=3, scope="project", scope_id=projet.id,
        )
    )
    await db_session.commit()

    contexte = await _get_memory_context(
        "les documents indexés",
        conversation_id=conversation.id,
        session=db_session,
    )

    assert contexte is None
