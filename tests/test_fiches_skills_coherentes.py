"""B-291 : une fiche de skill ne doit pas annoncer une police que le générateur n'applique pas.

`skills_config/docx/SKILL.md` annonçait « Inter (corps) » alors que les trois
chemins du générateur imposent Calibri : la règle impérative envoyée au modèle,
le gabarit de code qui l'accompagne, et le repli déterministe `_setup_styles`.
Un lecteur qui se fie à la fiche décrit au client un document qui ne sortira
pas ainsi.

Aucun nom de police n'est écrit en dur ici : les deux côtés sont extraits, puis
comparés. Une fiche corrigée en même temps qu'un générateur changé reste donc
verte, une fiche laissée en arrière rougit.
"""

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
FICHES = RACINE / "src" / "backend" / "app" / "skills_config"
GENERATEURS = RACINE / "src" / "backend" / "app" / "services" / "skills"

_POLICE_CORPS_PARENTHESE = re.compile(
    r"\*\*Police\*\*\s*:\s*.*?([A-Z][A-Za-z0-9 ]*?)\s*\(corps\)"
)
_POLICE_CORPS_DEDIEE = re.compile(r"\*\*Police corps\*\*\s*:\s*([A-Z][A-Za-z0-9]*)")
_POLICE_APPLIQUEE = re.compile(r"font\.name\s*=\s*[\"']([^\"']+)[\"']")
_POLICE_FONT_OPENPYXL = re.compile(r"Font\(\s*name\s*=\s*[\"']([^\"']+)[\"']")


def _police_de_corps_annoncee(fiche: Path) -> str:
    """La police de corps que la fiche promet au lecteur."""
    texte = fiche.read_text(encoding="utf-8")
    for motif in (_POLICE_CORPS_PARENTHESE, _POLICE_CORPS_DEDIEE):
        trouve = motif.search(texte)
        if trouve:
            return trouve.group(1).strip()
    raise AssertionError(f"aucune police de corps annoncée dans {fiche}")


def _polices_appliquees(module: Path) -> set[str]:
    source = module.read_text(encoding="utf-8")
    return set(_POLICE_APPLIQUEE.findall(source)) | set(
        _POLICE_FONT_OPENPYXL.findall(source)
    )


class TestFicheDocx:
    """Le cas fiché : les TROIS chemins du générateur Word, mesurés séparément."""

    def test_le_repli_deterministe_applique_la_police_annoncee(self, tmp_path):
        from app.services.skills.docx_generator import DocxSkill
        from docx import Document

        document = Document()
        DocxSkill(tmp_path)._setup_styles(document)
        appliquee = document.styles["Normal"].font.name

        assert appliquee == _police_de_corps_annoncee(FICHES / "docx" / "SKILL.md")

    def test_la_regle_imperative_du_prompt_annonce_la_meme_police(self, tmp_path):
        from app.services.skills.docx_generator import DocxSkill

        prompt = DocxSkill(tmp_path).get_system_prompt_addition()
        trouve = re.search(
            r"\*\*Police\*\*\s*:\s*([A-Z][A-Za-z0-9]*)[^,\n]*pour le corps", prompt
        )
        assert trouve, "la règle impérative du prompt ne nomme plus de police de corps"

        assert trouve.group(1) == _police_de_corps_annoncee(FICHES / "docx" / "SKILL.md")

    def test_le_gabarit_de_code_du_prompt_annonce_la_meme_police(self, tmp_path):
        from app.services.skills.docx_generator import DocxSkill

        prompt = DocxSkill(tmp_path).get_system_prompt_addition()
        gabarit = re.search(
            r"style\.font\.name\s*=\s*[\"']([^\"']+)[\"']", prompt
        )
        assert gabarit, "le gabarit de code du prompt ne configure plus la police Normal"

        assert gabarit.group(1) == _police_de_corps_annoncee(FICHES / "docx" / "SKILL.md")


class TestLesAutresFiches:
    """Garde plus faible sur pptx et xlsx : la police annoncée doit au moins
    être une police que le générateur applique réellement quelque part.

    Ces deux générateurs posent la police par appel unitaire (paragraphe,
    cellule) sans style « Normal » lisible sans construire tout un document :
    la comparaison stricte du cas docx n'y est pas transposable telle quelle.
    """

    @pytest.mark.parametrize(
        ("fiche", "generateur"),
        [
            ("pptx", "pptx_generator.py"),
            ("xlsx", "xlsx_generator.py"),
        ],
    )
    def test_la_police_annoncee_est_appliquee(self, fiche, generateur):
        annoncee = _police_de_corps_annoncee(FICHES / fiche / "SKILL.md")
        appliquees = _polices_appliquees(GENERATEURS / generateur)

        assert appliquees, f"aucune police appliquée trouvée dans {generateur}"
        assert annoncee in appliquees, (
            f"{fiche}/SKILL.md annonce « {annoncee} », "
            f"le générateur applique {sorted(appliquees)}"
        )


class TestLInstrumentLitBienLesDeuxCotes:
    """Une extraction muette rendrait toutes les fiches conformes."""

    def test_les_trois_fiches_annoncent_une_police(self):
        polices = {
            nom: _police_de_corps_annoncee(FICHES / nom / "SKILL.md")
            for nom in ("docx", "pptx", "xlsx")
        }
        assert all(polices.values()), polices

    def test_le_generateur_docx_expose_bien_une_police(self, tmp_path):
        from app.services.skills.docx_generator import DocxSkill
        from docx import Document

        document = Document()
        DocxSkill(tmp_path)._setup_styles(document)
        assert document.styles["Normal"].font.name
