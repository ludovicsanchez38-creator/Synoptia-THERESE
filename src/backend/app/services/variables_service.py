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


def _format_valeur(variable: Variable) -> str:
    value = variable.parsed_value
    if variable.kind == "text":
        assert isinstance(value, str)
        return value
    assert isinstance(value, list)
    if not value:
        return "(liste vide)"
    return "\n".join(f"- {item}" for item in value)


def _resume(variable: Variable) -> str:
    value = variable.parsed_value
    if variable.kind == "text":
        assert isinstance(value, str)
        return f"texte, {len(value)} caractère{'s' if len(value) > 1 else ''}"
    assert isinstance(value, list)
    return f"liste, {len(value)} élément{'s' if len(value) > 1 else ''}"


async def execute_chat_variable_action(
    session: AsyncSession,
    op: str,
    name: str | None,
    value: str | None,
    is_list: bool,
    error_message: str | None = None,
) -> str:
    """Exécute un verbe variable du chat (tranche 2 V4) - réponse locale,
    zéro LLM. Toute VariableError devient le texte de la réponse."""
    try:
        if op == "erreur":
            return error_message or "Commande variable invalide."
        if op == "lister":
            variables = await list_variables(session)
            if not variables:
                return (
                    "Aucune variable. Crée-en une avec "
                    '{action: variable creer nom "valeur"}.'
                )
            lignes = [f"- {v.name} ({_resume(v)})" for v in variables]
            return "Variables :\n" + "\n".join(lignes)

        assert name is not None
        if op == "creer":
            if is_list:
                await create_variable(session, name, "list", [])
                return f"Variable « {name} » créée (liste vide)."
            assert value is not None
            await create_variable(session, name, "text", value)
            return f"Variable « {name} » créée (texte)."
        if op == "remplacer":
            existing = await get_variable(session, name)
            if existing is not None and existing.kind == "list":
                return (
                    f"« {name} » est une liste : remplacer ne s'applique qu'aux "
                    "variables texte. Supprime-la puis recrée-la si besoin."
                )
            assert value is not None
            await replace_variable(session, name, value)
            return f"Variable « {name} » remplacée."
        if op == "ajouter":
            assert value is not None
            variable = await append_to_variable(session, name, value)
            return f"Ajouté à « {name} » ({_resume(variable)})."
        if op == "supprimer":
            variable = await get_variable(session, name)
            if variable is None:
                raise VariableError(f"La variable « {name} » n'existe pas.")
            apercu = _format_valeur(variable).replace("\n", ", ")[:120]
            await delete_variable(session, name)
            return f"Variable « {name} » supprimée (elle valait : {apercu})."
        if op == "afficher":
            variable = await get_variable(session, name)
            if variable is None:
                raise VariableError(f"La variable « {name} » n'existe pas.")
            return f"{variable.name} ({_resume(variable)}) :\n{_format_valeur(variable)}"
        return "Commande variable inconnue."
    except VariableError as e:
        return str(e)


# --- Tranche 3 : substitution {nom} (design V4, findings 9/10) ---

MAX_TOKENS_PER_MESSAGE = 20
MAX_RESOLVED_LENGTH = 60_000
_TOKEN_RE = re.compile(r"\{([a-z0-9_]{1,32})\}")
_ESCAPE_RE = re.compile(r"\{\{([a-z0-9_]{1,32})\}\}")
_SENTINEL = "\x00VAR\x00"
_SENTINEL_RE = re.compile("\x00VAR\x00([a-z0-9_]{1,32})\x00")


def resolve_text(
    text: str,
    variables: dict[str, str | list[str]],
    list_mode: str = "inline",
) -> tuple[str, list[str]]:
    """Substitution single-pass : les valeurs ne sont JAMAIS re-scannées
    (ni tokens, ni actions, ni directives - l'ordre des parseurs de
    send_message garantit le reste). `{{nom}}` = littéral `{nom}`.
    Inconnue = token laissé tel quel + signalé. Bornes : 20 tokens par
    message, 60 000 caractères résolus."""
    escaped = _ESCAPE_RE.sub(lambda m: f"{_SENTINEL}{m.group(1)}\x00", text)
    tokens = _TOKEN_RE.findall(escaped)
    if len(tokens) > MAX_TOKENS_PER_MESSAGE:
        raise VariableError(
            f"Trop de variables dans le message ({len(tokens)}, maximum "
            f"{MAX_TOKENS_PER_MESSAGE})."
        )
    unknown: list[str] = []

    def _sub(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in variables:
            unknown.append(name)
            return match.group(0)
        value = variables[name]
        if isinstance(value, list):
            if list_mode == "block":
                return "\n".join(f"- {item}" for item in value)
            return ", ".join(value)
        return value

    resolved = _TOKEN_RE.sub(_sub, escaped)
    resolved = _SENTINEL_RE.sub(r"{\1}", resolved)
    if len(resolved) > MAX_RESOLVED_LENGTH:
        raise VariableError(
            "Message résolu trop volumineux "
            f"({MAX_RESOLVED_LENGTH} caractères maximum)."
        )
    deduped: list[str] = []
    for name in unknown:
        if name not in deduped:
            deduped.append(name)
    return resolved, deduped


async def resolve_message(
    session: AsyncSession, text: str, list_mode: str = "inline"
) -> tuple[str, list[str]]:
    """resolve_text avec l'état courant de la base - MÊME fonction pour le
    preview et l'envoi réel (finding 10)."""
    variables = {v.name: v.parsed_value for v in await list_variables(session)}
    return resolve_text(text, variables, list_mode=list_mode)


async def variables_revision(session: AsyncSession) -> str:
    """Empreinte de l'état des variables (le frontend détecte un aperçu
    périmé entre le preview et l'envoi)."""
    import hashlib

    variables = await list_variables(session)
    payload = "|".join(f"{v.name}:{v.updated_at.isoformat()}" for v in variables)
    return hashlib.sha256(payload.encode()).hexdigest()[:12]
