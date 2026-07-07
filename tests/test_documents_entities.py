"""
Tests pour les entités Document/DocumentSection/DocumentPiste.

Cas de test : créer un document avec 2 sections et 1 piste,
relire et vérifier les ids UUID distincts et statuts par défaut.
"""

import pytest
from app.models.entities import Document, DocumentSection, DocumentPiste
from sqlmodel import select


@pytest.mark.asyncio
async def test_document_section_piste_creation_and_defaults(db_session):
    """Créer un document + 2 sections + 1 piste, relire, vérifier ids/statuts."""

    # Créer un document
    doc = Document(
        title="Mon Document",
        brief="Description du besoin",
    )
    db_session.add(doc)
    await db_session.flush()
    doc_id = doc.id

    # Créer 2 sections
    section1 = DocumentSection(
        document_id=doc_id,
        title="Section 1",
        brief="Première section",
    )
    section2 = DocumentSection(
        document_id=doc_id,
        title="Section 2",
        brief="Deuxième section",
        depth=1,
    )
    db_session.add(section1)
    db_session.add(section2)
    await db_session.flush()
    section1_id = section1.id
    section2_id = section2.id

    # Créer 1 piste
    piste = DocumentPiste(
        document_id=doc_id,
        section_origine_id=section1_id,
        texte="Idée annexe capturée",
    )
    db_session.add(piste)
    await db_session.flush()
    piste_id = piste.id

    # Vérifier les ids sont distincts
    assert doc_id != section1_id
    assert doc_id != section2_id
    assert doc_id != piste_id
    assert section1_id != section2_id
    assert section1_id != piste_id
    assert section2_id != piste_id

    # Vérifier que les ids ressemblent à des UUIDs (format string hex)
    assert len(doc_id) == 36  # uuid4 format avec tirets
    assert len(section1_id) == 36
    assert len(piste_id) == 36

    # Recharger depuis la base
    doc_reloaded = (
        await db_session.execute(select(Document).where(Document.id == doc_id))
    ).scalar_one()

    sections_reloaded = (
        await db_session.execute(select(DocumentSection).where(DocumentSection.document_id == doc_id))
    ).scalars().all()

    piste_reloaded = (
        await db_session.execute(select(DocumentPiste).where(DocumentPiste.id == piste_id))
    ).scalar_one()

    # Vérifier les données
    assert doc_reloaded.title == "Mon Document"
    assert doc_reloaded.brief == "Description du besoin"
    assert doc_reloaded.status == "en_cours"  # statut par défaut

    assert len(sections_reloaded) == 2
    assert sections_reloaded[0].title == "Section 1"
    assert sections_reloaded[0].status == "vide"  # statut par défaut
    assert sections_reloaded[0].order == 0.0  # order par défaut
    assert sections_reloaded[0].depth == 0
    assert sections_reloaded[0].orphan is False

    assert sections_reloaded[1].title == "Section 2"
    assert sections_reloaded[1].status == "vide"
    assert sections_reloaded[1].depth == 1
    assert sections_reloaded[1].orphan is False

    assert piste_reloaded.texte == "Idée annexe capturée"
    assert piste_reloaded.status == "nouvelle"  # statut par défaut
    assert piste_reloaded.section_origine_id == section1_id
