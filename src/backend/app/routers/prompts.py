"""
THERESE - Bibliotheque de prompts prets a l'emploi

API /api/prompts - Acces a la bibliotheque de prompts classes par categorie.
"""

from __future__ import annotations

import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)
router = APIRouter()

# Chargement des donnees au demarrage du module
# PyInstaller : __file__ pointe vers _MEIPASS, on adapte le chemin
if hasattr(sys, "_MEIPASS"):
    _LIBRARY_PATH = Path(sys._MEIPASS) / "app" / "data" / "prompt_library.json"
else:
    _LIBRARY_PATH = Path(__file__).resolve().parent.parent / "data" / "prompt_library.json"
_prompts: list[dict[str, Any]] = []
_categories_order = ["email", "commercial", "admin", "redaction", "organisation", "juridique"]
_categories_labels: dict[str, str] = {
    "email": "Email",
    "commercial": "Commercial",
    "admin": "Admin / Compta",
    "redaction": "R\u00e9daction",
    "organisation": "Organisation",
    "juridique": "Juridique",
}


def _load_library() -> list[dict[str, Any]]:
    """Charge la bibliotheque depuis le fichier JSON."""
    global _prompts
    if _prompts:
        return _prompts
    try:
        with open(_LIBRARY_PATH, encoding="utf-8") as f:
            _prompts = json.load(f)
        logger.info("Biblioth\u00e8que de prompts charg\u00e9e : %d prompts", len(_prompts))
    except FileNotFoundError:
        logger.warning("Fichier prompt_library.json introuvable : %s", _LIBRARY_PATH)
        _prompts = []
    except json.JSONDecodeError as e:
        logger.error("Erreur de parsing prompt_library.json : %s", e)
        _prompts = []
    return _prompts


def _group_by_category(
    prompts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Regroupe les prompts par categorie, dans l'ordre defini."""
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in prompts:
        groups[p.get("category", "autre")].append(p)

    result = []
    for cat in _categories_order:
        if cat in groups:
            result.append(
                {
                    "category": cat,
                    "label": _categories_labels.get(cat, cat.capitalize()),
                    "prompts": groups[cat],
                }
            )

    # Categories non prevues (securite)
    for cat, items in groups.items():
        if cat not in _categories_order:
            result.append(
                {
                    "category": cat,
                    "label": cat.capitalize(),
                    "prompts": items,
                }
            )

    return result


@router.get("/library")
async def get_prompt_library() -> dict[str, Any]:
    """Retourne la bibliotheque complete groupee par categorie."""
    prompts = _load_library()
    return {
        "total": len(prompts),
        "categories": _group_by_category(prompts),
    }


@router.get("/library/search")
async def search_prompts(
    q: str = Query(..., min_length=1, description="Terme de recherche"),
) -> dict[str, Any]:
    """Recherche dans la bibliotheque par mots-cles (titre, description, tags)."""
    prompts = _load_library()
    query = q.lower().strip()
    terms = query.split()

    results: list[dict[str, Any]] = []
    for p in prompts:
        searchable = " ".join(
            [
                p.get("title", ""),
                p.get("description", ""),
                " ".join(p.get("tags", [])),
                p.get("category", ""),
            ]
        ).lower()

        if all(term in searchable for term in terms):
            results.append(p)

    return {
        "query": q,
        "total": len(results),
        "categories": _group_by_category(results),
    }
