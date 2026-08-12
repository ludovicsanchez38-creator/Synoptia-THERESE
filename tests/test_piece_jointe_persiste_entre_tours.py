"""BUG-160 — une pièce jointe ne survit pas au tour où elle est envoyée.

Un testeur joint un fichier de 7 Ko et demande ce que dit l'avant-dernière
ligne : THÉRÈSE répond juste. Il enchaîne « affiche-moi l'intégralité du
fichier » et reçoit « Je ne dispose d'aucun outil permettant de lire le contenu
complet du fichier sur votre machine ».

La phrase est littéralement vraie à cet instant, et c'est bien le problème. Au
premier tour, le contenu entre dans le prompt système via le contexte mémoire,
un emplacement reconstruit à chaque requête et jamais conservé. Puis le
composeur vide sa liste de pièces jointes, le message enregistré en base ne
mentionne aucun fichier, et le tour suivant repart sans rien. Il ne reste au
mieux qu'un fragment remonté par la recherche vectorielle.

L'interface, elle, affiche « [Fichiers joints: FN.txt] » sous le message. Le
testeur croit donc légitimement que le fichier est attaché à la conversation.

Ces tests verrouillent la promesse que l'interface fait déjà : une pièce jointe
appartient à la conversation, pas au seul message qui l'a portée.
"""
import json

import pytest


class TestUnePieceJointeAppartientALaConversation:
    @pytest.mark.asyncio
    async def test_le_message_conserve_la_trace_de_ses_pieces_jointes(
        self, db_session, tmp_path
    ):
        """Sans trace en base, aucun tour suivant ne peut retrouver le fichier."""
        from app.models.entities import Conversation, Message
        from app.routers import chat as chat_router

        conversation = Conversation(id="conv-piece-jointe", title="Analyse")
        db_session.add(conversation)
        await db_session.commit()

        fichier = tmp_path / "FN.txt"
        fichier.write_text("ligne unique de contenu", encoding="utf-8")

        message = Message(
            conversation_id=conversation.id,
            role="user",
            content="Que dit l'avant-dernière ligne ?",
        )
        chat_router._memoriser_pieces_jointes(message, [str(fichier)])
        db_session.add(message)
        await db_session.commit()

        assert message.extra_data, (
            "le message part en base sans aucune mention du fichier joint : "
            "au tour suivant, plus rien ne dit qu'un document a été fourni"
        )
        donnees = json.loads(message.extra_data)
        chemins = [p["path"] for p in donnees.get("attachments", [])]
        assert str(fichier) in chemins

    @pytest.mark.asyncio
    async def test_les_pieces_jointes_des_tours_precedents_sont_rejouees(
        self, db_session, tmp_path
    ):
        """Le cœur du bug : au deuxième tour, le fichier doit encore être là."""
        from app.models.entities import Conversation, Message
        from app.routers import chat as chat_router

        conversation = Conversation(id="conv-relecture", title="Analyse")
        db_session.add(conversation)

        fichier = tmp_path / "FN.txt"
        fichier.write_text("contenu du document", encoding="utf-8")

        premier = Message(
            conversation_id=conversation.id,
            role="user",
            content="Que dit ce fichier ?",
            extra_data=json.dumps(
                {"attachments": [{"path": str(fichier), "name": fichier.name}]}
            ),
        )
        db_session.add(premier)
        await db_session.commit()

        rejoues = await chat_router._pieces_jointes_recentes(
            conversation.id, db_session, deja_fournis=[]
        )

        assert str(fichier) in rejoues, (
            "le fichier joint au tour précédent a disparu du contexte : "
            "THÉRÈSE répondra qu'elle n'a aucun moyen de le lire"
        )

    @pytest.mark.asyncio
    async def test_un_fichier_deja_fourni_n_est_pas_rejoue_deux_fois(
        self, db_session, tmp_path
    ):
        """Verrou de coût : le contenu part chez le fournisseur à chaque tour."""
        from app.models.entities import Conversation, Message
        from app.routers import chat as chat_router

        conversation = Conversation(id="conv-dedup", title="Analyse")
        db_session.add(conversation)

        fichier = tmp_path / "FN.txt"
        fichier.write_text("contenu", encoding="utf-8")

        db_session.add(
            Message(
                conversation_id=conversation.id,
                role="user",
                content="premier tour",
                extra_data=json.dumps(
                    {"attachments": [{"path": str(fichier), "name": fichier.name}]}
                ),
            )
        )
        await db_session.commit()

        rejoues = await chat_router._pieces_jointes_recentes(
            conversation.id, db_session, deja_fournis=[str(fichier)]
        )

        assert rejoues == []

    @pytest.mark.asyncio
    async def test_un_fichier_disparu_du_disque_ne_fait_pas_echouer_le_tour(
        self, db_session, tmp_path
    ):
        """Le fichier vit hors de THÉRÈSE : il peut être déplacé ou supprimé."""
        from app.models.entities import Conversation, Message
        from app.routers import chat as chat_router

        conversation = Conversation(id="conv-disparu", title="Analyse")
        db_session.add(conversation)

        db_session.add(
            Message(
                conversation_id=conversation.id,
                role="user",
                content="tour precedent",
                extra_data=json.dumps(
                    {
                        "attachments": [
                            {"path": str(tmp_path / "envole.txt"), "name": "envole.txt"}
                        ]
                    }
                ),
            )
        )
        await db_session.commit()

        rejoues = await chat_router._pieces_jointes_recentes(
            conversation.id, db_session, deja_fournis=[]
        )

        assert rejoues == []


class TestLeModeleSaitCeQuIlARecu:
    def test_le_bloc_de_capacites_decrit_les_pieces_jointes(self):
        """Sans cette phrase, le modèle nie correctement avoir reçu le fichier.

        Aucun outil ne lit un fichier local : le modèle qui répond « je n'ai
        aucun outil pour ça » suit exactement la consigne qu'on lui donne. Il
        faut donc lui dire où regarder, et quoi répondre s'il n'a qu'un extrait.
        """
        from app.routers.chat import BLOC_PIECES_JOINTES

        texte = BLOC_PIECES_JOINTES.lower()
        assert "pièce" in texte or "fichier" in texte
        assert "extrait" in texte, (
            "le modèle n'est pas averti qu'il peut ne recevoir qu'un extrait, "
            "il présentera donc une lecture partielle comme complète"
        )
