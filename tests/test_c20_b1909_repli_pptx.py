"""Le repli produit un vrai PowerPoint sans balises Markdown visibles."""

import pytest
from app.services.skills.base import SkillParams
from app.services.skills.pptx_generator import PptxSkill
from pptx import Presentation


@pytest.mark.asyncio
async def test_repli_pptx_convertit_les_puces_markdown(tmp_path):
    skill = PptxSkill(tmp_path)
    resultat = await skill.execute(SkillParams(
        title="Présentation",
        content=("## Bilan\n"
                 "- Voici un **élément clé** à retenir.\n"
                 "- Une *priorité* et [une source](https://exemple.fr).\n"
                 "- Le calcul 2 * 3 reste lisible."),
    ))
    presentation = Presentation(resultat.file_path)
    paragraphes = [p for shape in presentation.slides[1].shapes if shape.has_text_frame
                   for p in shape.text_frame.paragraphs]
    textes = [p.text.strip() for p in paragraphes]
    assert "Voici un élément clé à retenir." in textes
    assert "Une priorité et une source." in textes
    assert "Le calcul 2 * 3 reste lisible." in textes
    assert any(run.text == "élément clé" and run.font.bold for p in paragraphes for run in p.runs)
    assert any(run.text == "priorité" and run.font.italic for p in paragraphes for run in p.runs)
    assert any(run.text == "une source" and run.hyperlink.address == "https://exemple.fr"
               for p in paragraphes for run in p.runs)
