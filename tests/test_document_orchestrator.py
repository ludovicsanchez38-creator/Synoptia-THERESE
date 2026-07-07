"""
Tests des fonctions pures de l'orchestrateur documentaire (Lot B, tâche B1).

Aucun appel LLM, aucune base de données : uniquement construction de prompts
et parsing de réponses, avec des entités `Document`/`DocumentSection`
construites directement en mémoire (SQLModel s'instancie sans DB).
"""

import json

import pytest
from app.models.entities import Document, DocumentSection
from app.services.document_orchestrator import (
    build_outline_prompt,
    build_section_context,
    build_summary_prompt,
    parse_draft_output,
    parse_outline_response,
)

# =============================================================================
# build_outline_prompt
# =============================================================================


class TestBuildOutlinePrompt:
    def test_contient_titre_et_brief(self):
        prompt = build_outline_prompt(
            "Guide financement PME", "Aider les dirigeants à structurer leur dossier."
        )
        assert "Guide financement PME" in prompt
        assert "Aider les dirigeants à structurer leur dossier." in prompt

    def test_demande_un_tableau_json_avec_les_bonnes_cles(self):
        prompt = build_outline_prompt("Titre", "Besoin")
        assert "JSON" in prompt
        assert '"title"' in prompt
        assert '"brief"' in prompt
        assert '"depth"' in prompt

    def test_prompt_en_francais(self):
        prompt = build_outline_prompt("Titre", "Besoin")
        assert "trame" in prompt.lower()


# =============================================================================
# parse_outline_response
# =============================================================================


class TestParseOutlineResponse:
    def test_json_pur(self):
        raw = json.dumps(
            [{"title": "Introduction", "brief": "Présenter le sujet", "depth": 0}]
        )
        result = parse_outline_response(raw)
        assert result == [
            {"title": "Introduction", "brief": "Présenter le sujet", "depth": 0}
        ]

    def test_json_avec_fence_json(self):
        raw = (
            "```json\n"
            '[{"title": "Introduction", "brief": "Présenter", "depth": 0}]\n'
            "```"
        )
        result = parse_outline_response(raw)
        assert result[0]["title"] == "Introduction"
        assert result[0]["depth"] == 0

    def test_json_avec_fence_sans_langage(self):
        raw = (
            "```\n"
            '[{"title": "Introduction", "brief": "Présenter", "depth": 0}]\n'
            "```"
        )
        result = parse_outline_response(raw)
        assert result[0]["title"] == "Introduction"

    def test_json_avec_texte_autour_de_la_fence(self):
        raw = (
            "Voici la trame proposée :\n\n"
            "```json\n"
            '[{"title": "Introduction", "brief": "Présenter", "depth": 0}]\n'
            "```\n"
            "J'espère que cela convient."
        )
        result = parse_outline_response(raw)
        assert result[0]["title"] == "Introduction"

    def test_plusieurs_sections_avec_profondeur(self):
        raw = json.dumps(
            [
                {"title": "Chapitre 1", "brief": "b1", "depth": 0},
                {"title": "Sous-partie 1.1", "brief": "b2", "depth": 1},
                {"title": "Chapitre 2", "brief": "b3", "depth": 0},
            ]
        )
        result = parse_outline_response(raw)
        assert len(result) == 3
        assert [item["depth"] for item in result] == [0, 1, 0]

    def test_texte_libre_leve_value_error(self):
        with pytest.raises(ValueError):
            parse_outline_response("Voici la trame : Introduction, puis Conclusion.")

    def test_json_objet_au_lieu_de_liste_leve_value_error(self):
        with pytest.raises(ValueError):
            parse_outline_response('{"title": "Introduction"}')

    def test_liste_vide_leve_value_error(self):
        with pytest.raises(ValueError):
            parse_outline_response("[]")

    def test_item_sans_titre_leve_value_error(self):
        with pytest.raises(ValueError):
            parse_outline_response(json.dumps([{"brief": "sans titre"}]))

    def test_message_erreur_en_francais_et_clair(self):
        with pytest.raises(ValueError, match="trame illisible"):
            parse_outline_response("pas du json du tout")

    def test_depth_manquant_defaut_zero(self):
        raw = json.dumps([{"title": "Intro", "brief": "b"}])
        result = parse_outline_response(raw)
        assert result[0]["depth"] == 0

    def test_item_non_objet_leve_value_error(self):
        raw = json.dumps(["juste une chaîne, pas un objet"])
        with pytest.raises(ValueError, match="trame illisible"):
            parse_outline_response(raw)

    def test_title_null_leve_value_error(self):
        """title: null ne doit JAMAIS devenir la chaîne « None »."""
        raw = json.dumps([{"title": None, "brief": "b", "depth": 0}])
        with pytest.raises(ValueError, match="trame illisible"):
            parse_outline_response(raw)

    def test_title_vide_leve_value_error(self):
        raw = json.dumps([{"title": "   ", "brief": "b", "depth": 0}])
        with pytest.raises(ValueError, match="trame illisible"):
            parse_outline_response(raw)

    def test_title_non_chaine_leve_value_error(self):
        raw = json.dumps([{"title": 42, "brief": "b", "depth": 0}])
        with pytest.raises(ValueError, match="trame illisible"):
            parse_outline_response(raw)

    def test_brief_null_devient_chaine_vide(self):
        """brief: null est toléré mais ne doit pas devenir la chaîne « None »."""
        raw = json.dumps([{"title": "Intro", "brief": None, "depth": 0}])
        result = parse_outline_response(raw)
        assert result[0]["brief"] == ""

    def test_depth_non_numerique_leve_value_error(self):
        raw = json.dumps([{"title": "Intro", "brief": "b", "depth": "abc"}])
        with pytest.raises(ValueError, match="trame illisible"):
            parse_outline_response(raw)


# =============================================================================
# build_section_context
# =============================================================================


class TestBuildSectionContext:
    def _document(self) -> Document:
        return Document(
            id="doc-1",
            title="Guide financement",
            brief="Aider les dirigeants de TPE à structurer un dossier de financement.",
        )

    def _sections(self) -> list[DocumentSection]:
        return [
            DocumentSection(
                id="s1",
                document_id="doc-1",
                title="Introduction",
                brief="Présenter le contexte du guide",
                order=10.0,
                depth=0,
                content="TEXTE INTEGRAL TRES LONG DE L INTRODUCTION, page après page.",
                summary="L'introduction pose le contexte du financement des TPE.",
                status="validee",
            ),
            DocumentSection(
                id="s2",
                document_id="doc-1",
                title="Financement bancaire",
                brief="Détailler les prêts bancaires classiques",
                order=20.0,
                depth=0,
                content="",
                summary="",
                status="vide",
            ),
            DocumentSection(
                id="s3",
                document_id="doc-1",
                title="Aides publiques",
                brief="Lister les aides publiques mobilisables",
                order=30.0,
                depth=0,
                content="CONTENU INTEGRAL NON VALIDE d'aides publiques, brouillon en cours.",
                summary="",
                status="brouillon",
            ),
        ]

    def test_contient_le_brief_du_document(self):
        document = self._document()
        sections = self._sections()
        ctx = build_section_context(document, sections, sections[1])
        assert document.brief in ctx

    def test_contient_la_trame_complete_titres_et_consignes(self):
        document = self._document()
        sections = self._sections()
        ctx = build_section_context(document, sections, sections[1])
        for section in sections:
            assert section.title in ctx
            assert section.brief in ctx

    def test_contient_le_resume_des_sections_validees(self):
        document = self._document()
        sections = self._sections()
        ctx = build_section_context(document, sections, sections[1])
        assert "L'introduction pose le contexte du financement des TPE." in ctx

    def test_ne_contient_pas_le_contenu_integral_des_autres_sections(self):
        document = self._document()
        sections = self._sections()
        ctx = build_section_context(document, sections, sections[1])
        assert "TEXTE INTEGRAL TRES LONG DE L INTRODUCTION" not in ctx
        assert "CONTENU INTEGRAL NON VALIDE" not in ctx

    def test_contient_la_consigne_de_la_section_cible(self):
        document = self._document()
        sections = self._sections()
        target = sections[1]
        ctx = build_section_context(document, sections, target)
        assert target.brief in ctx
        assert target.title in ctx

    def test_sans_instruction_pas_de_bloc_retouche(self):
        document = self._document()
        sections = self._sections()
        ctx = build_section_context(document, sections, sections[1])
        assert "RETOUCHE" not in ctx.upper()

    def test_instruction_incluse_quand_fournie(self):
        document = self._document()
        sections = self._sections()
        ctx = build_section_context(
            document,
            sections,
            sections[1],
            instruction="Raccourcis le texte et ajoute un exemple chiffré.",
        )
        assert "Raccourcis le texte et ajoute un exemple chiffré." in ctx

    def test_explique_le_bloc_pistes_optionnel(self):
        document = self._document()
        sections = self._sections()
        ctx = build_section_context(document, sections, sections[1])
        assert "PISTES:" in ctx
        assert "- " in ctx

    def test_sans_section_validee_pas_de_bloc_resumes(self):
        document = self._document()
        sections = [s for s in self._sections() if s.status != "validee"]
        ctx = build_section_context(document, sections, sections[0])
        assert "RÉSUMÉS DES SECTIONS DÉJÀ VALIDÉES" not in ctx

    def test_section_cible_validee_pas_dans_les_resumes(self):
        """Retoucher une section déjà validée : son propre résumé ne doit
        pas apparaître dans la liste des sections validées (la cible est
        exclue du bloc de résumés, et il n'est émis nulle part ailleurs)."""
        document = self._document()
        sections = self._sections()
        target = sections[0]  # déjà "validee"
        ctx = build_section_context(document, sections, target)
        assert ctx.count("L'introduction pose le contexte du financement des TPE.") == 0


# =============================================================================
# build_section_context - amendement retouche (tâche B3)
# =============================================================================


class TestBuildSectionContextRetouche:
    """Cas « Retoucher » : quand une instruction est fournie ET que la
    section cible a déjà du contenu, ce contenu doit entrer dans le contexte
    (bloc dédié) pour qu'une instruction comme « raccourcis le 2e paragraphe »
    ait un sens. Les autres sections restent résumées uniquement."""

    def _document(self) -> Document:
        return Document(id="doc-1", title="Guide financement", brief="Brief du besoin.")

    def test_retouche_avec_contenu_existant_inclut_le_contenu_actuel(self):
        document = self._document()
        target = DocumentSection(
            id="s1",
            document_id="doc-1",
            title="Financement bancaire",
            brief="Détailler les prêts bancaires classiques",
            order=10.0,
            depth=0,
            content="Voici le paragraphe déjà rédigé sur les prêts bancaires.",
            status="brouillon",
        )
        ctx = build_section_context(
            document, [target], target, instruction="Raccourcis le 2e paragraphe."
        )
        assert "CONTENU ACTUEL DE LA SECTION" in ctx
        assert "Voici le paragraphe déjà rédigé sur les prêts bancaires." in ctx

    def test_sans_contenu_existant_pas_de_bloc_contenu_actuel_meme_avec_instruction(self):
        document = self._document()
        target = DocumentSection(
            id="s1",
            document_id="doc-1",
            title="Financement bancaire",
            brief="Détailler les prêts bancaires classiques",
            order=10.0,
            depth=0,
            content="",
            status="vide",
        )
        ctx = build_section_context(
            document, [target], target, instruction="Commence par une accroche chiffrée."
        )
        assert "CONTENU ACTUEL DE LA SECTION" not in ctx

    def test_autres_sections_gardent_uniquement_leur_resume_meme_en_retouche(self):
        """Le mode retouche ajoute le contenu de la CIBLE seulement - les
        autres sections restent résumées (pas de fuite de contenu intégral)."""
        document = self._document()
        other = DocumentSection(
            id="s0",
            document_id="doc-1",
            title="Introduction",
            brief="Poser le contexte",
            order=5.0,
            depth=0,
            content="TEXTE INTEGRAL DE L'INTRODUCTION, très long.",
            summary="Résumé de l'introduction.",
            status="validee",
        )
        target = DocumentSection(
            id="s1",
            document_id="doc-1",
            title="Financement bancaire",
            brief="Détailler les prêts bancaires classiques",
            order=10.0,
            depth=0,
            content="Contenu actuel de la section cible.",
            status="brouillon",
        )
        ctx = build_section_context(
            document, [other, target], target, instruction="Retouche ce paragraphe."
        )
        assert "TEXTE INTEGRAL DE L'INTRODUCTION" not in ctx
        assert "Résumé de l'introduction." in ctx
        assert "Contenu actuel de la section cible." in ctx


# =============================================================================
# build_summary_prompt
# =============================================================================


class TestBuildSummaryPrompt:
    def test_contient_titre_et_contenu_de_la_section(self):
        section = DocumentSection(
            id="s1",
            document_id="doc-1",
            title="Financement bancaire",
            content="Un long contenu rédigé sur les prêts bancaires classiques.",
        )
        prompt = build_summary_prompt(section)
        assert "Financement bancaire" in prompt
        assert "Un long contenu rédigé sur les prêts bancaires classiques." in prompt

    def test_demande_environ_150_mots(self):
        section = DocumentSection(
            id="s1", document_id="doc-1", title="Titre", content="Contenu."
        )
        prompt = build_summary_prompt(section)
        assert "150" in prompt


# =============================================================================
# parse_draft_output
# =============================================================================


class TestParseDraftOutput:
    def test_sans_bloc_pistes(self):
        raw = "## Financement bancaire\n\nLes prêts bancaires classiques..."
        content, pistes = parse_draft_output(raw)
        assert content == raw.strip()
        assert pistes == []

    def test_avec_bloc_pistes(self):
        raw = (
            "## Financement bancaire\n\n"
            "Les prêts bancaires classiques restent la voie la plus utilisée.\n\n"
            "PISTES:\n"
            "- Développer un exemple chiffré sur le crédit-bail\n"
            "- Comparer avec le financement participatif\n"
        )
        content, pistes = parse_draft_output(raw)
        assert content == (
            "## Financement bancaire\n\n"
            "Les prêts bancaires classiques restent la voie la plus utilisée."
        )
        assert pistes == [
            "Développer un exemple chiffré sur le crédit-bail",
            "Comparer avec le financement participatif",
        ]

    def test_bloc_pistes_avec_espace_avant_deux_points(self):
        raw = "Contenu de la section.\n\nPISTES :\n- Une seule piste ici\n"
        content, pistes = parse_draft_output(raw)
        assert content == "Contenu de la section."
        assert pistes == ["Une seule piste ici"]

    def test_bloc_pistes_vide_retourne_liste_vide(self):
        raw = "Contenu de la section.\n\nPISTES:\n"
        content, pistes = parse_draft_output(raw)
        assert content == "Contenu de la section."
        assert pistes == []

    def test_marqueur_pistes_minuscule_nest_plus_reconnu_comme_marqueur(self):
        """Durci (revue adversariale lot B, finding 2) : le marqueur est
        désormais STRICTEMENT sensible à la casse - une ligne « pistes: »
        en minuscule n'est plus prise pour le sentinelle, elle reste du
        contenu tel quel (l'ancien comportement insensible à la casse
        verrouillait le bug : « Pistes : » est un mot courant en français
        qui tronquait du contenu réel)."""
        raw = "Contenu.\n\npistes:\n- Une piste\n"
        content, pistes = parse_draft_output(raw)
        assert content == raw.strip()
        assert pistes == []

    def test_ligne_pistes_en_plein_texte_reste_du_contenu(self):
        """Repro confirmée (finding 2) : « Pistes : » au milieu d'une
        section rédigée (mot courant en français, casse mixte) ne doit
        JAMAIS être pris pour le marqueur - le contenu entier est
        conservé, aucune piste créée."""
        raw = (
            "Le budget prévisionnel doit couvrir plusieurs volets.\n\n"
            "Pistes : financement bancaire, aides publiques, apport personnel.\n\n"
            "Cette section se termine ici."
        )
        content, pistes = parse_draft_output(raw)
        assert content == raw.strip()
        assert pistes == []

    def test_bloc_pistes_final_apres_une_ligne_pistes_mi_texte(self):
        """Une ligne « Pistes : » mi-texte (mot courant, casse mixte) suivie
        PLUS LOIN d'un vrai bloc `PISTES:` final (majuscules strictes) :
        seul le bloc final doit être découpé, la ligne mi-texte reste dans
        le contenu (le marqueur le plus tardif ET valide gagne)."""
        raw = (
            "Introduction du sujet.\n\n"
            "Pistes : plusieurs options existent pour financer ce projet.\n\n"
            "Développement du propos jusqu'à la fin de la section.\n\n"
            "PISTES:\n"
            "- Comparer avec le crédit-bail\n"
        )
        content, pistes = parse_draft_output(raw)
        assert content == (
            "Introduction du sujet.\n\n"
            "Pistes : plusieurs options existent pour financer ce projet.\n\n"
            "Développement du propos jusqu'à la fin de la section."
        )
        assert pistes == ["Comparer avec le crédit-bail"]

    def test_contenu_vide_avec_seulement_des_pistes(self):
        raw = "PISTES:\n- Piste unique\n"
        content, pistes = parse_draft_output(raw)
        assert content == ""
        assert pistes == ["Piste unique"]

    def test_piste_sans_prefixe_tiret_toleree(self):
        """Tolérance volontaire : une ligne de piste sans le préfixe « - »
        est quand même capturée (les LLM oublient parfois le tiret)."""
        raw = (
            "Contenu de la section.\n\n"
            "PISTES:\n"
            "- Piste avec tiret\n"
            "Piste sans tiret\n"
        )
        content, pistes = parse_draft_output(raw)
        assert content == "Contenu de la section."
        assert pistes == ["Piste avec tiret", "Piste sans tiret"]
