"""Finding 9 (revue 30/08) : deux dossiers de données, trousseau et PDF ne suivaient pas.

Le Keychain restait `therese-app` / `encryption-key` : un second profil
écrasait la clé. Les PDF sans working_directory s'écrivaient dans
`~/.therese/invoices`, pas dans le data dir.
"""

from __future__ import annotations

from pathlib import Path

import pytest


def test_trousseau_du_profil_par_defaut_garde_l_entree_historique():
    from app.services.encryption import _compte_trousseau

    defaut = Path.home() / ".therese"
    assert _compte_trousseau(defaut) == "encryption-key"


def test_trousseau_d_un_autre_profil_ne_partage_pas_l_entree():
    from app.services.encryption import _compte_trousseau

    autre = Path("/tmp/therese-profil-b")
    compte = _compte_trousseau(autre)
    assert compte != "encryption-key"
    assert "therese-profil-b" in compte


@pytest.mark.asyncio
async def test_pdf_facture_suit_le_data_dir(db_session, monkeypatch, tmp_path):
    from app.config import settings
    from app.routers import invoices as invoices_mod

    monkeypatch.setattr(settings, "data_dir", tmp_path)
    dossier = await invoices_mod._get_invoice_output_dir(db_session)
    assert Path(dossier) == tmp_path / "invoices"
    assert ".therese/invoices" not in dossier or str(tmp_path) in dossier
