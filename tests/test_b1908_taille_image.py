"""B-1908 : une image trop grosse ne s'affiche pas à la taille limite."""
from app.services.images_jointes import TAILLE_MAX_IMAGE, charger_images_jointes


def test_depassement_minimal_affiche_une_taille_superieure_a_la_limite(tmp_path, monkeypatch):
    from app.services import images_jointes

    image = tmp_path / "image.png"
    with image.open(mode="wb") as fichier:
        fichier.truncate(TAILLE_MAX_IMAGE + 1)
    monkeypatch.setattr(images_jointes, "validate_file_path", lambda chemin, _: image)
    chargees, avertissements = charger_images_jointes([str(image)])
    assert chargees == []
    assert "5,01 Mo" in avertissements[0]
    assert "limite 5 Mo" in avertissements[0]
