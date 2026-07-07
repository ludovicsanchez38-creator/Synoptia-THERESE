"""
THÉRÈSE v2 - Orchestrateur documentaire (fonctions pures)

Construit les prompts et parse les réponses LLM de l'atelier documentaire
(lot B du design du 07/07/2026). Aucun appel LLM ni accès base de données
ici - uniquement de la construction de texte et du parsing, testable avec
de simples objets `Document`/`DocumentSection` en mémoire.

Le point central est `build_section_context` : il fournit au LLM le brief
du document, la trame complète (titres + consignes), les RÉSUMÉS des
sections déjà validées (jamais leur texte intégral - c'est le levier qui
garde le coût constant même sur un document de 50 pages) et la consigne de
la section à rédiger. Le prompt qu'il construit explique aussi le bloc
optionnel `PISTES:` (une idée par ligne, préfixe `- `) que
`parse_draft_output` sait ensuite extraire de la réponse.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.entities import Document, DocumentSection


# =============================================================================
# Génération de trame (outline)
# =============================================================================


def build_outline_prompt(title: str, brief: str) -> str:
    """Construit le prompt qui demande au LLM la trame d'un document."""
    return (
        "Tu es un assistant qui construit la trame (plan détaillé) d'un "
        "document long en français, pour un solopreneur ou une TPE.\n\n"
        f"Titre du document : {title}\n"
        f"Besoin exprimé par l'utilisateur : {brief}\n\n"
        "Propose une trame hiérarchique claire qui couvre ce besoin de bout "
        "en bout (sections principales et, si utile, sous-sections). Pour "
        "chaque élément de la trame, donne :\n"
        "- title : un titre concis\n"
        "- brief : une consigne d'une ligne (ce que la section doit couvrir)\n"
        "- depth : 0 pour une section principale, 1 pour une sous-section\n\n"
        "Réponds UNIQUEMENT avec un tableau JSON, sans texte avant ni après "
        "et sans commentaire, au format exact :\n"
        '[{"title": "...", "brief": "...", "depth": 0}, '
        '{"title": "...", "brief": "...", "depth": 1}]'
    )


_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.IGNORECASE | re.DOTALL)


def _strip_code_fence(raw: str) -> str:
    """Retire un éventuel bloc de code ```json ... ``` (ou ``` ... ```)
    autour (ou dans) la réponse, tolère du texte parasite avant/après."""
    match = _FENCE_RE.search(raw)
    if match:
        return match.group(1).strip()
    return raw.strip()


def parse_outline_response(raw: str) -> list[dict[str, str | int]]:
    """Parse la réponse LLM d'une trame (JSON attendu, tolérant aux fences
    ```json). Lève `ValueError` avec un message clair en français si la
    réponse n'est pas exploitable - le router la transforme en 502
    « trame illisible, réessaie »."""
    text = _strip_code_fence(raw)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "trame illisible : la réponse du modèle n'est pas du JSON valide"
        ) from exc

    if not isinstance(data, list):
        raise ValueError(
            "trame illisible : un tableau JSON de sections était attendu"
        )

    if not data:
        raise ValueError("trame illisible : aucune section trouvée dans la réponse")

    sections: list[dict[str, str | int]] = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError(
                "trame illisible : chaque section doit être un objet JSON"
            )
        title = item.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(
                "trame illisible : chaque section doit contenir un titre non vide"
            )
        # brief null ou absent = toléré (chaîne vide), mais jamais « None ».
        brief = item.get("brief")
        brief_text = brief.strip() if isinstance(brief, str) else ""
        try:
            depth = int(item.get("depth") or 0)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "trame illisible : la profondeur d'une section doit être un nombre"
            ) from exc
        sections.append(
            {
                "title": title.strip(),
                "brief": brief_text,
                "depth": depth,
            }
        )

    return sections


# =============================================================================
# Contexte de rédaction d'une section
# =============================================================================


def build_section_context(
    document: "Document",
    sections: list["DocumentSection"],
    target: "DocumentSection",
    instruction: str | None = None,
) -> str:
    """Construit le prompt de rédaction d'UNE section du document.

    Contient, dans l'ordre : le brief du document, la trame complète
    (titres + consignes de toutes les sections, triées par `order`), les
    RÉSUMÉS des sections déjà validées (jamais leur texte intégral - budget
    de tokens maîtrisé), la consigne de la section cible, et l'instruction
    de retouche éventuelle. Se termine en expliquant le bloc final optionnel
    `PISTES:` que `parse_draft_output` sait extraire.
    """
    parts: list[str] = [
        f"Tu rédiges une section du document « {document.title} », destiné "
        "à un solopreneur ou une TPE française. Réponds en français, dans "
        "un style clair et professionnel, en markdown.",
        "",
        "BESOIN GLOBAL DU DOCUMENT :",
        document.brief or "(non précisé)",
        "",
        "TRAME COMPLÈTE DU DOCUMENT (titres et consignes de chaque section) :",
    ]

    for section in sections:
        indent = "  " * section.depth
        marker = " <- SECTION À RÉDIGER MAINTENANT" if section.id == target.id else ""
        parts.append(f"{indent}- {section.title} : {section.brief}{marker}")
    parts.append("")

    validated = [
        section
        for section in sections
        if section.status == "validee" and section.id != target.id
    ]
    if validated:
        parts.append(
            "RÉSUMÉS DES SECTIONS DÉJÀ VALIDÉES (pour rester cohérent avec "
            "elles, PAS leur texte intégral) :"
        )
        for section in validated:
            resume = section.summary or "(résumé non disponible)"
            parts.append(f"- {section.title} : {resume}")
        parts.append("")

    parts.extend(
        [
            "SECTION À RÉDIGER MAINTENANT :",
            f"Titre : {target.title}",
            f"Consigne : {target.brief or '(aucune consigne particulière)'}",
            "",
        ]
    )

    if instruction:
        # Cas « Retoucher » : la cible a déjà du contenu -> on le donne au
        # LLM (bloc dédié, JAMAIS pour les autres sections) pour qu'une
        # instruction comme « raccourcis le 2e paragraphe » ait un sens.
        if target.content.strip():
            parts.extend(
                [
                    "CONTENU ACTUEL DE LA SECTION (à retoucher) :",
                    target.content,
                    "",
                ]
            )
        parts.extend(
            [
                "INSTRUCTION DE RETOUCHE DEMANDÉE PAR L'UTILISATEUR :",
                instruction,
                "",
            ]
        )

    parts.extend(
        [
            "FORMAT DE SORTIE ATTENDU :",
            "Rédige directement le contenu markdown de cette section, sans "
            "répéter son titre en tête (il est déjà affiché dans l'atelier). "
            "Ne rédige QUE cette section, jamais les autres sections de la "
            "trame.",
            "Si une idée te semble intéressante mais hors sujet pour cette "
            "section précise, ne l'intègre pas dans le texte : ajoute-la en "
            "toute fin de ta réponse, dans un bloc optionnel qui commence "
            "par la ligne exacte « PISTES: », suivie d'une idée par ligne "
            "préfixée par « - ». N'ajoute ce bloc que si tu as réellement "
            "une piste à proposer.",
            "Exemple de bloc pistes :",
            "PISTES:",
            "- Développer un exemple chiffré sur le financement participatif",
        ]
    )

    return "\n".join(parts)


# =============================================================================
# Résumé d'une section validée
# =============================================================================


def build_summary_prompt(section: "DocumentSection") -> str:
    """Construit le prompt qui demande le résumé (~150 mots) d'une section
    validée - c'est ce résumé qui nourrira le contexte des sections
    suivantes, jamais le texte intégral."""
    return (
        "Résume le contenu suivant en environ 150 mots, en français, sous "
        "la forme d'un paragraphe continu (pas de titre, pas de liste à "
        "puces). Ce résumé sert de contexte concis pour la rédaction des "
        "sections suivantes du même document, sans exposer le texte "
        "intégral.\n\n"
        f"Section « {section.title} » :\n\n{section.content}"
    )


# =============================================================================
# Parsing du brouillon rédigé
# =============================================================================

_PISTES_MARKER_RE = re.compile(r"^PISTES\s*:?\s*$")


def parse_draft_output(raw: str) -> tuple[str, list[str]]:
    """Sépare le contenu markdown rédigé des pistes annexes.

    Le prompt (`build_section_context`) demande un bloc final optionnel qui
    commence par la ligne exacte `PISTES:` (tolérant `PISTES :`), suivie
    d'une idée par ligne préfixée par `- `. Retourne
    `(contenu_sans_bloc, [pistes])` ; si aucun bloc n'est présent, retourne
    tout le texte tel quel et une liste de pistes vide.

    Le marqueur est STRICTEMENT sensible à la casse (revue adversariale lot
    B, finding 2) : une ligne de contenu « Pistes : » (mot courant en
    français, ex. « Pistes : financement bancaire, aides publiques... »)
    n'est JAMAIS prise pour le sentinelle - seule la ligne EXACTE `PISTES:`
    (majuscules, cohérent avec le prompt) déclenche la coupure. En
    complément, c'est le marqueur le plus TARDIF qui fait foi : si le texte
    contient plusieurs lignes qui matchent exactement `PISTES:` (cas
    limite), seul le DERNIER délimite le bloc de pistes - tout ce qui
    précède, y compris un candidat plus tôt dans le texte, reste du
    contenu. Ça garantit que le bloc reconnu est bien en QUEUE de réponse :
    par construction, il n'y a plus aucune ligne après le marqueur choisi
    qui ressemble à un nouveau paragraphe suivi d'un autre marqueur -
    sinon ce serait ce marqueur-là qui aurait été retenu.
    """
    lines = raw.splitlines()

    marker_index: int | None = None
    for index, line in enumerate(lines):
        if _PISTES_MARKER_RE.match(line.strip()):
            marker_index = index  # pas de break : le dernier match gagne

    if marker_index is None:
        return raw.strip(), []

    content = "\n".join(lines[:marker_index]).strip()

    pistes: list[str] = []
    for line in lines[marker_index + 1 :]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("-"):
            piste = stripped[1:].strip()
        else:
            piste = stripped
        if piste:
            pistes.append(piste)

    return content, pistes
