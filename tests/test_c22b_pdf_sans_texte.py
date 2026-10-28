"""B-1213 : un scan vide n'est ni prêt ni silencieusement écarté."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from pypdf import PdfWriter
from app.routers import chat, files
from app.services.file_parser import extract_text


@pytest.mark.asyncio
async def test_scan_avertit_le_chat(tmp_path, monkeypatch):
    pdf = tmp_path / 'scan.pdf'
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.write(pdf)
    monkeypatch.setattr(chat, 'validate_file_path', lambda _: pdf)
    assert extract_text(pdf) == ''
    contexte, avis = await chat._get_file_context(str(pdf), MagicMock())
    assert contexte is None
    assert 'texte sélectionnable' in avis
    assert 'JPEG' in avis
    # Même type que le filtre des deux chemins de chat.
    from app.services.file_parser import AvisLectureFichier
    assert isinstance(avis, AvisLectureFichier)


@pytest.mark.asyncio
async def test_indexation_vide_ne_repond_pas_pret(client, monkeypatch):
    monkeypatch.setattr(files, 'indexer_avec_suivi', AsyncMock(return_value=MagicMock(chunk_count=0)))
    reponse = await client.post('/api/files/index', json={'path': '/tmp/scan.pdf'})
    assert reponse.status_code == 422
    assert 'texte sélectionnable' in reponse.text


def test_un_long_scan_ne_devient_pas_du_texte_par_sa_marque_de_troncature(tmp_path, monkeypatch):
    from app.services import file_parser
    monkeypatch.setattr(file_parser, 'MAX_PDF_PAGES', 1)
    pdf = tmp_path / 'long-scan.pdf'
    writer = PdfWriter()
    for _ in range(2):
        writer.add_blank_page(width=200, height=200)
    writer.write(pdf)
    assert extract_text(pdf) == ''
