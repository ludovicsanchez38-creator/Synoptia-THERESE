"""Contre-relecture C20-A : vrais PDF via generate_document, sans modèle."""

import pytest

from tests import test_p104_pdf_depuis_chat as p104

generer = p104.generer
registre_pdf = p104.registre_pdf


def fragments_pdf(lecteur):
    fragments = []

    def relever(texte, cm, tm, police, taille):
        if texte.strip() and police:
            fragments.append((texte.rstrip("\n"), str(police["/BaseFont"]), tm[5] + cm[5]))

    for page in lecteur.pages:
        page.extract_text(visitor_text=relever)
    return fragments


@pytest.mark.asyncio
async def test_b1241_courrier_lignes_citation_separateur(registre_pdf):
    lecteur = await generer(registre_pdf, "Madame Martin\nSARL Dupont\n12 rue des Lilas\n75001 Paris\n\n"
                            "La facture reste impayée.\n> Rappel : merci de régler.\n---\n"
                            "Cordialement,\nÉlodie Martin")
    texte = lecteur.pages[0].extract_text()
    assert "Madame Martin\nSARL Dupont\n12 rue des Lilas\n75001 Paris" in texte
    assert "Cordialement,\nÉlodie Martin" in texte
    assert ">" not in texte and "---" not in texte
    fragments = fragments_pdf(lecteur)
    assert any("Rappel : merci de régler." in t and ("Oblique" in f or "Italic" in f)
               for t, f, _ in fragments)
    positions = {t.strip(): y for t, _, y in fragments}
    assert positions["75001 Paris"] - positions["La facture reste impayée."] > (
        positions["12 rue des Lilas"] - positions["75001 Paris"]
    )


# Dix entrées inventées après le premier vert B-1241.
@pytest.mark.asyncio
@pytest.mark.parametrize(("contenu", "lignes"), [
    ("À Maëlle\nAtelier du Rhône\n69002 Lyon", ["À Maëlle", "Atelier du Rhône", "69002 Lyon"]),
    ("Fait à Sète\nLe 14 novembre\nPour la direction", ["Fait à Sète", "Le 14 novembre", "Pour la direction"]),
    ("Lundi : accueil\r\nMardi : visite", ["Lundi : accueil", "Mardi : visite"]),
    ("Une **décision\n*révisée* demain**.", ["Une décision", "révisée demain."]),
    ("Préambule\n\nParagraphe A\nSuite A\n\nParagraphe B", ["Préambule", "Paragraphe A", "Suite A", "Paragraphe B"]),
    ("> **Accord** de Zoé\n> Réserve de Noël\nConclusion", ["Accord de Zoé", "Réserve de Noël", "Conclusion"]),
    ("Avant\n---\nAprès", ["Avant", "Après"]),
    ("Ouverture\n***\nClôture", ["Ouverture", "Clôture"]),
    ("Début\n___\nFin", ["Début", "Fin"]),
    ("<br/> reste littéral\nMarge < 7 & seuil > 2", ["<br/> reste littéral", "Marge < 7 & seuil > 2"]),
])
async def test_b1241_dix_entrees_apres_vert(registre_pdf, contenu, lignes):
    lecteur = await generer(registre_pdf, contenu)
    corps = [ligne.strip() for page in lecteur.pages for ligne in page.extract_text().splitlines()
             if ligne not in {"Synthèse française", "Généré par THÉRÈSE - Synoptïa"}
             and not ligne.startswith("Page ")]
    assert corps == lignes
