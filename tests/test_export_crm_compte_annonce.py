"""
B-141 : l'export CRM « tout » en CSV annonçait un compte que son contenu dément.

`export_all` calcule `total_count = contacts + projets + livrables` puis, dans la
branche CSV, n'écrit que la boucle sur les contacts - tout en renvoyant ce total
dans l'en-tête `X-Row-Count`. Reproduit le 02/09/2026 : 7 contacts + 1 projet,
en-tête `x-row-count: 8`, fichier de 7 lignes toutes de Type=Contact.

L'invariant posé ici : **le compte annoncé est celui du contenu livré**. Un
en-tête qui promet des lignes absentes se lit comme une perte de données, et
c'est encore pire quand la perte, elle, est réelle.

Le périmètre CSV lui-même (contacts uniquement) reste tel qu'il est documenté
dans la docstring de la route : fusionner les trois entités dans un CSV plat
demanderait un arbitrage de colonnes (« Nom » désigne `last_name` chez le
contact et `name` chez le projet, « Statut » n'existe pas chez le contact).
"""

import csv
import io

import pytest
from httpx import AsyncClient


async def _peupler(client: AsyncClient) -> None:
    """Un contact ET un projet : le projet est ce que le CSV n'écrit pas."""
    reponse = await client.post(
        "/api/crm/contacts",
        json={
            "first_name": "Marie",
            "last_name": "Dupont",
            "company": "Synoptia",
            "email": "marie@synoptia.fr",
            "stage": "contact",
        },
    )
    assert reponse.status_code == 200, reponse.text

    reponse = await client.post(
        "/api/memory/projects",
        json={
            "name": "Projet Formation IA",
            "description": "Formation IA pour 15 collaborateurs",
            "status": "active",
        },
    )
    assert reponse.status_code == 200, reponse.text


def _lignes_de_donnees(corps: bytes) -> list[dict]:
    """Le CSV part avec un BOM pour Excel : le décoder, sinon la 1re colonne ment."""
    texte = corps.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(texte)))


class TestLeCompteAnnonceEgaleLeContenu:
    @pytest.mark.asyncio
    async def test_csv_le_compte_annonce_egale_les_lignes_ecrites(self, client: AsyncClient):
        await _peupler(client)

        reponse = await client.post("/api/crm/export/all?format=csv")
        assert reponse.status_code == 200, reponse.text

        lignes = _lignes_de_donnees(reponse.content)
        annonce = int(reponse.headers["x-row-count"])
        assert annonce == len(lignes), (
            f"en-tête X-Row-Count={annonce} pour {len(lignes)} ligne(s) écrite(s) : "
            "le compte annoncé dément le fichier livré"
        )

    @pytest.mark.asyncio
    async def test_csv_ne_promet_pas_le_projet_qu_il_n_ecrit_pas(self, client: AsyncClient):
        await _peupler(client)

        reponse = await client.post("/api/crm/export/all?format=csv")
        lignes = _lignes_de_donnees(reponse.content)

        assert {ligne["Type"] for ligne in lignes} == {"Contact"}
        assert int(reponse.headers["x-row-count"]) == len(lignes)

    @pytest.mark.asyncio
    async def test_json_annonce_bien_les_trois_entites(self, client: AsyncClient):
        """Contrôle : la branche JSON, elle, livre les trois - le compte y est juste
        et le correctif CSV ne doit pas le rendre faux."""
        await _peupler(client)

        reponse = await client.post("/api/crm/export/all?format=json")
        assert reponse.status_code == 200, reponse.text

        donnees = reponse.json()
        contenu = (
            len(donnees["contacts"]) + len(donnees["projects"]) + len(donnees["deliverables"])
        )
        assert int(reponse.headers["x-row-count"]) == contenu
        assert len(donnees["projects"]) == 1
