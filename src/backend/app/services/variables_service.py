"""
THÉRÈSE v2 - Variables utilisateur (chantier 4 V1, design V4 du 11/07/2026).

Mémoire de travail bornée, co-designée avec Dr_logic : une variable est SOIT
une valeur texte (enrichie par concaténation), SOIT une liste de valeurs
(enrichie par ajout). Point de validation UNIQUE pour l'API et les actions du
chat. Sémantique anti-destruction (finding Codex 6) : `create` refuse
d'écraser, `replace` est le verbe explicite. Les valeurs entrantes passent
par check_prompt_safety (finding 4 : une valeur stockée est rejouée vers le
LLM sans nouveau contrôle - le contrôle se fait donc à l'entrée). PAS un
coffre à secrets : les valeurs partent au LLM à l'usage.
"""

import json
import re
from datetime import UTC, datetime

from app.models.entities import Variable
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

MAX_VARIABLES = 100
MAX_TEXT_LENGTH = 4000
MAX_LIST_ITEMS = 100
MAX_LIST_ITEM_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 200
RESERVED_NAMES = frozenset({"action", "aide", "variable", "variables"})
_NAME_RE = re.compile(r"[a-z0-9_]{1,32}\Z")

VALID_KINDS = ("text", "list")


class VariableError(ValueError):
    """Erreur métier : le message est destiné à l'utilisateur (chat ou API)."""


def validate_name(name: str) -> None:
    if not _NAME_RE.fullmatch(name):
        raise VariableError(
            f"Nom de variable invalide : « {name[:40]} ». Attendu : minuscules, "
            "chiffres et _ (32 caractères maximum)."
        )
    if name in RESERVED_NAMES:
        raise VariableError(f"« {name} » est un mot réservé.")


def _validate_fragment(fragment: str, limit: int, label: str) -> None:
    if not isinstance(fragment, str) or not fragment.strip():
        raise VariableError(f"{label} ne peut pas être vide.")
    if len(fragment) > limit:
        raise VariableError(f"{label} dépasse la limite de {limit} caractères.")
    # Finding 4 : contrôle sécurité à l'ENTRÉE (la valeur sera rejouée au LLM
    # dans de futurs tours sans repasser par le filtre).
    from app.services.prompt_security import check_prompt_safety

    if not check_prompt_safety(fragment).is_safe:
        raise VariableError(f"{label} est bloquée pour raison de sécurité.")


def validate_value(kind: str, value: str | list[str]) -> None:
    if kind not in VALID_KINDS:
        raise VariableError("Type de variable invalide (attendu : text ou list).")
    if kind == "text":
        if not isinstance(value, str):
            raise VariableError("Une variable texte attend une valeur texte.")
        _validate_fragment(value, MAX_TEXT_LENGTH, "La valeur")
    else:
        if not isinstance(value, list) or any(
            not isinstance(item, str) for item in value
        ):
            raise VariableError("Une variable liste attend une liste de textes.")
        if len(value) > MAX_LIST_ITEMS:
            raise VariableError(
                f"La liste dépasse la limite de {MAX_LIST_ITEMS} éléments."
            )
        for item in value:
            _validate_fragment(item, MAX_LIST_ITEM_LENGTH, "Un élément")


def _validate_description(description: str | None) -> None:
    if description is not None and len(description) > MAX_DESCRIPTION_LENGTH:
        raise VariableError(
            f"La description dépasse {MAX_DESCRIPTION_LENGTH} caractères."
        )


async def list_variables(session: AsyncSession) -> list[Variable]:
    result = await session.execute(select(Variable).order_by(Variable.name))
    return list(result.scalars().all())


async def get_variable(session: AsyncSession, name: str) -> Variable | None:
    result = await session.execute(select(Variable).where(Variable.name == name))
    return result.scalars().first()


async def create_variable(
    session: AsyncSession,
    name: str,
    kind: str,
    value: str | list[str],
    description: str | None = None,
) -> Variable:
    validate_name(name)
    # Liste vide autorisée à la création ({action: variable creer courses liste})
    if not (kind == "list" and value == []):
        validate_value(kind, value)
    elif kind not in VALID_KINDS:  # pragma: no cover - garde de cohérence
        raise VariableError("Type de variable invalide.")
    _validate_description(description)

    if await get_variable(session, name) is not None:
        raise VariableError(
            f"La variable « {name} » existe déjà. Utilise « remplacer » pour "
            "changer sa valeur (l'écrasement silencieux est refusé)."
        )
    count = len(await list_variables(session))
    if count >= MAX_VARIABLES:
        raise VariableError(
            f"Nombre maximum de variables atteint ({MAX_VARIABLES})."
        )
    variable = Variable(
        name=name, kind=kind, value=json.dumps(value, ensure_ascii=False),
        description=description,
    )
    session.add(variable)
    await session.commit()
    await session.refresh(variable)
    return variable


async def replace_variable(
    session: AsyncSession, name: str, value: str | list[str]
) -> Variable:
    variable = await get_variable(session, name)
    if variable is None:
        raise VariableError(f"La variable « {name} » n'existe pas.")
    validate_value(variable.kind, value)
    variable.value = json.dumps(value, ensure_ascii=False)
    variable.updated_at = datetime.now(UTC)
    session.add(variable)
    await session.commit()
    await session.refresh(variable)
    return variable


async def append_to_variable(
    session: AsyncSession, name: str, fragment: str
) -> Variable:
    """Concaténation (texte, avec espace) ou ajout d'élément (liste)."""
    variable = await get_variable(session, name)
    if variable is None:
        raise VariableError(f"La variable « {name} » n'existe pas.")
    current = variable.parsed_value
    if variable.kind == "text":
        assert isinstance(current, str)
        new_value: str | list[str] = f"{current} {fragment}".strip()
    else:
        assert isinstance(current, list)
        new_value = [*current, fragment]
    validate_value(variable.kind, new_value)
    variable.value = json.dumps(new_value, ensure_ascii=False)
    variable.updated_at = datetime.now(UTC)
    session.add(variable)
    await session.commit()
    await session.refresh(variable)
    return variable


async def delete_variable(session: AsyncSession, name: str) -> None:
    variable = await get_variable(session, name)
    if variable is None:
        raise VariableError(f"La variable « {name} » n'existe pas.")
    await session.delete(variable)
    await session.commit()
