"""B2 — l'adresse d'un client doit pouvoir être saisie, partout.

Campagne dix personas, finding F2 de l'artisan : « Mettre l'adresse du client
(14 chemin des Oliviers, Mane) dans la fiche. Pas de champ Adresse à l'écran.
J'ai quand même envoyé l'adresse : elle est revenue vide. »

Le champ existe en base (`entities.py:30`) et sept couches le déclarent. Trois
l'honorent : la base, le `PATCH`, l'import VCF. Les autres le jettent.

La relecture de design a corrigé mon périmètre : ce n'est pas « une ligne dans
POST ». Le chemin réel de l'artisan est le formulaire du PREMIER devis, qui n'a
ni adresse ni téléphone. Toutes les couches doivent être honorées ensemble,
sinon elles redivergeront.

Hors périmètre, nommé : le LIEU D'EXÉCUTION. `Invoice` n'a pas le champ, et le
PDF lit `contact.address` comme destinataire. Pour un particulier, la maison est
le chantier ; pour une SCI, non. C'est un autre chantier.
"""
import pytest


class TestLaCreationHonoreLAdresse:
    @pytest.mark.asyncio
    async def test_l_adresse_postee_est_relue(self, client):
        """Le cas exact de l'artisan : il l'envoie, elle revient vide."""
        creation = await client.post(
            "/api/memory/contacts",
            json={
                "first_name": "Alain",
                "last_name": "Moreau",
                "address": "14 chemin des Oliviers, 04300 Mane",
                "phone": "06 12 34 56 78",
            },
        )
        assert creation.status_code in (200, 201), creation.text
        cree = creation.json()
        assert cree["address"] == "14 chemin des Oliviers, 04300 Mane", (
            "POST /memory/contacts jetait l'adresse : un devis sans adresse ne "
            "s'envoie pas"
        )
        assert cree["phone"] == "06 12 34 56 78"

        relecture = await client.get(f"/api/memory/contacts/{cree['id']}")
        assert relecture.json()["address"] == "14 chemin des Oliviers, 04300 Mane"


class TestLOutilDuChatSaitPrendreUneAdresse:
    def test_create_contact_expose_l_adresse(self):
        """« Enregistre Moreau, 14 chemin des Oliviers » doit fonctionner."""
        from app.services.memory_tools import CREATE_CONTACT_TOOL

        proprietes = CREATE_CONTACT_TOOL["function"]["parameters"]["properties"]
        assert "address" in proprietes, (
            "sans ce paramètre, le modèle ne peut pas transmettre une adresse "
            "dictée, même quand l'utilisateur la donne"
        )

    @pytest.mark.asyncio
    async def test_l_outil_ecrit_vraiment_l_adresse(self, client):
        """Un paramètre déclaré et non écrit serait un champ mort de plus."""
        from app.models.database import get_session_context
        from app.models.entities import Contact
        from app.services.memory_tools import execute_create_contact
        from sqlalchemy import select

        async with get_session_context() as session:
            await execute_create_contact(
                {
                    "first_name": "Sophie",
                    "last_name": "Garcia",
                    "address": "3 rue des Lices, 84000 Avignon",
                },
                session,
            )
            await session.commit()

            trouve = await session.execute(
                select(Contact).where(Contact.last_name == "Garcia")
            )
            contact = trouve.scalars().first()
            assert contact is not None
            assert contact.address == "3 rue des Lices, 84000 Avignon"
