"""Vérité d'exécution (Chantier A - revue produit).

Deux helpers PURS (sans I/O) pour que l'IA ne mente jamais sur ce qu'elle fait :

- `enforce_create_cap` : plafonne le nombre de créations d'entités exécutées dans un tour,
  en complément de la déduplication par nom (memory_tools) et du plafond de 5 itérations.
  Défense contre une rafale de créations de noms *différents* hallucinés par le LLM.

- `summarize_executions` : produit un résumé DÉTERMINISTE de ce qui a réellement été
  créé / réutilisé / échoué, à partir des résultats d'outils — indépendant de la prose
  du LLM, pour que l'utilisateur voie toujours l'état réel.
"""

from __future__ import annotations

import json
from typing import Any, Iterable

_CREATE_TOOLS = ("create_contact", "create_project")
DEFAULT_CREATE_CAP = 10


def enforce_create_cap(tool_calls: list[Any], max_creates: int = DEFAULT_CREATE_CAP) -> tuple[list[Any], list[Any]]:
    """Sépare les tool calls en (autorisés, bloqués).

    Seules les créations d'entités (`create_contact`/`create_project`) au-delà de
    `max_creates` sont bloquées ; les autres outils passent toujours.
    """
    allowed: list[Any] = []
    blocked: list[Any] = []
    create_count = 0
    for call in tool_calls:
        if getattr(call, "name", None) in _CREATE_TOOLS:
            create_count += 1
            if create_count > max_creates:
                blocked.append(call)
                continue
        allowed.append(call)
    return allowed, blocked


def summarize_executions(results: Iterable[tuple[str, str, bool]]) -> str | None:
    """Résumé déterministe des créations réelles.

    `results` : itérable de (tool_name, result_str, is_error). Retourne une phrase de
    récap ("Récap réel : ...") s'il y a eu au moins une opération de création, sinon None.
    """
    contacts_created = contacts_reused = projects_created = projects_reused = failures = 0

    for name, result_str, is_error in results:
        if name not in _CREATE_TOOLS:
            continue
        is_contact = name == "create_contact"
        if is_error:
            failures += 1
            continue
        try:
            data: dict[str, Any] = json.loads(result_str)
        except (ValueError, TypeError):
            failures += 1
            continue
        if data.get("error"):
            failures += 1
        elif data.get("already_existed"):
            if is_contact:
                contacts_reused += 1
            else:
                projects_reused += 1
        elif data.get("success"):
            if is_contact:
                contacts_created += 1
            else:
                projects_created += 1
        else:
            failures += 1

    total = contacts_created + contacts_reused + projects_created + projects_reused + failures
    if total == 0:
        return None

    parts: list[str] = []
    if contacts_created:
        parts.append(f"{contacts_created} contact(s) créé(s)")
    if projects_created:
        parts.append(f"{projects_created} projet(s) créé(s)")
    reused = contacts_reused + projects_reused
    if reused:
        parts.append(f"{reused} déjà existant(s)")
    if failures:
        parts.append(f"{failures} échec(s)")
    return "Récap réel : " + ", ".join(parts) + "."
