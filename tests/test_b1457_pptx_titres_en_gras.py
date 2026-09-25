"""B-1457 (recette P-146, lot 3) : avec un modèle local, le repli PPTX
recevait des titres écrits en gras (« **Contexte** ») : il n'y voyait aucun
titre, tout partait dans une seule diapositive « Slide », tronquée à six
points. Un titre en gras, ou `###`, ouvre sa diapositive comme `#` et `##`."""

from pathlib import Path

from app.services.skills.pptx_generator import PptxSkill


def test_les_titres_en_gras_ouvrent_chacun_leur_diapositive(tmp_path: Path):
    skill = PptxSkill(output_dir=tmp_path)
    diapos = skill._parse_content(
        "**Contexte**\n- Atelier de menuiserie\n- Trois salariés\n\n"
        "**Offre :**\n- Agenda partagé\n- Relances\n\n"
        "### Calendrier\n- Octobre"
    )
    assert diapos == [
        {"title": "Contexte", "points": ["Atelier de menuiserie", "Trois salariés"]},
        {"title": "Offre", "points": ["Agenda partagé", "Relances"]},
        {"title": "Calendrier", "points": ["Octobre"]},
    ]


def test_les_titres_diese_restent_reconnus(tmp_path: Path):
    skill = PptxSkill(output_dir=tmp_path)
    diapos = skill._parse_content("## Contexte\n- A\n\n---\n\n## Planning\n- B")
    assert [d["title"] for d in diapos] == ["Contexte", "Planning"]
