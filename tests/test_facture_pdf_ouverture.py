
import pytest


def test_ouverture_uniquement_du_pdf_de_la_facture_dans_son_dossier(tmp_path):
    from app.services.invoice_pdf import chemin_pdf_a_ouvrir
    dossier = tmp_path / 'Dossier choisi' / 'factures'
    dossier.mkdir(parents=True)
    pdf = dossier / 'FAC-001.pdf'
    pdf.write_bytes(b'%PDF-1.7\n')
    assert chemin_pdf_a_ouvrir(str(dossier), 'FAC-001') == pdf.resolve()


@pytest.mark.parametrize('numero', ['../secret', '/etc/passwd', '..\\secret'])
def test_numero_ne_peut_pas_sortir_du_dossier(tmp_path, numero):
    from app.services.invoice_pdf import chemin_pdf_a_ouvrir
    with pytest.raises(ValueError):
        chemin_pdf_a_ouvrir(str(tmp_path), numero)


def test_lien_vers_un_autre_dossier_refuse(tmp_path):
    from app.services.invoice_pdf import chemin_pdf_a_ouvrir
    dossier = tmp_path / 'factures'
    dossier.mkdir()
    (tmp_path / 'autre.pdf').write_bytes(b'%PDF-1.7\n')
    (dossier / 'FAC-001.pdf').symlink_to(tmp_path / 'autre.pdf')
    with pytest.raises(ValueError):
        chemin_pdf_a_ouvrir(str(dossier), 'FAC-001')


def test_fichier_absent_refuse(tmp_path):
    from app.services.invoice_pdf import chemin_pdf_a_ouvrir
    with pytest.raises(FileNotFoundError):
        chemin_pdf_a_ouvrir(str(tmp_path), 'FAC-001')


@pytest.mark.asyncio
async def test_route_resout_le_pdf_depuis_la_facture_et_le_dossier_choisi(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from app.routers import invoices
    from fastapi import HTTPException
    dossier = tmp_path / 'factures'
    dossier.mkdir()
    fichier = dossier / 'FAC-001.pdf'
    fichier.write_bytes(b'%PDF-1.7\n')
    facture = AsyncMock(return_value=SimpleNamespace(invoice_number='FAC-001'))
    monkeypatch.setattr(invoices, '_get_invoice_with_lines', facture)
    monkeypatch.setattr(invoices, '_get_invoice_output_dir', AsyncMock(return_value=str(dossier)))
    assert await invoices.pdf_pour_ouverture('inv-1', session=None) == {'pdf_path': str(fichier)}
    facture.assert_awaited_once_with(None, 'inv-1')
    facture.return_value = None
    with pytest.raises(HTTPException) as erreur:
        await invoices.pdf_pour_ouverture('inconnue', session=None)
    assert erreur.value.status_code == 404
