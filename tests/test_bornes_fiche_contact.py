"""
Une fiche contact n'accepte ni une étape inconnue, ni un champ de 100 ko.

Deux constats du persona « robustesse API » (RB-012 et RB-013, cycle 2), même
porte : `POST /api/memory/contacts`.

**B-167, l'étape hors pipeline.** `stage` était une chaîne libre. Un contact
créé avec `stage="nimportequoi"` était accepté en 200 et le gardait à la
relecture. L'écran, lui, groupe les fiches en parcourant les sept colonnes
connues (`PipelineView.tsx`, `PIPELINE_STAGES.reduce`) : il n'existe pas de
colonne de repli, donc la fiche disparaissait de la vue pipeline sans un mot.
Accepter une valeur que l'écran ne sait pas rendre, c'est promettre un
enregistrement puis le cacher.

**B-168, le champ sans borne.** Aucun champ texte n'avait de longueur
maximale. Un `first_name` de 100 000 caractères était stocké entier, et la
liste des contacts le rendait ensuite intégralement : 203 116 octets pour six
fiches, dont une seule pesait presque tout. La route de liste n'a pas de
projection, donc une seule fiche suffit à alourdir chaque affichage.

Les deux gardes sont posées sur le schéma, pas dans la route : elles valent
alors pour toutes les portes qui déclarent ce schéma, la création comme la
mise à jour.
"""

import pytest

ETAPE_INCONNUE = "nimportequoi"


async def _creer_contact(client, **champs):
    charge = {"first_name": "Témoin"}
    charge.update(champs)
    return await client.post("/api/memory/contacts", json=charge)


class TestUneEtapeHorsPipelineEstRefusee:
    @pytest.mark.asyncio
    async def test_creation_refusee(self, client):
        reponse = await _creer_contact(
            client, first_name="StageBidon", stage=ETAPE_INCONNUE
        )

        assert reponse.status_code == 422, (
            "une étape que la vue pipeline ne sait pas afficher est acceptée : "
            f"{reponse.status_code} {reponse.text[:200]}"
        )

    @pytest.mark.asyncio
    async def test_la_fiche_refusee_n_est_pas_en_base(self, client):
        await _creer_contact(client, first_name="StageBidon", stage=ETAPE_INCONNUE)

        liste = await client.get("/api/memory/contacts")
        assert liste.status_code == 200, liste.text
        assert all(c["stage"] != ETAPE_INCONNUE for c in liste.json()), (
            "la fiche à l'étape inconnue est enregistrée : elle n'apparaîtra "
            "dans aucune colonne du pipeline"
        )

    @pytest.mark.asyncio
    async def test_les_sept_etapes_connues_passent(self, client):
        for etape in (
            "contact",
            "discovery",
            "proposition",
            "signature",
            "delivery",
            "active",
            "archive",
        ):
            reponse = await _creer_contact(
                client, first_name=f"Etape {etape}", stage=etape
            )
            assert reponse.status_code == 200, (
                f"l'étape « {etape} » du pipeline est refusée : {reponse.text[:200]}"
            )

    @pytest.mark.asyncio
    async def test_la_mise_a_jour_refuse_aussi(self, client):
        cree = await _creer_contact(client, first_name="Bascule")
        assert cree.status_code == 200, cree.text
        identifiant = cree.json()["id"]

        reponse = await client.patch(
            f"/api/memory/contacts/{identifiant}", json={"stage": ETAPE_INCONNUE}
        )
        assert reponse.status_code == 422, (
            "la garde de création est contournable par une mise à jour : "
            f"{reponse.status_code} {reponse.text[:200]}"
        )

    @pytest.mark.asyncio
    async def test_la_porte_crm_refuse_aussi(self, client):
        cree = await client.post(
            "/api/crm/contacts",
            json={"first_name": "Pipeline", "stage": ETAPE_INCONNUE},
        )
        assert cree.status_code == 422, (
            "la création CRM accepte une étape hors pipeline : "
            f"{cree.status_code} {cree.text[:200]}"
        )

        contact = await client.post("/api/crm/contacts", json={"first_name": "Bascule"})
        assert contact.status_code == 200, contact.text
        deplacement = await client.patch(
            f"/api/crm/contacts/{contact.json()['id']}/stage",
            json={"stage": ETAPE_INCONNUE},
        )
        assert deplacement.status_code == 422, (
            "le déplacement dans le pipeline accepte une étape inconnue : "
            f"{deplacement.status_code} {deplacement.text[:200]}"
        )


class TestUnChampTexteEstBorne:
    @pytest.mark.asyncio
    async def test_un_nom_de_100_ko_est_refuse(self, client):
        reponse = await _creer_contact(client, first_name="N" * 100_000)

        assert reponse.status_code == 422, (
            "un nom de contact de 100 000 caractères est accepté : "
            f"{reponse.status_code}"
        )

    @pytest.mark.asyncio
    async def test_des_notes_de_100_ko_sont_refusees(self, client):
        reponse = await _creer_contact(client, notes="N" * 100_000)

        assert reponse.status_code == 422, (
            "des notes de 100 000 caractères sont acceptées : "
            f"{reponse.status_code}"
        )

    @pytest.mark.asyncio
    async def test_la_liste_ne_peut_plus_peser_200_ko(self, client):
        await _creer_contact(client, first_name="G" * 100_000, notes="N" * 100_000)

        liste = await client.get("/api/memory/contacts")
        assert liste.status_code == 200, liste.text
        assert len(liste.content) < 100_000, (
            "une seule fiche suffit à alourdir chaque affichage de la liste : "
            f"{len(liste.content)} octets"
        )

    @pytest.mark.asyncio
    async def test_une_fiche_ordinaire_passe(self, client):
        reponse = await _creer_contact(
            client,
            first_name="Camille",
            last_name="Moreau",
            company="Atelier Moreau",
            email="camille@atelier-moreau.test",
            phone="0612345678",
            address="12 rue des Genêts, 04100 Manosque",
            notes="Rencontrée au salon. " * 200,
        )

        assert reponse.status_code == 200, (
            f"une fiche ordinaire est refusée par les bornes : {reponse.text[:300]}"
        )

    @pytest.mark.asyncio
    async def test_la_mise_a_jour_est_bornee_aussi(self, client):
        cree = await _creer_contact(client, first_name="Bornes")
        assert cree.status_code == 200, cree.text

        reponse = await client.patch(
            f"/api/memory/contacts/{cree.json()['id']}",
            json={"notes": "N" * 100_000},
        )
        assert reponse.status_code == 422, (
            "la borne de création est contournable par une mise à jour : "
            f"{reponse.status_code}"
        )
