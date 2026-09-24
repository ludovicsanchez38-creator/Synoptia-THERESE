"""B-1180 : les fiches créées (ou mises à jour) par l'import vCard n'entrent
pas dans Qdrant ; le contexte du chat, qui n'interroge que Qdrant
(chat.py:767-783), ne les voit pas.

Attendu : même règle que la création à l'unité, « Auto-embed to Qdrant for
semantic search » (memory.py:611-612, create_contact), et que la création CRM
(crm.py:431-434, BUG-102 : « sans ça les contacts CRM sont introuvables »).
Chemin servi : MemoryPanel.tsx:187 -> POST /api/memory/contacts/import ;
jumeau CRMPanel.tsx:124 -> POST /api/crm/import/vcf.

Le simulacre Qdrant de la suite n'a pas `async_add_memory` en AsyncMock :
sans l'espion posé ici, `_embed_contact` échoue en silence partout.
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock

import pytest

VCF = (
    "BEGIN:VCARD\r\n"
    "VERSION:3.0\r\n"
    "N:Martin;Alice;;;\r\n"
    "FN:Alice Martin\r\n"
    "ORG:Boulangerie Martin\r\n"
    "EMAIL:alice.martin@example.fr\r\n"
    "END:VCARD\r\n"
).encode("utf-8")


@pytest.fixture
def espion_qdrant(monkeypatch):
    import app.services.qdrant as module_qdrant

    espion = AsyncMock(return_value="point-id")
    monkeypatch.setattr(module_qdrant._qdrant_service, "async_add_memory", espion)
    return espion


def _entites_indexees(espion, attendue: str | None = None) -> list[str]:
    # B-1204 : l'indexation part en tâche de fond après la réponse ; on lui
    # laisse le temps d'arriver (la boucle de l'application tourne à part).
    for _ in range(100):
        vues = [c.kwargs.get("entity_id") for c in espion.await_args_list]
        if attendue is None or attendue in vues:
            return vues
        time.sleep(0.05)
    return vues


async def _contact_id(client, email: str) -> str:
    liste = (await client.get("/api/memory/contacts")).json()
    return next(c["id"] for c in liste if c.get("email") == email)


@pytest.mark.asyncio
async def test_une_fiche_creee_par_l_import_vcard_est_indexee(client, espion_qdrant):
    resp = await client.post(
        "/api/memory/contacts/import",
        files={"file": ("carnet.vcf", VCF, "text/vcard")},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["created"] == 1, resp.json()

    cid = await _contact_id(client, "alice.martin@example.fr")
    assert cid in _entites_indexees(espion_qdrant, cid), (
        f"fiche {cid} créée par l'import vCard, appels async_add_memory = "
        f"{espion_qdrant.await_count} ({_entites_indexees(espion_qdrant)})"
    )


@pytest.mark.asyncio
async def test_une_fiche_mise_a_jour_par_l_import_vcard_est_reindexee(client, espion_qdrant):
    cree = await client.post(
        "/api/memory/contacts",
        json={"first_name": "Alice", "last_name": "Martin", "email": "alice.martin@example.fr"},
    )
    assert cree.status_code == 200, cree.text
    cid = cree.json()["id"]
    espion_qdrant.reset_mock()

    resp = await client.post(
        "/api/memory/contacts/import",
        files={"file": ("carnet.vcf", VCF, "text/vcard")},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["updated"] == 1, resp.json()
    fiche = (await client.get(f"/api/memory/contacts/{cid}")).json()
    assert fiche["company"] == "Boulangerie Martin"
    assert cid in _entites_indexees(espion_qdrant, cid), (
        f"société passée à « Boulangerie Martin » par l'import, embedding non "
        f"refait : appels = {espion_qdrant.await_count}"
    )


@pytest.mark.asyncio
async def test_jumeau_crm_une_fiche_importee_par_vcard_est_indexee(client, espion_qdrant):
    resp = await client.post(
        "/api/crm/import/vcf",
        files={"file": ("carnet.vcf", VCF, "text/vcard")},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["created"] == 1, resp.json()

    cid = await _contact_id(client, "alice.martin@example.fr")
    assert cid in _entites_indexees(espion_qdrant, cid), (
        f"fiche {cid} créée par /api/crm/import/vcf, appels async_add_memory = "
        f"{espion_qdrant.await_count}"
    )


@pytest.mark.asyncio
async def test_temoin_la_creation_a_l_unite_indexe_la_fiche(client, espion_qdrant):
    resp = await client.post(
        "/api/memory/contacts",
        json={"first_name": "Alice", "last_name": "Martin", "email": "alice.martin@example.fr"},
    )
    assert resp.status_code == 200, resp.text
    cid = resp.json()["id"]
    appels = [c for c in espion_qdrant.await_args_list if c.kwargs.get("entity_id") == cid]
    assert len(appels) == 1
    assert appels[0].kwargs["memory_type"] == "contact"


@pytest.mark.asyncio
async def test_mesure_score_et_etape_d_une_fiche_importee(client, espion_qdrant):
    """Mesure (pas un verdict) : score et étape posés par l'import, contre la
    création à l'unité qui calcule un score initial (memory.py:614-618)."""
    import sys

    await client.post(
        "/api/memory/contacts/import",
        files={"file": ("carnet.vcf", VCF, "text/vcard")},
    )
    cid = await _contact_id(client, "alice.martin@example.fr")
    importee = (await client.get(f"/api/memory/contacts/{cid}")).json()
    unitaire = (
        await client.post(
            "/api/memory/contacts",
            json={"first_name": "Bob", "last_name": "Durand", "company": "Boulangerie Martin",
                  "email": "bob.durand@example.fr"},
        )
    ).json()
    sys.__stderr__.write(
        f"\nMESURE B-1180 importée : stage={importee.get('stage')} score={importee.get('score')} "
        f"last_interaction={importee.get('last_interaction')} | unitaire : "
        f"stage={unitaire.get('stage')} score={unitaire.get('score')}\n"
    )


@pytest.mark.asyncio
async def test_l_import_repond_sans_attendre_l_indexation(client, monkeypatch):
    """B-1204 : régression de B-1180. Indexer les fiches une à une DANS la
    requête dépasse le délai client de 30 s sur une machine modeste (19 s par
    vecteur, BUG-172) ; l'utilisateur relance et les fiches sans courriel
    naissent en double. L'import répond, l'indexation suit en tâche de fond."""
    import asyncio

    import app.services.qdrant as module_qdrant

    async def lent(**_kwargs):
        await asyncio.sleep(2)
        return "point-id"

    monkeypatch.setattr(module_qdrant._qdrant_service, "async_add_memory", lent)
    carnet = b"".join(
        f"BEGIN:VCARD\r\nVERSION:3.0\r\nFN:Fiche {i}\r\nEMAIL:fiche{i}@example.fr\r\nEND:VCARD\r\n".encode()
        for i in range(3)
    )
    debut = time.monotonic()
    resp = await client.post(
        "/api/memory/contacts/import",
        files={"file": ("carnet.vcf", carnet, "text/vcard")},
    )
    duree = time.monotonic() - debut
    assert resp.status_code == 200, resp.text
    assert duree < 1.5, f"l'import a attendu l'indexation : {duree:.1f} s pour 3 fiches"
