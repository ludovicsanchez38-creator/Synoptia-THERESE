"""La numerotation des devis et factures : au-dela de 999, et sous concurrence.

02/09/2026, campagne de robustesse du cycle 2.

RB-002 (B-159) : le 1000e devis d'une annee passe, le 1001e rend 500 et la
panne est DEFINITIVE. `_generate_invoice_number` prenait le maximum
LEXICOGRAPHIQUE de la colonne texte : « DEV-2026-1000 » < « DEV-2026-999 »,
donc le maximum reste bloque sur 999 et le numero calcule est toujours 1000,
deja pris.

RB-003 (B-160) : huit creations simultanees, six erreurs 500. Le numero est lu
par MAX() puis insere sans transaction verrouillante : deux requetes qui
lisent le meme maximum calculent le meme numero, et la seconde viole la
contrainte d'unicite.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest


async def _cree_contact(client) -> str:
    reponse = await client.post(
        "/api/memory/contacts",
        json={"first_name": "Numero", "last_name": "Test", "email": "num@test.fr"},
    )
    assert reponse.status_code == 200, reponse.text
    return reponse.json()["id"]


async def _pose_document(numero: str, contact_id: str) -> None:
    """Insere un document directement en base, avec son numero impose."""
    from app.models import database as db_module
    from app.models.entities import Invoice

    async with db_module.AsyncSessionLocal() as session:
        session.add(
            Invoice(
                invoice_number=numero,
                contact_id=contact_id,
                document_type="devis",
                due_date=datetime.now(UTC) + timedelta(days=30),
            )
        )
        await session.commit()


def _corps_de_devis(contact_id: str) -> dict:
    return {
        "contact_id": contact_id,
        "document_type": "devis",
        "lines": [
            {
                "description": "Prestation",
                "quantity": 1.0,
                "unit_price_ht": 10.0,
                "tva_rate": 20.0,
            }
        ],
    }


class TestLeMillieme:
    """B-159 : passer le cap des trois chiffres ne doit pas arreter la serie."""

    @pytest.mark.asyncio
    async def test_le_1001e_devis_prend_le_numero_suivant(self, client):
        annee = datetime.now(UTC).year
        contact_id = await _cree_contact(client)
        await _pose_document(f"DEV-{annee}-999", contact_id)
        await _pose_document(f"DEV-{annee}-1000", contact_id)

        reponse = await client.post("/api/invoices/", json=_corps_de_devis(contact_id))

        assert reponse.status_code == 200, (
            f"la creation doit continuer au-dela du 1000e : "
            f"{reponse.status_code} {reponse.text[:200]}"
        )
        assert reponse.json()["invoice_number"] == f"DEV-{annee}-1001"


class TestLaCourseAuNumero:
    """B-160 : deux creations simultanees calculent le meme numero.

    Le client de test serialise les requetes : lancer huit POST par
    `asyncio.gather` passerait deja, et un test qui ne peut pas rougir ne
    prouve rien. La collision est donc provoquee AU POINT EXACT ou elle a
    lieu : entre la lecture du numero et l'insertion, un concurrent ecrit ce
    numero pour de vrai (autre session, commit reel). La contrainte d'unicite
    de SQLite fait le reste.
    """

    @pytest.mark.asyncio
    async def test_un_numero_double_par_un_concurrent_ne_perd_pas_la_creation(
        self, client, monkeypatch
    ):
        from app.routers import invoices as module

        annee = datetime.now(UTC).year
        contact_id = await _cree_contact(client)
        original = module._generate_invoice_number
        course = {"doublee": False}

        async def numero_puis_double(session, document_type="facture"):
            numero = await original(session, document_type)
            if not course["doublee"]:
                course["doublee"] = True
                await _pose_document(numero, contact_id)
            return numero

        monkeypatch.setattr(module, "_generate_invoice_number", numero_puis_double)

        reponse = await client.post("/api/invoices/", json=_corps_de_devis(contact_id))

        assert course["doublee"], "la collision n'a pas ete provoquee"
        assert reponse.status_code == 200, (
            f"un numero double par un concurrent doit etre repris, pas rendu "
            f"en erreur : {reponse.status_code} {reponse.text[:200]}"
        )
        assert reponse.json()["invoice_number"] == f"DEV-{annee}-002"

    @pytest.mark.asyncio
    async def test_les_lignes_du_document_repris_sont_bien_la(self, client, monkeypatch):
        """La reprise rejoue l'insertion : le document ne doit pas perdre ses
        lignes ni ses totaux au passage."""
        from app.routers import invoices as module

        contact_id = await _cree_contact(client)
        original = module._generate_invoice_number
        course = {"doublee": False}

        async def numero_puis_double(session, document_type="facture"):
            numero = await original(session, document_type)
            if not course["doublee"]:
                course["doublee"] = True
                await _pose_document(numero, contact_id)
            return numero

        monkeypatch.setattr(module, "_generate_invoice_number", numero_puis_double)

        reponse = await client.post("/api/invoices/", json=_corps_de_devis(contact_id))

        assert reponse.status_code == 200, reponse.text[:200]
        corps = reponse.json()
        assert len(corps["lines"]) == 1, f"lignes perdues a la reprise : {corps['lines']}"
        assert corps["total_ttc"] == 12.0


class TestLesAutresCheminsDInsertion:
    """B-338 (05/09/2026) : la reprise de numéro posée en B-160 ne couvrait que
    `create_invoice`. Les deux autres chemins qui insèrent une pièce numérotée,
    la conversion de type (`POST /{id}/convert`) et la conversion d'un devis en
    facture (`POST /{id}/convert-to-invoice`), lisaient le numéro puis
    inséraient sans reprise : six conversions simultanées sur huit finissaient
    en 500 « UNIQUE constraint failed: invoices.invoice_number ». Même
    provocation qu'au-dessus : un concurrent pose le numéro entre la lecture
    et l'insertion.
    """

    async def _devis_cree(self, client, contact_id: str) -> str:
        reponse = await client.post("/api/invoices/", json=_corps_de_devis(contact_id))
        assert reponse.status_code == 200, reponse.text[:200]
        return reponse.json()["id"]

    def _double_le_prochain_numero(self, monkeypatch, contact_id: str) -> dict:
        from app.routers import invoices as module

        original = module._generate_invoice_number
        course = {"doublee": False}

        async def numero_puis_double(session, document_type="facture"):
            numero = await original(session, document_type)
            if not course["doublee"]:
                course["doublee"] = True
                await _pose_document(numero, contact_id)
            return numero

        monkeypatch.setattr(module, "_generate_invoice_number", numero_puis_double)
        return course

    @pytest.mark.asyncio
    async def test_la_conversion_de_type_reprend_un_numero_double(self, client, monkeypatch):
        annee = datetime.now(UTC).year
        contact_id = await _cree_contact(client)
        devis_id = await self._devis_cree(client, contact_id)
        course = self._double_le_prochain_numero(monkeypatch, contact_id)

        reponse = await client.post(
            f"/api/invoices/{devis_id}/convert", json={"target_type": "facture"}
        )

        assert course["doublee"], "la collision n'a pas ete provoquee"
        assert reponse.status_code == 200, (
            f"la conversion de type doit reprendre un numero double, pas rendre "
            f"{reponse.status_code} {reponse.text[:200]}"
        )
        assert reponse.json()["invoice_number"] == f"FACT-{annee}-002"

    @pytest.mark.asyncio
    async def test_la_conversion_du_devis_en_facture_reprend_un_numero_double(
        self, client, monkeypatch
    ):
        annee = datetime.now(UTC).year
        contact_id = await _cree_contact(client)
        devis_id = await self._devis_cree(client, contact_id)
        course = self._double_le_prochain_numero(monkeypatch, contact_id)

        reponse = await client.post(f"/api/invoices/{devis_id}/convert-to-invoice", json={})

        assert course["doublee"], "la collision n'a pas ete provoquee"
        assert reponse.status_code == 200, (
            f"la conversion du devis doit reprendre un numero double, pas rendre "
            f"{reponse.status_code} {reponse.text[:200]}"
        )
        assert reponse.json()["invoice_number"] == f"FACT-{annee}-002"
