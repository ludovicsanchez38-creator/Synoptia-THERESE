"""R1-6 : une copie confirmée, bornée au dossier choisi et sans écrasement."""
from pathlib import Path

import pytest
from app.models.entities import Preference


@pytest.mark.asyncio
async def test_copie_seulement_apres_confirmation(client, db_session, tmp_path):
    travail = tmp_path / 'travail'
    travail.mkdir()
    source = tmp_path / 'devis.txt'
    source.write_text('Devis de recette')
    homonyme = travail / source.name
    homonyme.write_text('Original')
    db_session.add(Preference(key='working_directory', value=str(travail)))
    await db_session.commit()
    refus = await client.post('/api/files/copy-to-working-directory', json={'path': str(source), 'confirmed': False})
    assert refus.status_code == 422
    assert list(travail.iterdir()) == [homonyme]
    copie = await client.post('/api/files/copy-to-working-directory', json={'path': str(source), 'confirmed': True})
    assert copie.status_code == 200, copie.text
    destination = Path(copie.json()['path'])
    assert destination.parent == travail
    assert destination.read_text(encoding="utf-8") == source.read_text(encoding="utf-8")
    assert homonyme.read_text(encoding="utf-8") == 'Original'


@pytest.mark.asyncio
async def test_sans_dossier_la_copie_est_refusee(client, tmp_path):
    source = tmp_path / 'rapport.txt'
    source.write_text('Rapport')
    reponse = await client.post('/api/files/copy-to-working-directory', json={'path': str(source), 'confirmed': True})
    assert reponse.status_code == 400
