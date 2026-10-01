"""B-1767 : qualifier le lecteur PDF après le correctif pypdf de sécurité.

Les documents sont synthétiques et générés par ReportLab. Le lecteur pypdf,
le parseur produit et l'outil read_file ne sont pas substitués. Les fixtures
habituelles isolent la base et neutralisent les services externes.
Ces contrôles d'intégration ne reproduisent pas les huit CVE elles-mêmes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from app.models.entities import FileMetadata
from app.services.file_parser import extract_text
from app.services.memory_tools import execute_memory_tool
from reportlab.pdfgen.canvas import Canvas
from sqlalchemy.ext.asyncio import AsyncSession


def _pdf(chemin: Path, pages: list[list[str]], *, compresse: bool = True) -> Path:
    document = Canvas(str(chemin), pageCompression=int(compresse))
    for lignes in pages:
        document.setFont("Helvetica", 8)
        for numero, ligne in enumerate(lignes):
            document.drawString(36, 800 - numero * 16, ligne)
        document.showPage()
    document.save()
    return chemin


async def _indexer_metadonnee(
    session: AsyncSession, chemin: Path, *, scope: str = "global",
    scope_id: str | None = None,
) -> str:
    fichier = FileMetadata(
        path=str(chemin),
        name=chemin.name,
        extension=".pdf",
        mime_type="application/pdf",
        size=chemin.stat().st_size,
        chunk_count=1,
        scope=scope,
        scope_id=scope_id,
    )
    session.add(fichier)
    await session.commit()
    return fichier.id


def _contenu_enveloppe(brut: str) -> dict[str, Any]:
    debut = "[Source: fichier]\n"
    fin = "\n[End fichier]"
    assert brut.startswith(debut), "La lecture réussie doit rester une source balisée."
    assert brut.endswith(fin)
    return json.loads(brut[len(debut):-len(fin)])


@pytest.mark.parametrize("compresse", [False, True], ids=["brut", "flate"])
def test_deux_pages_sont_reellement_extraites_dans_l_ordre(
    tmp_path: Path, compresse: bool,
) -> None:
    chemin = _pdf(
        tmp_path / "deux-pages.pdf",
        [["École : échéance déjà réglée, 1 234,56 EUR."],
         ["Deuxième page : réunion prévue, 789,01 EUR."]],
        compresse=compresse,
    )
    assert (b"/FlateDecode" in chemin.read_bytes()) is compresse

    texte = extract_text(chemin)

    assert texte is not None
    assert "École : échéance déjà réglée, 1 234,56 EUR." in texte
    assert "Deuxième page : réunion prévue, 789,01 EUR." in texte
    assert texte.index("--- Page 1 ---") < texte.index("--- Page 2 ---")
    assert texte.index("École") < texte.index("Deuxième page")
    assert "tronqué" not in texte


def test_cent_une_pages_sont_bornees_et_la_troncature_est_annoncee(
    tmp_path: Path,
) -> None:
    chemin = _pdf(
        tmp_path / "cent-une-pages.pdf",
        [[f"TEXTE_PAGE_{numero:03d}"] for numero in range(1, 102)],
    )

    texte = extract_text(chemin)

    assert texte is not None
    assert "TEXTE_PAGE_001" in texte
    assert "TEXTE_PAGE_100" in texte
    assert "TEXTE_PAGE_101" not in texte
    assert texte.count("--- Page ") == 100
    assert texte.endswith("[... tronqué à 100 pages]")


def test_un_petit_pdf_tronque_ne_passe_pas_pour_une_extraction_reussie(
    tmp_path: Path,
) -> None:
    chemin = tmp_path / "incomplet.pdf"
    chemin.write_bytes(b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\n")

    assert extract_text(chemin) is None


@pytest.mark.asyncio
async def test_read_file_lit_un_vrai_pdf_indexe_sans_fournisseur(
    db_session: AsyncSession, tmp_path: Path,
) -> None:
    chemin = _pdf(
        tmp_path / "piece-indexee.pdf",
        [["Preuve synthétique : première page, 123,45 EUR."],
         ["Échéance négociée : deuxième page, 678,90 EUR."]],
    )
    identifiant = await _indexer_metadonnee(db_session, chemin)

    brut = await execute_memory_tool("read_file", {"file_id": identifiant}, db_session)
    resultat = _contenu_enveloppe(brut)

    assert resultat["found"] is True
    assert resultat["id"] == identifiant
    assert resultat["nom"] == chemin.name
    assert resultat["chemin"] == chemin.name
    assert "première page, 123,45 EUR." in resultat["contenu"]
    assert "Échéance négociée : deuxième page, 678,90 EUR." in resultat["contenu"]
    assert resultat["contenu"].index("première") < resultat["contenu"].index("deuxième")
    assert resultat["tronque"] is False


@pytest.mark.asyncio
async def test_read_file_signale_la_coupe_d_un_vrai_pdf_long(
    db_session: AsyncSession, tmp_path: Path,
) -> None:
    pages = [
        [f"Ligne {page}-{ligne} : échéance réglée 123,45 EUR. "
         + "Document synthétique B1767. " * 2 for ligne in range(35)]
        for page in range(4)
    ]
    pages[0][0] = "DEBUT_TRANSMIS_1767 " + pages[0][0]
    pages[-1].append("FIN_NON_TRANSMISE_1767")
    chemin = _pdf(tmp_path / "piece-longue.pdf", pages)
    texte_complet = extract_text(chemin)
    assert texte_complet is not None
    assert len(texte_complet) > 10_000
    assert "FIN_NON_TRANSMISE_1767" in texte_complet
    identifiant = await _indexer_metadonnee(db_session, chemin)

    brut = await execute_memory_tool("read_file", {"file_id": identifiant}, db_session)
    resultat = _contenu_enveloppe(brut)

    assert resultat["found"] is True
    assert resultat["tronque"] is True
    assert "DEBUT_TRANSMIS_1767" in resultat["contenu"]
    assert "FIN_NON_TRANSMISE_1767" not in resultat["contenu"]


@pytest.mark.asyncio
async def test_read_file_ne_lit_pas_le_pdf_d_un_autre_projet(
    db_session: AsyncSession, tmp_path: Path,
) -> None:
    chemin = _pdf(tmp_path / "autre-projet.pdf", [["CONTENU_HORS_PERIMETRE_1767"]])
    identifiant = await _indexer_metadonnee(
        db_session, chemin, scope="project", scope_id="projet-b1767-prive",
    )

    brut = await execute_memory_tool(
        "read_file", {"file_id": identifiant}, db_session,
        scope="project", scope_id="autre-projet-b1767",
    )
    resultat = json.loads(brut)

    assert resultat["found"] is False
    assert "CONTENU_HORS_PERIMETRE_1767" not in brut
    assert chemin.name not in brut
