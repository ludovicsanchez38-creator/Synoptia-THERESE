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
