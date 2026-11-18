
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
    fichier_etranger = dossier / 'FAC-001.pdf'
    fichier_etranger.write_bytes(b'%PDF-1.7\narchive')
    prefixe = invoices._prefixe_apercu_pdf('inv-1', 'FAC-001')
    fichier = dossier / f'{prefixe}{"a" * 32}.pdf'
    fichier.write_bytes(b'%PDF-1.7\n')
    facture = AsyncMock(return_value=SimpleNamespace(invoice_number='FAC-001', document_type='devis'))
    monkeypatch.setattr(invoices, '_get_invoice_with_lines', facture)
    monkeypatch.setattr(invoices, '_get_invoice_output_dir', AsyncMock(return_value=str(dossier)))
    assert await invoices.pdf_pour_ouverture('inv-1', session=None) == {'pdf_path': str(fichier)}
    assert fichier_etranger.read_bytes() == b'%PDF-1.7\narchive'
    facture.assert_awaited_once_with(None, 'inv-1')
    facture.return_value = None
    with pytest.raises(HTTPException) as erreur:
        await invoices.pdf_pour_ouverture('inconnue', session=None)
    assert erreur.value.status_code == 404


@pytest.mark.asyncio
async def test_apercu_remplace_par_un_lien_apres_la_recherche_ne_sort_pas_du_dossier(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from app.routers import invoices
    from fastapi import HTTPException

    dossier = tmp_path / 'factures'
    dossier.mkdir()
    prefixe = invoices._prefixe_apercu_pdf('inv-1', 'FAC-001')
    apercu = dossier / f'{prefixe}{"a" * 32}.pdf'
    apercu.write_bytes(b'%PDF-1.7\napercu')
    exterieur = tmp_path / 'autre.pdf'
    exterieur.write_bytes(b'%PDF-1.7\nautre')
    monkeypatch.setattr(invoices, '_get_invoice_with_lines', AsyncMock(
        return_value=SimpleNamespace(invoice_number='FAC-001', document_type='devis'),
    ))
    monkeypatch.setattr(invoices, '_get_invoice_output_dir', AsyncMock(return_value=str(dossier)))
    chercher = invoices._apercus_pdf

    def remplacer_apres_recherche(*args):
        resultats = chercher(*args)
        lien = dossier / 'remplacement'
        lien.symlink_to(exterieur)
        lien.replace(apercu)
        return resultats

    monkeypatch.setattr(invoices, '_apercus_pdf', remplacer_apres_recherche)
    with pytest.raises(HTTPException) as erreur:
        await invoices.pdf_pour_ouverture('inv-1', session=None)
    assert erreur.value.status_code == 400
    assert exterieur.read_bytes() == b'%PDF-1.7\nautre'
