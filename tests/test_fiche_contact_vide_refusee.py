"""B-171 (P-005, décision de Ludo) : une fiche sans aucune donnée d'identité était
acceptée, et une adresse e-mail non valide aussi."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_une_fiche_sans_rien_est_refusee(client):
    reponse = await client.post("/api/memory/contacts", json={})
    assert reponse.status_code == 422, reponse.text
    assert "prénom" in reponse.text or "identit" in reponse.text.lower()


@pytest.mark.asyncio
async def test_une_fiche_avec_seulement_des_notes_est_refusee(client):
    reponse = await client.post("/api/memory/contacts", json={"notes": "vu au salon", "phone": "06 00 00 00 00"})
    assert reponse.status_code == 422, reponse.text


@pytest.mark.asyncio
async def test_une_adresse_qui_n_est_pas_une_adresse_est_refusee(client):
    reponse = await client.post("/api/memory/contacts", json={"first_name": "Marie", "email": "pas-une-adresse"})
    assert reponse.status_code == 422, reponse.text
    assert "adresse" in reponse.text.lower()


@pytest.mark.asyncio
async def test_une_fiche_minimale_passe(client):
    reponse = await client.post("/api/memory/contacts", json={"company": "Atelier Martin"})
    assert reponse.status_code in (200, 201), reponse.text
    reponse = await client.post("/api/memory/contacts", json={"first_name": "Marie", "email": "marie@exemple.fr"})
    assert reponse.status_code in (200, 201), reponse.text
