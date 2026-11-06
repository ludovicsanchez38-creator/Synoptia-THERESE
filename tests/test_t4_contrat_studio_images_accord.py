"""Contrat du POST d'accord émis par le Studio Images avant génération."""

import json
from datetime import datetime

import pytest


@pytest.mark.asyncio
async def test_decision_du_studio_images_ouvre_la_garde_du_moteur(client):
    from app.config import settings
    from app.services.consentements import AccordEnvoiRequis, exiger_accord

    with pytest.raises(AccordEnvoiRequis, match="Ton accord"):
        exiger_accord("images", "gpt-image-2")

    # Même corps que ImagesWorkspaceCanvas -> grantCloudConsent -> consentSync.
    decision = {
        "event_id": "00000000-0000-4000-8000-000000000083",
        "purpose": "images",
        "provider": "gpt-image-2",
        "granted": True,
        "text_version": "3",
        "data_categories": ["description du visuel", "format", "qualité"],
        "occurred_at": "2026-10-30T09:00:00.000Z",
        "data_profile": str(settings.data_dir),
    }

    response = await client.post("/api/consents", json=decision)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"grants", "history"}
    assert len(body["grants"]) == len(body["history"]) == 1
    grant = body["grants"][0]
    assert grant == {
        "purpose": "images",
        "provider": "gpt-image-2",
        "timestamp": datetime.fromisoformat(decision["occurred_at"].replace("Z", "+00:00")).isoformat(),
        "dataCategories": decision["data_categories"],
        "textVersion": "3",
    }
    preuve = body["history"][0]
    assert preuve["event_id"] == decision["event_id"]
    assert preuve["purpose"] == decision["purpose"]
    assert preuve["provider"] == decision["provider"]
    assert preuve["granted"] is True
    assert preuve["text_version"] == "3"
    assert json.loads(preuve["data_categories"]) == decision["data_categories"]
    assert preuve["source"] == "interface"

    # C'est la garde appelée avant le fournisseur dans image_generator.py.
    exiger_accord("images", "gpt-image-2")
