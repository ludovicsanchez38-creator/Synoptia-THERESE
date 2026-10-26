"""B-1323/B-1324 : conserver le texte des grands documents professionnels."""

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from docx import Document

from tests.test_c20f_docx_borne import extraire_borne


def creer_document_professionnel(path, tableaux):
    """Construit le XML linéairement, avec un texte attendu indépendant du parseur."""
    base = BytesIO()
    Document().save(base)
    blocs = ['<w:p><w:r><w:t>Avant</w:t></w:r></w:p>']
    attendu = ["Avant"]
    for numero, (lignes, colonnes) in enumerate(tableaux, 1):
        blocs.append("<w:tbl>")
        for ligne in range(1, lignes + 1):
            cellules = [
                f"Unité {numero} / ligne {ligne} / rubrique {colonne}"
                for colonne in range(1, colonnes + 1)
            ]
            attendu.append("\t".join(cellules))
            blocs.append("<w:tr>" + "".join(
                f"<w:tc><w:p><w:r><w:t>{texte}</w:t></w:r></w:p></w:tc>"
                for texte in cellules
            ) + "</w:tr>")
        blocs.append("</w:tbl>")
    blocs.append('<w:p><w:r><w:t>Après</w:t></w:r></w:p>')
    attendu.append("Après")
    xml = (
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>" + "".join(blocs) + "</w:body></w:document>"
    )
    with ZipFile(base) as source, ZipFile(path, "w", ZIP_DEFLATED) as cible:
        for entree in source.infolist():
            cible.writestr(entree, xml if entree.filename == "word/document.xml" else source.read(entree))
    return "\n\n".join(attendu)


def test_b1323_catalogue_1500_lignes_complet(tmp_path):
    path = tmp_path / "catalogue.docx"
    attendu = creer_document_professionnel(path, [(1500, 4)])
    assert extraire_borne(path) == attendu


@pytest.mark.parametrize("lignes,colonnes", [
    (1001, 2), (1024, 3), (1250, 4), (1501, 4), (1777, 5),
    (2000, 4), (2500, 3), (3333, 3), (4096, 2), (10_000, 1),
])
def test_b1323_dix_catalogues_apres_correctif(tmp_path, lignes, colonnes):
    path = tmp_path / "catalogue-rejeu.docx"
    attendu = creer_document_professionnel(path, [(lignes, colonnes)])
    assert extraire_borne(path) == attendu
