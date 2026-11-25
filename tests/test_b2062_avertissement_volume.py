"""Le choix du dossier avertit seulement quand la création du lien est refusée."""

import errno
import os

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("erreur", "avertit"),
    [
        (None, False),
        (errno.EPERM, True),
        (errno.EOPNOTSUPP, True),
        (errno.EACCES, False),
    ],
)
async def test_le_choix_du_dossier_signale_un_refus_de_lien(
    client, tmp_path, monkeypatch, erreur, avertit
):
    choisi = tmp_path / "Bureau de Camille"
    choisi.mkdir()
    factures = choisi / "factures"
    factures.mkdir()
    original = factures / "facture-existante.pdf"
    original.write_bytes(b"piece a conserver")

    liens = []
    os_link = os.link

    def lier(source, destination):
        liens.append((source, destination))
        if erreur is not None:
            raise OSError(erreur, "refus simulé")
        os_link(source, destination)

    monkeypatch.setattr(os, "link", lier)
    reponse = await client.post("/api/config/working-directory", json={"path": str(choisi)})

    assert reponse.status_code == 200
    avertissement = reponse.json().get("avertissement_facturation")
    if avertit:
        assert avertissement
        assert "lien physique" in avertissement
        assert "PDF de devis et de factures" in avertissement
        assert "disque interne" in avertissement
    else:
        assert avertissement is None
    [(source, destination)] = liens
    assert source.parent == destination.parent
    assert source.parent.parent == factures.resolve()
    assert list(factures.iterdir()) == [original]
    assert original.read_bytes() == b"piece a conserver"
    relu = await client.get("/api/config/working-directory")
    assert relu.json()["path"] == str(choisi.resolve())
    assert len(liens) == 1
