"""P-104 : un vrai PDF depuis le chat, relu sans aucun appel de modèle."""

from io import BytesIO
from pathlib import Path

import pytest
import pytest_asyncio
from app.services import workspace_tools
from app.services.skills import registry as registre_module
from app.services.skills.base import SkillExecuteRequest
from app.services.tool_capabilities import capacites_outils
from app.services.tool_confirmations import register_pending
from pypdf import PdfReader


@pytest_asyncio.fixture
async def registre_pdf(tmp_path, monkeypatch):
    monkeypatch.setattr(registre_module.settings, "data_dir", tmp_path)
    monkeypatch.setattr(registre_module, "_registry", None)
    await registre_module.init_skills()
    registre = registre_module.get_skills_registry()
    yield registre
    workspace_tools.drain_generated_files()


async def generer(registre, contenu, titre="Synthèse française"):
    workspace_tools.start_generated_files_collection()
    message = await workspace_tools.execute_workspace_tool(
        "generate_document",
        {"format": "pdf", "title": titre, "content": contenu},
        None,
    )
    fichiers = workspace_tools.drain_generated_files()
    assert len(fichiers) == 1, message
    fichier = fichiers[0]
    assert fichier["format"] == "pdf"
    assert fichier["local_dir"] == str(registre.output_dir)
    resultat = registre.get_file(fichier["file_id"])
    assert resultat.mime_type == "application/pdf"
    assert resultat.file_path.parent == registre.output_dir
    assert resultat.file_path.read_bytes().startswith(b"%PDF-")
    return PdfReader(resultat.file_path)


def test_le_modele_connait_le_format_pdf():
    outil = workspace_tools.GENERATE_DOCUMENT_TOOL["function"]
    assert "pdf" in outil["parameters"]["properties"]["format"]["enum"]
    assert "PDF" in outil["description"]
    assert "pdf" in capacites_outils(["generate_document"]).lower()


@pytest.mark.asyncio
async def test_une_page_structuree_conserve_les_accents(registre_pdf):
    lecteur = await generer(registre_pdf, """# Synthèse française

## Décisions de l'équipe
L'été à Noël : cœur, œuvre, ŒUVRE, Æsir, garçon, où, naïf, « déjà », 25 €.

- Préparer l'échéancier
- Vérifier la clôture

### Étapes suivantes
1. Réunir les associés
2. Valider le budget

| Désignation | Coût |
| --- | --- |
| Étude préalable | 25 € |
| Maîtrise d'œuvre | 50 € |
""")
    assert len(lecteur.pages) == 1
    texte = lecteur.pages[0].extract_text()
    for attendu in (
        "Synthèse française", "Décisions de l'équipe", "L'été à Noël",
        "cœur", "œuvre", "ŒUVRE", "Æsir", "garçon", "où", "naïf",
        "« déjà »", "25 €", "Préparer l'échéancier", "Vérifier la clôture",
        "Étapes suivantes", "Réunir les associés", "Valider le budget",
        "Désignation", "Coût", "Étude préalable", "Maîtrise d'œuvre", "Page 1",
    ):
        assert attendu in texte
    assert texte.count("Synthèse française") == 1
    assert "##" not in texte
    assert "| --- |" not in texte


@pytest.mark.asyncio
async def test_un_document_long_est_pagine_sans_perte(registre_pdf):
    paragraphes = [
        f"Repère {i:03d} : décision vérifiée, échéance arrêtée et équipe prévenue."
        for i in range(180)
    ]
    lecteur = await generer(registre_pdf, "\n\n".join(paragraphes))
    assert len(lecteur.pages) >= 3
    texte = "\n".join(page.extract_text() for page in lecteur.pages)
    for paragraphe in paragraphes:
        assert paragraphe in texte
    for numero, page in enumerate(lecteur.pages, 1):
        assert f"Page {numero}" in page.extract_text()


@pytest.mark.asyncio
async def test_un_tableau_long_repete_son_entete(registre_pdf):
    contenu = "| Désignation | Échéance |\n| --- | --- |\n" + "\n".join(
        f"| Prestation {i:03d} | Décembre |" for i in range(100)
    )
    lecteur = await generer(registre_pdf, contenu)
    assert len(lecteur.pages) >= 2
    for page in lecteur.pages:
        assert "Désignation" in page.extract_text()
    texte = "\n".join(page.extract_text() for page in lecteur.pages)
    assert "Prestation 000" in texte and "Prestation 099" in texte


@pytest.mark.asyncio
async def test_les_balises_restent_du_texte_sans_lecture_externe(registre_pdf, monkeypatch):
    def interdire_ressource(*args, **kwargs):
        pytest.fail("Le PDF a tenté de charger une ressource externe")

    monkeypatch.setattr("reportlab.lib.utils.open_for_read", interdire_ressource)
    contenu = '<img src="file:///inexistant.png"/> <b>été</b> & <script>alerte</script>'
    lecteur = await generer(registre_pdf, contenu, titre="<b>Échéance</b>")
    texte = lecteur.pages[0].extract_text()
    assert "<b>Échéance</b>" in texte
    assert contenu in texte


@pytest.mark.asyncio
async def test_une_ligne_sans_espace_se_replie_sur_plusieurs_pages(registre_pdf):
    contenu = "é" * 24000
    lecteur = await generer(registre_pdf, contenu)
    assert len(lecteur.pages) >= 2
    texte = "".join(page.extract_text() for page in lecteur.pages)
    # Isoler les lignes du contenu pour ne pas compter les accents du pied de page.
    assert "".join(ligne for ligne in texte.splitlines() if set(ligne) == {"é"}) == contenu


@pytest.mark.asyncio
async def test_une_emphase_triple_produit_un_pdf_et_sa_carte(registre_pdf):
    lecteur = await generer(registre_pdf, "Décision ***très importante*** à confirmer.")
    assert "Décision très importante à confirmer." in lecteur.pages[0].extract_text()


@pytest.mark.asyncio
async def test_une_formule_en_code_conserve_ses_asterisques(registre_pdf):
    lecteur = await generer(registre_pdf, "Formule : `=B2*C2*(1-D2)`.")
    assert "Formule : =B2*C2*(1-D2)." in lecteur.pages[0].extract_text()


@pytest.mark.asyncio
async def test_un_entete_geant_conserve_son_texte_et_les_cellules(registre_pdf):
    entete = "é" * 4000
    lecteur = await generer(
        registre_pdf, f"| {entete} | B |\n| --- | --- |\n| A | C |",
    )
    lignes = "\n".join(page.extract_text() for page in lecteur.pages).splitlines()
    assert "".join(ligne for ligne in lignes if set(ligne) == {"é"}) == entete
    assert {"A", "B", "C"} <= set(lignes)


def texte_du_corps(lecteur):
    """Relire tout le contenu, sans titre ni pied de page, malgré les coupures."""
    lignes = (ligne for page in lecteur.pages for ligne in page.extract_text().splitlines())
    return "".join(
        "".join(ligne.split()) for ligne in lignes
        if ligne not in {"Synthèse française", "Généré par THÉRÈSE - Synoptïa"}
        and not ligne.startswith("Page ")
    )


# Inventées après le vert des deux régressions d'Astra : dix par défaut.
@pytest.mark.asyncio
@pytest.mark.parametrize(("contenu", "attendu", "polices"), [
    pytest.param(
        "**Ferme** puis *souple* et ***résolu***.", "Ferme puis souple et résolu.",
        [("Ferme", True, False), ("souple", False, True), ("résolu", True, True)],
        id="emphases-cote-a-cote",
    ),
    pytest.param(
        "**Accord *prioritaire*** et **délai *ajustable* demain**.",
        "Accord prioritaire et délai ajustable demain.",
        [("Accord", True, False), ("prioritaire", True, True), ("demain", True, False)],
        id="italique-dans-gras",
    ),
    pytest.param(
        "*Accord **prioritaire*** puis *délai **ajustable** demain*.",
        "Accord prioritaire puis délai ajustable demain.",
        [("Accord", False, True), ("prioritaire", True, True), ("demain", False, True)],
        id="gras-dans-italique",
    ),
    pytest.param(
        "## ***Relevé***\n\n3. **À *relire***\n\n| ***Avis*** | *Suite* |\n"
        "| --- | --- |\n| **<validé>** | *été* |",
        "Relevé 3. À relire Avis Suite <validé> été", [], id="titres-listes-cellules",
    ),
    pytest.param(
        "Une **décision *contestée** à confirmer* & <avis>.",
        "Une **décision *contestée** à confirmer* & <avis>.", [], id="emphases-croisees",
    ),
    pytest.param(
        "Début *isolé et **inachevé puis ***suspendu <fin> & suite.",
        "Début *isolé et **inachevé puis ***suspendu <fin> & suite.", [], id="asterisques-orphelins",
    ),
    pytest.param(
        "Avis ****trouble****, *****vraiment***** et ******oui******.",
        "Avis ****trouble****, *****vraiment***** et ******oui******.", [], id="longues-series-ambigues",
    ),
    pytest.param(
        r"Texte \*littéral\* et ** stable ** puis * *.",
        r"Texte \*littéral\* et ** stable ** puis * *.", [], id="echappements-et-espaces",
    ),
    pytest.param(
        "Une **décision\n*révisée* demain**.", "Une décision révisée demain.",
        [("révisée", True, True)], id="emphases-sur-plusieurs-lignes",
    ),
    pytest.param(
        '***<img src="https://exemple.invalid/sceau"/>*** et *&inconnue; <b>été</b>*.',
        '<img src="https://exemple.invalid/sceau"/> et &inconnue; <b>été</b>.', [],
        id="balises-litterales-dans-emphases",
    ),
])
async def test_dix_emphases_apres_correctif(registre_pdf, monkeypatch, contenu, attendu, polices):
    def interdire_ressource(*args, **kwargs):
        pytest.fail("Le balisage du PDF a déclenché une lecture externe")

    monkeypatch.setattr("reportlab.lib.utils.open_for_read", interdire_ressource)
    lecteur = await generer(registre_pdf, contenu)
    assert texte_du_corps(lecteur) == "".join(attendu.split())
    fragments = []

    def relever_police(texte, matrice, transformation, police, taille):
        if police:
            fragments.append((texte, str(police["/BaseFont"])))

    for page in lecteur.pages:
        page.extract_text(visitor_text=relever_police)
    for mot, gras, italique in polices:
        fontes = [fonte for texte, fonte in fragments if mot in texte]
        assert fontes, mot
        assert all(("Bold" in fonte) == gras for fonte in fontes), (mot, fontes)
        assert all(("Oblique" in fonte or "Italic" in fonte) == italique for fonte in fontes)


# Inventées après le vert de la formule signalée par Astra v2.
@pytest.mark.asyncio
@pytest.mark.parametrize(("contenu", "attendu", "codes"), [
    pytest.param(
        "Total : `=SUM(A3:A9)*$F$2`.", "Total : =SUM(A3:A9)*$F$2.",
        ["=SUM(A3:A9)*$F$2"], id="excel-reference-absolue",
    ),
    pytest.param(
        'Choix : `=IF(C4<0,"*",C4*D4)`.', 'Choix : =IF(C4<0,"*",C4*D4).',
        ['=IF(C4<0,"*",C4*D4)'], id="excel-comparaison-et-guillemets",
    ),
    pytest.param(
        r"Sources : `C:\Exports\2027\*.csv` ; `D:\Archives\*\bilan.*`.",
        r"Sources : C:\Exports\2027\*.csv ; D:\Archives\*\bilan.*.",
        [r"C:\Exports\2027\*.csv", r"D:\Archives\*\bilan.*"], id="chemins-windows",
    ),
    pytest.param(
        r"Motifs : `^[A-Z]*\d+$` et `a\*b.*`.", r"Motifs : ^[A-Z]*\d+$ et a\*b.*.",
        [r"^[A-Z]*\d+$", r"a\*b.*"], id="regex-et-asterisque-echappe",
    ),
    pytest.param(
        "| Expression | `x*y*z` |\n| --- | --- |\n| `items[0]*2` | `p*q*r` |",
        "Expression\nx*y*z\nitems[0]*2\np*q*r",
        ["x*y*z", "items[0]*2", "p*q*r"], id="code-entete-et-cellules",
    ),
    pytest.param(
        "Calcul `r*s*t`, puis `reste **lisible**.", "Calcul r*s*t, puis `reste lisible.",
        ["r*s*t"], id="backtick-non-ferme",
    ),
    pytest.param(
        "***Calcul `h*i*j` confirmé*** et *`u*v*w`*.",
        "Calcul h*i*j confirmé et u*v*w.", ["h*i*j", "u*v*w"], id="code-dans-emphases",
    ),
    pytest.param(
        "Copier : ` total  =  prix * 2 `.", "Copier :  total  =  prix * 2 .",
        [" total  =  prix * 2 "], id="espaces-du-code",
    ),
    pytest.param(
        'Balises : `<img src="file:///absent"/> & *.*`.',
        'Balises : <img src="file:///absent"/> & *.*.',
        ['<img src="file:///absent"/> & *.*'], id="balise-litterale-sans-lecture",
    ),
    pytest.param(
        "## `p**q`\n\n2. Appliquer `x***y`.\n\nHors code : 7 * 8, étoile \\*.",
        "p**q\n2. Appliquer x***y.\nHors code : 7 * 8, étoile \\*.",
        ["p**q", "x***y"], id="titre-liste-et-asterisques-hors-code",
    ),
])
async def test_dix_codes_apres_astra_v2(registre_pdf, monkeypatch, contenu, attendu, codes):
    def interdire_ressource(*args, **kwargs):
        pytest.fail("Le code imprimé a déclenché une lecture externe")

    monkeypatch.setattr("reportlab.lib.utils.open_for_read", interdire_ressource)
    lecteur = await generer(registre_pdf, contenu)
    lignes = (ligne for page in lecteur.pages for ligne in page.extract_text().splitlines())
    texte = "\n".join(
        ligne for ligne in lignes
        if ligne not in {"Synthèse française", "Généré par THÉRÈSE - Synoptïa"}
        and not ligne.startswith("Page ")
    )
    # Comparer aussi les espaces : ils font partie du code à recopier.
    assert texte == attendu
    fragments_code = []

    def relever_code(texte, matrice, transformation, police, taille):
        if police and police["/BaseFont"] == "/Courier":
            fragments_code.append(texte)

    for page in lecteur.pages:
        page.extract_text(visitor_text=relever_code)
    for code in codes:
        assert code in "".join(fragments_code)


def tableau_markdown(entete, lignes):
    contenu = "\n".join(
        "| " + " | ".join(ligne) + " |"
        for ligne in [entete, ["---"] * len(entete), *lignes]
    )
    attendu = " ".join(cellule for ligne in [entete, *lignes] for cellule in ligne)
    return contenu, attendu


@pytest.mark.asyncio
@pytest.mark.parametrize(("contenu", "attendu", "pages_min"), [
    pytest.param(*tableau_markdown(["é" * 10000], [["Première"], ["Dernière"]]),
                 2, id="entete-une-colonne"),
    pytest.param(*tableau_markdown([c * (1000 + i) for i, c in enumerate("abcdefgh")],
                                  [[f"Valeur{i}" for i in range(8)]]),
                 2, id="entetes-huit-colonnes"),
    pytest.param(*tableau_markdown(["Gauche", "Droite"], [["ü" * 12000, "ç" * 11000]]),
                 2, id="deux-cellules-geantes"),
    pytest.param(*tableau_markdown(["Récit"], [["Œuvre achevée à Noël. " * 800], ["Clôture"]]),
                 2, id="cellule-avec-espaces"),
    pytest.param(*tableau_markdown([f"Col{i}" for i in range(8)],
                                  [[c * 3000 for c in "abcdefgh"]]),
                 2, id="cellules-huit-colonnes"),
    pytest.param(*tableau_markdown(["ê" * 9000], [["à" * 13000], ["œ" * 7000]]),
                 2, id="entete-et-corps-geants"),
    pytest.param(*tableau_markdown(["é" * 2700, "Repère"], [["Suite", "Fin"]]),
                 1, id="entete-proche-hauteur-page"),
    pytest.param(*tableau_markdown(["A", "B", "C", "D", "E", "F", "G", "H"],
                                  [["", "", "z" * 9000, "", "Fin", "", "", ""]]),
                 2, id="cellules-geantes-et-vides"),
    pytest.param(*tableau_markdown(["Accent", "Repère"],
                                  [["é" * 6000, "Premier"], ["à" * 6000, "Dernier"]]),
                 2, id="plusieurs-lignes-geantes"),
    pytest.param("œ" * 20000, "œ" * 20000, 2, id="mot-unique-20000-hors-tableau"),
])
async def test_dix_volumes_apres_correctif(registre_pdf, contenu, attendu, pages_min):
    lecteur = await generer(registre_pdf, contenu)
    assert len(lecteur.pages) >= pages_min
    # Égalité de tout le texte : ni troncature, ni duplication, ni cellule perdue.
    assert texte_du_corps(lecteur) == "".join(attendu.split())


@pytest.mark.asyncio
async def test_le_vide_est_refuse_sans_fichier(registre_pdf):
    workspace_tools.start_generated_files_collection()
    message = await workspace_tools.execute_workspace_tool(
        "generate_document", {"format": "pdf", "content": " \n\t "}, None,
    )
    assert "Aucun contenu" in message
    assert workspace_tools.drain_generated_files() == []
    reponse = await registre_pdf.execute(
        "pdf-pro", SkillExecuteRequest(prompt="Vide"), " \n\t ",
    )
    assert not reponse.success
    assert "vide" in reponse.error.lower()
    assert list(registre_pdf.output_dir.iterdir()) == []


@pytest.mark.asyncio
@pytest.mark.parametrize("lien", [False, True], ids=["chemin_exterieur", "lien_symbolique"])
async def test_un_chemin_hors_sorties_est_refuse(registre_pdf, tmp_path, monkeypatch, lien):
    skill = registre_pdf.get("pdf-pro")
    assert skill is not None
    dehors = tmp_path / "hors-espace" / "interdit.pdf"
    dehors.parent.mkdir()
    cible = registre_pdf.output_dir / "lien.pdf" if lien else dehors
    if lien:
        cible.symlink_to(dehors)
    monkeypatch.setattr(skill, "get_output_path", lambda *_: cible)
    reponse = await registre_pdf.execute(
        "pdf-pro", SkillExecuteRequest(prompt="Évasion"), "Ne pas écrire dehors.",
    )
    assert not reponse.success
    assert "hors" in reponse.error.lower()
    assert not dehors.exists()


@pytest.mark.asyncio
async def test_un_titre_chemin_est_neutralise(registre_pdf):
    await generer(registre_pdf, "Reste dans les sorties.", titre="../../ailleurs/Été.pdf")
    fichiers = list(registre_pdf.output_dir.iterdir())
    assert len(fichiers) == 1
    assert fichiers[0].resolve().is_relative_to(registre_pdf.output_dir.resolve())


@pytest.mark.asyncio
async def test_confirmation_carte_et_telechargement_reel(client, registre_pdf):
    cid = register_pending("generate_document", {
        "format": "pdf", "title": "Réunion d'été", "content": "Décision : budget approuvé.",
    })
    reponse = await client.post("/api/chat/confirm-tool", json={
        "confirmation_id": cid, "approved": True,
    })
    assert reponse.status_code == 200
    fichiers = reponse.json().get("skill_files", [])
    assert len(fichiers) == 1, reponse.json()
    fichier = fichiers[0]
    assert fichier["format"] == "pdf"
    assert "Document PDF créé" in reponse.json()["result"]
    for avec_cache in (True, False):
        if not avec_cache:
            registre_pdf._file_cache.clear()
        telechargement = await client.get(fichier["download_url"])
        assert telechargement.status_code == 200
        assert telechargement.headers["content-type"] == "application/pdf"
        lecteur = PdfReader(BytesIO(telechargement.content))
        assert "Décision : budget approuvé." in lecteur.pages[0].extract_text()
    assert Path(fichier["local_dir"]) == registre_pdf.output_dir
