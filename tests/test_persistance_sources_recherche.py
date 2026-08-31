"""La recherche approfondie doit VRAIMENT persister ses sources.

Trouvé le 01/09/2026 par la boucle d'amélioration, dans un correctif que
j'avais moi-même fusionné la veille.

`chat.py` écrivait `async with get_session() as save_session`. Or
`get_session` est une génératrice d'injection de dépendance, sans
`@asynccontextmanager` : la forme lève `TypeError: 'async_generator' object
does not support the asynchronous context manager protocol`. L'exception
était avalée par un `except Exception` qui ne faisait qu'un log, donc le
rapport et ses sources n'étaient jamais écrits, exactement le défaut que le
commentaire voisin annonçait corrigé.

Le test qui gardait ce correctif faisait `assert '"sources"' in source` : il
cherchait la chaîne dans le TEXTE de `chat.py`. Elle y était, donc il passait
sans jamais exécuter la ligne fautive. C'est le motif que la campagne de
lecture a trouvé partout : un test qui vérifie le texte du code au lieu de
son comportement.

Ces deux tests exercent le mécanisme, ils ne le lisent pas.
"""

import json
import re
from pathlib import Path

import pytest
from sqlmodel import select


@pytest.mark.asyncio
async def test_un_message_avec_ses_sources_survit_a_l_ecriture(db_session):
    """Le comportement, pas le texte : on écrit, on relit.

    La fixture `db_session` du dépôt initialise la base ; on n'utilise
    ensuite que `get_session_context`, la forme que le code doit employer.
    """
    from app.models.database import get_session_context
    from app.models.entities import Conversation, Message

    sources = [{"title": "Un titre", "url": "https://exemple.fr", "snippet": "extrait"}]

    async with get_session_context() as session:
        conversation = Conversation(title="Recherche approfondie")
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
        session.add(
            Message(
                conversation_id=conversation.id,
                role="assistant",
                content="synthèse",
                extra_data=json.dumps({"sources": sources}),
            )
        )
        await session.commit()
        identifiant = conversation.id

    async with get_session_context() as relecture:
        messages = (
            await relecture.execute(
                select(Message).where(Message.conversation_id == identifiant)
            )
        ).scalars().all()

    assert len(messages) == 1, "le message n'a pas survécu à l'écriture"
    relues = json.loads(messages[0].extra_data)["sources"]
    assert relues == sources, "les sources n'ont pas survécu à l'aller-retour"


def test_aucun_site_du_backend_n_ouvre_get_session_en_gestionnaire_de_contexte():
    """La forme fautive ne doit revenir nulle part.

    Garde structurelle, avec la vérification de non-vacuité que plusieurs
    tests du dépôt oublient : si le balayage ne trouve aucun fichier, il
    échoue au lieu de passer.
    """
    racine = Path("src/backend/app")
    fichiers = list(racine.rglob("*.py"))
    assert len(fichiers) > 50, f"balayage suspect : {len(fichiers)} fichiers trouvés"

    # Le garde ignore les commentaires : sans cela, la ligne d'explication
    # posée à côté du correctif le déclenchait elle-même. C'est le piège que
    # cette campagne a trouvé partout, un commentaire qui satisfait une
    # recherche de texte ; il valait aussi pour ce test.
    fautifs = [
        f"{f}:{n}"
        for f in fichiers
        for n, ligne in enumerate(f.read_text(encoding="utf-8").splitlines(), 1)
        if not ligne.strip().startswith("#")
        and re.search(r"async with get_session\s*\(\s*\)", ligne)
    ]
    assert not fautifs, (
        "get_session est une génératrice de dépendance, pas un gestionnaire de "
        f"contexte : utilisez get_session_context. Sites fautifs : {fautifs}"
    )
