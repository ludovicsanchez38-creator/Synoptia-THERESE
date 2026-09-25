"""B-1371 (persona Hugo, cycle 13, haute) : la synchronisation de dossier
n'indexait aucun fichier.

Pour garantir que l'on indexe exactement les octets vérifiés au plan, la
synchronisation copie chaque fichier dans un temporaire
(`indexation._copier_si_conforme`), puis extrait le texte de cette copie. Le
temporaire était créé sans extension ; `file_parser.extract_text` aiguille sur
l'extension : « Unsupported file type: » pour le `.md` comme pour le `.txt`,
zéro fragment, et le chat répondait que `specifications.md` n'existait pas.
Présent depuis 05165c10 (0.45).
"""

import hashlib

import pytest
from app.services.file_parser import extract_text
from app.services.indexation import _copier_si_conforme


@pytest.mark.parametrize("nom", ["specifications.md", "notes-reunion.txt", "README.MD"])
def test_la_copie_verifiee_reste_lisible_par_l_extracteur(tmp_path, nom):
    source = tmp_path / nom
    source.write_text("# Orion\n\nLa variante B est retenue pour l'API client.\n", encoding="utf-8")
    empreinte = hashlib.sha256(source.read_bytes()).hexdigest()

    copie = _copier_si_conforme(source, empreinte)
    try:
        assert copie is not None
        assert copie.suffix == source.suffix
        texte = extract_text(copie)
        assert texte and "variante B" in texte
    finally:
        if copie is not None:
            copie.unlink(missing_ok=True)


def test_une_empreinte_divergente_ne_laisse_aucune_copie(tmp_path):
    source = tmp_path / "specifications.md"
    source.write_text("contenu", encoding="utf-8")
    assert _copier_si_conforme(source, "0" * 64) is None
