"""
`create_contact` ne dit pas « réussi » quand il n'a rien écrit.

Campagne cinq personas, finding de Karim. La branche de déduplication
(`memory_tools.py:436-445`) rendait `success: true` AVANT de lire `notes`,
`address` et `phone`. Sur un contact existant, ces arguments étaient donc lus
par personne - et THÉRÈSE annonçait « la fiche inclut désormais l'historique
de la signature » alors que le champ valait `None`.

La phrase venait du modèle. Mais c'est le CONTRAT de l'outil qui l'autorisait :
un modèle parfait annonce la mise à jour, parce que `success: true` la lui
promet.

Ce test fige le contrat, pas la phrase :
- `success` ne vaut vrai que si quelque chose a été écrit ;
- le message NOMME ce qui a été jeté, plutôt que de laisser croire.

Pas d'`update_contact` : le plan 0.56 le sort explicitement du périmètre. On
répare le contrat des outils qui existent, on n'ouvre pas de porte.
"""

import json

import pytest


async def _creer(client, **champs):
    from app.models.database import get_session_context
    from app.services.memory_tools import execute_memory_tool

    async with get_session_context() as session:
        brut = await execute_memory_tool("create_contact", champs, session)
    return json.loads(brut)


class TestUnContactExistantNestPasUneEcriture:
    @pytest.mark.asyncio
    async def test_le_premier_appel_reussit(self, client):
        resultat = await _creer(
            client, first_name="Camille", last_name="Moreau", company="Atelier Moreau"
        )
        assert resultat["success"] is True
        assert resultat.get("already_existed") is not True

    @pytest.mark.asyncio
    async def test_le_second_appel_ne_dit_pas_reussi(self, client):
        await _creer(client, first_name="Camille", last_name="Moreau")
        resultat = await _creer(
            client,
            first_name="Camille",
            last_name="Moreau",
            notes="A signé le 12 août, chantier Vermeer",
            address="12 rue des Genêts, Manosque",
            phone="0612345678",
        )

        assert resultat["already_existed"] is True
        assert resultat["success"] is False, (
            "« success: true » promet au modèle une écriture qui n'a pas eu "
            "lieu : il annonce alors la mise à jour, et il a raison de le faire"
        )

    @pytest.mark.asyncio
    async def test_le_message_nomme_ce_qui_a_ete_jete(self, client):
        await _creer(client, first_name="Camille", last_name="Moreau")
        resultat = await _creer(
            client,
            first_name="Camille",
            last_name="Moreau",
            notes="A signé le 12 août",
            address="12 rue des Genêts",
        )

        message = resultat["message"].lower()
        assert "notes" in message and "adresse" in message, (
            f"le message doit nommer les champs ignorés : {resultat['message']!r}"
        )
        assert "ignor" in message or "pas enregistr" in message or "rien" in message

    @pytest.mark.asyncio
    async def test_sans_champ_supplementaire_le_message_reste_sobre(self, client):
        """Redire un contact sans rien ajouter n'est pas une perte : ne pas alarmer."""
        await _creer(client, first_name="Camille", last_name="Moreau")
        resultat = await _creer(client, first_name="Camille", last_name="Moreau")

        assert resultat["already_existed"] is True
        assert "notes" not in resultat["message"].lower()

    @pytest.mark.asyncio
    async def test_le_contact_reste_reutilisable(self, client):
        """Refuser l'écriture ne doit pas casser la déduplication."""
        premier = await _creer(client, first_name="Camille", last_name="Moreau")
        second = await _creer(
            client, first_name="Camille", last_name="Moreau", notes="X"
        )
        assert second["contact_id"] == premier["contact_id"]


class TestLeRecapDitQueRienNaEteEcrit:
    """
    « 1 déjà existant(s) » est vrai, et ne dit pas l'essentiel.

    Le récap est la dernière ligne de défense contre une prose inventée : c'est
    lui qui a contredit le modèle chez Thomas (« Récap réel : 1 contact(s)
    créé(s) » contre « facture générée et rappel programmé »). Face au cas de
    Karim, il disait « 1 déjà existant » pendant que le modèle annonçait une
    mise à jour. Le lecteur ne pouvait pas trancher.

    Quand des champs ont été jetés, le récap doit le dire — sans crier quand
    redire un contact ne perd rien.
    """

    @staticmethod
    def _recap(resultats):
        from app.services.execution_truth import summarize_executions

        return summarize_executions(resultats)

    def test_un_contact_reutilise_avec_des_champs_jetes_le_dit(self):
        recap = self._recap([
            ("create_contact", json.dumps({
                "success": False, "already_existed": True,
                "champs_ignores": ["notes", "adresse"],
                "contact_id": "c1", "display_name": "Camille Moreau",
            }), False),
        ])
        assert recap is not None
        assert "rien n" in recap.lower() and "écrit" in recap.lower(), (
            f"le récap doit dire que rien n'a été écrit : {recap!r}"
        )

    def test_un_contact_redit_sans_perte_ne_crie_pas(self):
        recap = self._recap([
            ("create_contact", json.dumps({
                "success": True, "already_existed": True,
                "champs_ignores": [], "contact_id": "c1",
            }), False),
        ])
        assert recap is not None
        assert "rien n" not in recap.lower(), (
            f"redire un contact sans rien ajouter n'est pas une perte : {recap!r}"
        )

    def test_une_vraie_creation_reste_annoncee(self):
        recap = self._recap([
            ("create_contact", json.dumps({"success": True, "contact_id": "c1"}), False),
        ])
        assert "créé" in recap
