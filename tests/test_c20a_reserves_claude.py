"""Contre-relecture C20-A : vrais PDF via generate_document, sans modèle."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

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


@pytest.mark.asyncio
async def test_b1242_bloc_code_preformate_sans_titre(registre_pdf):
    code = '# commentaire\nfor nom in ["Zoé", "Noël"]:\n    print(nom)\n    total = 2 * 3'
    lecteur = await generer(registre_pdf, f"Avant\n```python\n{code}\n```\nAprès")
    texte = lecteur.pages[0].extract_text()
    assert code in texte
    assert "```" not in texte
    for ligne in code.splitlines():
        fontes = [f for t, f, _ in fragments_pdf(lecteur) if ligne in t]
        assert fontes and all("Courier" in f for f in fontes), (ligne, fontes)


# Inventées après le vert B-1242, y compris une clôture absente et la pagination.
@pytest.mark.asyncio
@pytest.mark.parametrize(("langue", "code", "ferme"), [
    ("bash", "# préparer\nprintf '%s' 'été'\nprintf '%s' 'fin'", True),
    ("python", "def saluer():\n    nom = 'Anaïs'\n    return nom", True),
    ("txt", "<img src='file:///absent'/> & **brut**\n> brut\n---", True),
    ("sql", "SELECT nom, montant\n  FROM prestations\n WHERE montant > 7;", True),
    ("", "  colonne A  colonne B  \n    17         29", True),
    ("python", "if valide:\n\tprint('accord')", True),
    ("text", "| A | B |\n|:-|-:|\n| x | y |", True),
    ("python", "# sans clôture\nvaleur = 4 ** 3\n    suite", False),
    ("text", "x" * 1800, True),
    ("text", "\n".join(f"# instruction {i:03d}" for i in range(130)), True),
])
async def test_b1242_dix_entrees_apres_vert(registre_pdf, monkeypatch, langue, code, ferme):
    def interdire(*args, **kwargs):
        pytest.fail("Lecture externe depuis un bloc préformaté")

    monkeypatch.setattr("reportlab.lib.utils.open_for_read", interdire)
    contenu = f"```{langue}\n{code}" + ("\n```" if ferme else "")
    lecteur = await generer(registre_pdf, contenu)
    fragments = [(t, f) for t, f, _ in fragments_pdf(lecteur) if "Courier" in f]
    extrait = "\n".join(t for t, _ in fragments)
    if len(code) == 1800:
        assert extrait.replace("\n", "") == code
    else:
        assert extrait == code.expandtabs(4)
    assert "```" not in "\n".join(p.extract_text() for p in lecteur.pages)
    if code.startswith("# instruction"):
        assert len(lecteur.pages) >= 2


@pytest.mark.asyncio
async def test_b1243_tableau_separateur_court(registre_pdf):
    lecteur = await generer(registre_pdf, "| Poste | Montant |\n|:--|--:|\n"
                            "| Conseil | 490 € |\n| Formation | 2 490 € |")
    texte = lecteur.pages[0].extract_text()
    assert "Poste\nMontant\nConseil\n490 €\nFormation\n2 490 €" in texte
    assert "|" not in texte and "--" not in texte
    assert any("Poste" in t and "Bold" in f for t, f, _ in fragments_pdf(lecteur))


# Dix entrées créées après le vert B-1243 : tirets et deux-points combinés.
@pytest.mark.asyncio
@pytest.mark.parametrize(("separateur", "entete", "valeurs"), [
    ("|-|-|", ["Agence", "Ville"], ["Aube", "Troyes"]),
    ("|:-|-:|", ["Lot", "Prix"], ["Bougies", "31 €"]),
    ("|:-:|:-:|", ["Auteure", "Œuvre"], ["Inès", "Éclosion"]),
    ("|--|--|", ["Produit", "Quantité"], ["Tisane", "24"]),
    ("|:--|--:|", ["Poste", "Montant"], ["Transport", "87 €"]),
    ("| :--: | ---: |", ["Équipe", "Effectif"], ["Création", "12"]),
    ("- | :-:", ["Horaire", "Activité"], ["09 h", "Accueil"]),
    ("|-:|", ["Solde"], ["176 €"]),
    ("|:-|--:|:-:|", ["Article", "Stock", "Rayon"], ["Cahier", "57", "Sud"]),
    ("|---|:-|", ["Projet", "Clôture"], ["Rénovation", "Noël"]),
])
async def test_b1243_dix_entrees_apres_vert(registre_pdf, separateur, entete, valeurs):
    contenu = " | ".join(entete) + "\n" + separateur + "\n" + " | ".join(valeurs)
    # Une colonne doit garder ses barres pour être identifiée comme tableau.
    if len(entete) == 1:
        contenu = f"|{entete[0]}|\n{separateur}\n|{valeurs[0]}|"
    lecteur = await generer(registre_pdf, contenu)
    texte = lecteur.pages[0].extract_text()
    assert "\n".join(entete + valeurs) in texte
    assert "|" not in texte and separateur not in texte
    for cellule in entete:
        assert any(cellule in t and "Bold" in f for t, f, _ in fragments_pdf(lecteur))


async def verifier_refus_route_pdf(registre, monkeypatch, mode, contenu, requete):
    from app.routers import skills
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    # Le parcours chat reste disponible et son fichier est relu avant le refus.
    lecteur = await generer(registre, contenu)
    assert p104.texte_du_corps(lecteur) == "".join(contenu.split())
    fichiers_avant = {p: p.read_bytes() for p in registre.output_dir.iterdir()}
    cache_avant = set(registre._file_cache)
    llm = SimpleNamespace(
        config=SimpleNamespace(provider=SimpleNamespace(value="simulé"), model="sans-réseau"),
        generate_content=AsyncMock(return_value=contenu),
    )
    monkeypatch.setattr(skills, "get_llm_service", lambda: llm)
    monkeypatch.setattr(skills, "get_model_capability", lambda *_: mode)
    monkeypatch.setattr(skills, "get_cached_profile", lambda: None)
    monkeypatch.setattr(skills, "enregistrer_usage_llm", lambda *args: None)
    session = AsyncMock()
    resultat = MagicMock()
    resultat.scalars.return_value.all.return_value = []
    session.execute.return_value = resultat
    app = FastAPI()
    app.include_router(skills.router, prefix="/api/skills")
    app.dependency_overrides[skills.get_session] = lambda: session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        reponse = await client.post("/api/skills/execute/pdf-pro", json=requete)
    assert {p: p.read_bytes() for p in registre.output_dir.iterdir()} == fichiers_avant
    assert set(registre._file_cache) == cache_avant
    assert reponse.status_code == 400, reponse.text
    assert "chat" in reponse.json()["detail"].lower()
    llm.generate_content.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["code", "markdown"])
async def test_b1245_route_pdf_refuse_sans_orphelin(registre_pdf, monkeypatch, mode):
    await verifier_refus_route_pdf(
        registre_pdf, monkeypatch, mode, "Attestation remise à Maëlle.",
        {"prompt": "Prépare une attestation PDF", "title": "Attestation"},
    )


# Dix demandes nouvelles après le vert B-1245, avec variantes des paramètres HTTP.
@pytest.mark.asyncio
@pytest.mark.parametrize(("mode", "contenu", "options"), [
    ("code", "Bon de remise : cinq dossiers.", {}),
    ("markdown", "Attestation de présence : Chloé.", {"title": "Présence"}),
    ("code", "Planning de décembre : atelier le jeudi.", {"title": ""}),
    ("markdown", "Procès-verbal : résolution adoptée.", {"title": None}),
    ("code", "Bordereau : matériel réceptionné.", {"template": "synoptia-dark"}),
    ("markdown", "Note de frais : 63 € remboursés.", {"template": "inconnu"}),
    ("code", "Lettre de mission : diagnostic initial.", {"context": {"client": "Atelier Boréal"}}),
    ("markdown", "Inventaire : trois tables et huit chaises.", {"context": {"lignes": [3, 8]}}),
    ("code", "Synthèse : réouverture mardi.", {"title": "../../ailleurs/Été"}),
    ("markdown", "Compte rendu : prochaine séance à Nîmes.", {"title": "Réunion", "context": {}}),
])
async def test_b1245_dix_entrees_apres_vert(registre_pdf, monkeypatch, mode, contenu, options):
    await verifier_refus_route_pdf(
        registre_pdf, monkeypatch, mode, contenu, {"prompt": contenu, **options},
    )
