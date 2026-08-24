"""
THÉRÈSE v2 - Config Router

Endpoints for application configuration.
"""

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

from app.config import settings
from app.models.database import get_session
from app.models.entities import Preference
from app.models.schemas import (
    ApiKeyUpdate,
    ConfigResponse,
    ImportClaudeMdRequest,
    LLMConfigResponse,
    LLMConfigUpdate,
    OllamaModelInfo,
    OllamaModelRecommendation,
    OllamaStatusResponse,
    SystemResourcesResponse,
    UserProfileResponse,
    UserProfileUpdate,
    WorkingDirectoryResponse,
    WorkingDirectoryUpdate,
)
from app.services.audit import AuditAction, log_activity
from app.services.encryption import decrypt_value, encrypt_value, is_value_encrypted
from app.services.http_client import get_http_client
from app.services.system_resources import OLLAMA_CONTEXT_MARGIN_BYTES, detect_system_memory
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

logger = logging.getLogger(__name__)

router = APIRouter()

from app.services.export_profile import ExportProfile as ExportProfileBody  # noqa: E402

# Track startup time
_startup_time = datetime.now(UTC)


async def _cles_dechiffrables(
    session: AsyncSession, pref_keys: list[str]
) -> dict[str, tuple[bool, bool]]:
    """Le même verdict que `_check_key_decryptable`, en UNE requête SQL.

    Seconde passe de revue dette 0.43.4 : la carte api_keys ajoutait 14
    vérifications unitaires aux 11 existantes (25 SELECT + déchiffrements par
    GET /api/config/, 7 clés vérifiées deux fois). Une clé absente du
    résultat n'existe pas en base : (False, False).
    """
    result = await session.execute(
        select(Preference).where(Preference.key.in_(pref_keys))
    )
    verdicts: dict[str, tuple[bool, bool]] = {k: (False, False) for k in pref_keys}
    for pref in result.scalars():
        try:
            if is_value_encrypted(pref.value):
                decrypt_value(pref.value)
            verdicts[pref.key] = (True, False)
        except Exception as e:
            logger.debug("Verification echouee (%s): %s", pref.key, e)
            verdicts[pref.key] = (False, True)
    return verdicts


async def _check_key_decryptable(session: AsyncSession, pref_key: str) -> tuple[bool, bool]:
    """Vérifie si une clé API en DB existe et est déchiffrable.

    Returns:
        (has_key, is_corrupted) : has_key=True si la ligne existe,
        is_corrupted=True si le blob Fernet est illisible.
    """
    result = await session.execute(
        select(Preference).where(Preference.key == pref_key)
    )
    pref = result.scalar_one_or_none()
    if pref is None:
        return False, False
    # La clé existe en DB - vérifier qu'elle est déchiffrable
    try:
        if is_value_encrypted(pref.value):
            decrypt_value(pref.value)
        return True, False
    except Exception as e:
        logger.debug("Verification echouee: %s", e)
        return False, True


@router.get("/", response_model=ConfigResponse)
async def get_config(session: AsyncSession = Depends(get_session)):
    """Get current application configuration."""
    # Check Ollama availability
    ollama_available = False
    try:
        client = await get_http_client()
        response = await client.get(f"{settings.ollama_base_url}/api/tags", timeout=2.0)
        ollama_available = response.status_code == 200
    except Exception as e:
        logger.debug("Service non disponible: %s", e)

    corrupted_keys: list[str] = []

    # Un fournisseur = une entrée, env d'abord puis clé chiffrée en base - la
    # même règle pour tous, plus jamais un fournisseur ajouté sans restitution
    # de sa clé (revue dette 0.43.4). Lecture GROUPÉE : une requête SQL pour
    # toutes les clés, là où l'ancien flux en faisait une par fournisseur.
    fournisseurs_llm = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "groq": "GROQ_API_KEY",
        "grok": "XAI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "perplexity": "PERPLEXITY_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "glm": "GLM_API_KEY",
        "kimi": "KIMI_API_KEY",
        "qwen": "QWEN_API_KEY",
        "minimax": "MINIMAX_API_KEY",
        "infomaniak": "INFOMANIAK_API_KEY",
    }
    autres_cles = ["openai_image", "gemini_image", "fal", "brave"]
    verdicts = await _cles_dechiffrables(
        session,
        [f"{p}_api_key" for p in fournisseurs_llm] + [f"{c}_api_key" for c in autres_cles],
    )

    def _statut(nom: str, env_ok: bool) -> bool:
        if env_ok:
            return True
        has_db, is_corrupted = verdicts[f"{nom}_api_key"]
        if is_corrupted and nom not in corrupted_keys:
            corrupted_keys.append(nom)
        return has_db and not is_corrupted

    api_keys: dict[str, bool] = {}
    for fournisseur, env_var in fournisseurs_llm.items():
        env_ok = bool(os.environ.get(env_var))
        if fournisseur == "anthropic":
            env_ok = env_ok or bool(settings.anthropic_api_key)
        elif fournisseur == "mistral":
            env_ok = env_ok or bool(settings.mistral_api_key)
        elif fournisseur == "gemini":
            env_ok = env_ok or bool(os.environ.get("GOOGLE_API_KEY"))
        api_keys[fournisseur] = _statut(fournisseur, env_ok)

    # Clés hors LLM (images, recherche web) : même flux groupé.
    has_openai_image = _statut("openai_image", bool(os.environ.get("OPENAI_IMAGE_API_KEY")))
    has_gemini_image = _statut("gemini_image", bool(os.environ.get("GEMINI_IMAGE_API_KEY")))
    has_fal = _statut("fal", bool(os.environ.get("FAL_API_KEY")))
    has_brave = _statut("brave", bool(os.environ.get("BRAVE_API_KEY")))

    # Champs historiques, servis depuis la carte (compatibilité).
    has_anthropic = api_keys["anthropic"]
    has_mistral = api_keys["mistral"]
    has_openai = api_keys["openai"]
    has_gemini = api_keys["gemini"]
    has_groq = api_keys["groq"]
    has_grok = api_keys["grok"]
    has_openrouter = api_keys["openrouter"]

    # Check web search preference (default: enabled)
    web_search_enabled = True
    result = await session.execute(
        select(Preference).where(Preference.key == "web_search_enabled")
    )
    pref = result.scalar_one_or_none()
    if pref:
        web_search_enabled = pref.value.lower() == "true"


    return ConfigResponse(
        app_name=settings.app_name,
        app_version=settings.app_version,
        llm_provider=settings.llm_provider,
        has_anthropic_key=has_anthropic,
        has_mistral_key=has_mistral,
        has_openai_key=has_openai,
        has_gemini_key=has_gemini,
        has_groq_key=has_groq,
        has_grok_key=has_grok,
        has_openrouter_key=has_openrouter,
        has_openai_image_key=has_openai_image,
        has_gemini_image_key=has_gemini_image,
        has_fal_key=has_fal,
        has_brave_key=has_brave,
        ollama_available=ollama_available,
        web_search_enabled=web_search_enabled,
        corrupted_keys=corrupted_keys,
        api_keys=api_keys,
    )


@router.post("/api-key")
async def set_api_key(
    request: ApiKeyUpdate,
    http_request: Request,
    session: AsyncSession = Depends(get_session),
):
    """
    Set an API key.

    Stores the key securely in the database with Fernet encryption (US-SEC-01).
    Validates the API key format before storing.
    """
    # Validate API key format
    key = request.api_key.strip()
    provider = request.provider.lower()

    # Validate API key format based on provider
    if provider == "anthropic" and not key.startswith("sk-ant-"):
        raise HTTPException(
            status_code=400,
            detail="La clé API Anthropic doit commencer par 'sk-ant-'"
        )
    elif provider == "openai" and not key.startswith("sk-"):
        raise HTTPException(
            status_code=400,
            detail="La clé API OpenAI doit commencer par 'sk-'"
        )
    elif provider == "openai_image" and not key.startswith("sk-"):
        raise HTTPException(
            status_code=400,
            detail="La clé API OpenAI (Image) doit commencer par 'sk-'"
        )
    elif provider == "gemini" and len(key) < 10:
        # BUG-099 : Google émet désormais des clés en 'AQ.' (avant 'AIza').
        # On ne valide plus le préfixe, juste une longueur minimale ; l'API tranche.
        raise HTTPException(
            status_code=400,
            detail="La clé API Gemini semble invalide (trop courte)"
        )
    elif provider == "gemini_image" and len(key) < 10:
        raise HTTPException(
            status_code=400,
            detail="La clé API Gemini (Image) semble invalide (trop courte)"
        )
    elif provider == "groq" and not key.startswith("gsk_"):
        raise HTTPException(
            status_code=400,
            detail="La clé API Groq doit commencer par 'gsk_'"
        )
    elif provider == "grok" and not key.startswith("xai-"):
        raise HTTPException(
            status_code=400,
            detail="La clé API Grok (xAI) doit commencer par 'xai-'"
        )
    elif provider == "openrouter" and not key.startswith("sk-or-"):
        raise HTTPException(
            status_code=400,
            detail="La clé API OpenRouter doit commencer par 'sk-or-'"
        )

    key_name = f"{request.provider}_api_key"

    # Encrypt the API key before storing (US-SEC-01)
    encrypted_key = encrypt_value(request.api_key)

    # Get or create preference
    result = await session.execute(
        select(Preference).where(Preference.key == key_name)
    )
    pref = result.scalar_one_or_none()

    is_update = pref is not None
    if pref:
        pref.value = encrypted_key
        pref.updated_at = datetime.now(UTC)
    else:
        pref = Preference(
            key=key_name,
            value=encrypted_key,
            category="llm",
        )
        session.add(pref)

    await session.commit()

    # Audit log (US-SEC-05)
    await log_activity(
        session,
        AuditAction.API_KEY_SET,
        resource_type="api_key",
        resource_id=request.provider,
        details=json.dumps({"is_update": is_update}),
    )

    # Invalider le cache des cles API pour forcer un rechargement (SEC-005)
    # Les cles sont lues depuis la DB, plus stockees dans os.environ
    from app.services.llm import invalidate_api_key_cache, load_api_key_cache
    invalidate_api_key_cache()
    await load_api_key_cache()

    # Reset LLM service to pick up new config
    import app.services.llm as _llm_mod
    _llm_mod._llm_service = None

    # Mettre à jour le cache Brave Search si la clé change
    if provider == "brave":
        from app.services.web_search import set_brave_api_key
        set_brave_api_key(key)

    return {"success": True, "provider": request.provider}


@router.delete("/api-key/{provider}")
async def delete_api_key(
    provider: str,
    http_request: Request,
    session: AsyncSession = Depends(get_session),
):
    """
    Delete an API key.

    Removes the encrypted key from the database.
    """
    key_name = f"{provider}_api_key"

    result = await session.execute(
        select(Preference).where(Preference.key == key_name)
    )
    pref = result.scalar_one_or_none()

    if not pref:
        raise HTTPException(status_code=404, detail=f"API key for {provider} not found")

    await session.delete(pref)
    await session.commit()

    # Remove from environment
    env_mapping = {
        "anthropic": "ANTHROPIC_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "groq": "GROQ_API_KEY",
        "grok": "XAI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "openai_image": "OPENAI_IMAGE_API_KEY",
        "gemini_image": "GEMINI_IMAGE_API_KEY",
        "fal": "FAL_API_KEY",
    }
    if provider in env_mapping and env_mapping[provider] in os.environ:
        del os.environ[env_mapping[provider]]

    # Audit log (US-SEC-05)
    await log_activity(
        session,
        AuditAction.API_KEY_DELETED,
        resource_type="api_key",
        resource_id=provider,
    )

    return {"success": True, "provider": provider, "deleted": True}


@router.get("/export-profile")
async def get_export_profile() -> dict[str, object]:
    """Profil d'export DOCX (chantier 5) + avertissement si fichier illisible."""
    from app.services.export_profile import load_export_profile

    profile, warning = load_export_profile()
    return {"profile": profile.model_dump(), "warning": warning}


@router.put("/export-profile")
async def set_export_profile(profile: "ExportProfileBody") -> dict[str, object]:
    """Remplace le profil d'export (validation stricte Pydantic, 422 sinon).
    L'import de profil = ce même PUT avec le contenu JSON du fichier."""
    from app.services.export_profile import ExportProfile, save_export_profile

    validated = ExportProfile.model_validate(profile.model_dump(exclude_unset=True))
    save_export_profile(validated)
    return {"profile": validated.model_dump(), "warning": None}


@router.delete("/export-profile")
async def reset_export_profile_route() -> dict[str, bool]:
    """Réinitialise le profil d'export aux défauts (charte Synoptia)."""
    from app.services.export_profile import reset_export_profile

    reset_export_profile()
    return {"success": True}


@router.get("/preferences")
async def get_preferences(
    category: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """Get all preferences, optionally filtered by category."""
    query = select(Preference)
    if category:
        query = query.where(Preference.category == category)

    result = await session.execute(query)
    preferences = result.scalars().all()

    return {
        pref.key: {
            "value": json.loads(pref.value)
            if pref.value.startswith("[") or pref.value.startswith("{")
            else pref.value,
            "category": pref.category,
            "updated_at": pref.updated_at.isoformat(),
        }
        for pref in preferences
        # Don't expose API keys
        if "api_key" not in pref.key
    }


@router.put("/preferences/{key}")
async def set_preference(
    key: str,
    value: str | int | float | bool | list | dict,
    category: str = "general",
    session: AsyncSession = Depends(get_session),
):
    """Set a preference value."""
    # Prevent setting API keys through this endpoint
    if "api_key" in key.lower():
        raise HTTPException(
            status_code=400, detail="Use /api-key endpoint for API keys"
        )

    # Revue dette 0.43.4 : ce detour permettait d'ecrire une adresse de
    # fournisseur invalide, relue ensuite sans controle par POST /llm.
    if key.lower().endswith("_base_url"):
        if not isinstance(value, str) or not _base_url_valide(value.strip()):
            raise HTTPException(
                status_code=400,
                detail="Adresse invalide : http(s):// avec un hôte, sans espace",
            )

    # Serialize value
    if isinstance(value, (list, dict)):
        value_str = json.dumps(value)
    else:
        value_str = str(value)

    # Get or create preference
    result = await session.execute(select(Preference).where(Preference.key == key))
    pref = result.scalar_one_or_none()

    if pref:
        pref.value = value_str
        pref.category = category
        pref.updated_at = datetime.now(UTC)
    else:
        pref = Preference(
            key=key,
            value=value_str,
            category=category,
        )
        session.add(pref)

    await session.commit()

    return {"success": True, "key": key, "value": value}


# ============================================================
# Web Search Settings
# ============================================================


@router.get("/web-search")
async def get_web_search_status(session: AsyncSession = Depends(get_session)):
    """Get web search configuration status."""
    result = await session.execute(
        select(Preference).where(Preference.key == "web_search_enabled")
    )
    pref = result.scalar_one_or_none()
    enabled = pref.value.lower() == "true" if pref else True  # Default: enabled

    # Vérifier si Brave Search est configuré
    has_brave = bool(os.environ.get("BRAVE_API_KEY"))
    if not has_brave:
        brave_result = await session.execute(
            select(Preference).where(Preference.key == "brave_api_key")
        )
        has_brave = brave_result.scalar_one_or_none() is not None

    others_provider = "Brave Search API" if has_brave else "DuckDuckGo (tool calling)"
    description = (
        f"Gemini utilise le grounding Google Search natif. "
        f"Les autres LLMs (Claude, GPT, Mistral, Grok) utilisent {others_provider} via tool calling."
    )

    return {
        "enabled": enabled,
        "providers": {
            "gemini": "Google Search Grounding (natif)",
            "others": others_provider,
        },
        "has_brave_key": has_brave,
        "description": description,
    }


@router.post("/web-search")
async def set_web_search_status(
    enabled: bool,
    session: AsyncSession = Depends(get_session),
):
    """Enable or disable web search for LLMs."""
    result = await session.execute(
        select(Preference).where(Preference.key == "web_search_enabled")
    )
    pref = result.scalar_one_or_none()

    if pref:
        pref.value = str(enabled).lower()
        pref.updated_at = datetime.now(UTC)
    else:
        pref = Preference(
            key="web_search_enabled",
            value=str(enabled).lower(),
            category="features",
        )
        session.add(pref)

    await session.commit()

    return {"success": True, "enabled": enabled}


@router.delete("/preferences/{key}")
async def delete_preference(
    key: str,
    session: AsyncSession = Depends(get_session),
):
    """Delete a preference."""
    result = await session.execute(select(Preference).where(Preference.key == key))
    pref = result.scalar_one_or_none()

    if not pref:
        raise HTTPException(status_code=404, detail="Preference not found")

    await session.delete(pref)
    await session.commit()

    return {"deleted": True, "key": key}


@router.post("/export")
async def export_data(
    session: AsyncSession = Depends(get_session),
):
    """
    Export all user data.

    Returns a JSON file with all contacts, projects, conversations, etc.
    """
    from app.models.entities import Contact, Conversation, Message, Project

    # Get all data
    contacts_result = await session.execute(select(Contact))
    contacts = contacts_result.scalars().all()

    projects_result = await session.execute(select(Project))
    projects = projects_result.scalars().all()

    conversations_result = await session.execute(select(Conversation))
    conversations = conversations_result.scalars().all()

    messages_result = await session.execute(select(Message))
    messages = messages_result.scalars().all()

    export_data = {
        "exported_at": datetime.now(UTC).isoformat(),
        "app_version": settings.app_version,
        "contacts": [
            {
                "id": c.id,
                "first_name": c.first_name,
                "last_name": c.last_name,
                "company": c.company,
                "email": c.email,
                "phone": c.phone,
                "notes": c.notes,
                "tags": json.loads(c.tags) if c.tags else None,
                "created_at": c.created_at.isoformat(),
            }
            for c in contacts
        ],
        "projects": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "contact_id": p.contact_id,
                "status": p.status,
                "budget": p.budget,
                "notes": p.notes,
                "tags": json.loads(p.tags) if p.tags else None,
                "created_at": p.created_at.isoformat(),
            }
            for p in projects
        ],
        "conversations": [
            {
                "id": conv.id,
                "title": conv.title,
                "summary": conv.summary,
                "created_at": conv.created_at.isoformat(),
                "messages": [
                    {
                        "id": m.id,
                        "role": m.role,
                        "content": m.content,
                        "created_at": m.created_at.isoformat(),
                    }
                    for m in messages
                    if m.conversation_id == conv.id
                ],
            }
            for conv in conversations
        ],
    }

    return export_data


@router.get("/stats")
async def get_stats(
    session: AsyncSession = Depends(get_session),
):
    """Get usage statistics."""
    from app.models.entities import Contact, Conversation, FileMetadata, Message, Project
    from sqlmodel import func

    # Count entities
    contacts_count = (
        await session.execute(select(func.count()).select_from(Contact))
    ).scalar()
    projects_count = (
        await session.execute(select(func.count()).select_from(Project))
    ).scalar()
    conversations_count = (
        await session.execute(select(func.count()).select_from(Conversation))
    ).scalar()
    messages_count = (
        await session.execute(select(func.count()).select_from(Message))
    ).scalar()
    files_count = (
        await session.execute(select(func.count()).select_from(FileMetadata))
    ).scalar()

    # Uptime
    uptime = (datetime.now(UTC) - _startup_time).total_seconds()

    return {
        "entities": {
            "contacts": contacts_count,
            "projects": projects_count,
            "conversations": conversations_count,
            "messages": messages_count,
            "files": files_count,
        },
        "uptime_seconds": uptime,
        "data_dir": str(settings.data_dir),
        "db_path": str(settings.db_path),
    }


@router.get("/stats/qdrant")
async def get_qdrant_stats():
    """Get Qdrant vector store statistics."""
    from app.services.qdrant import get_qdrant_service

    try:
        service = get_qdrant_service()
        stats = service.get_stats()
        return {
            "status": "connected",
            "collection": settings.qdrant_collection,
            **stats,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


# ============================================================
# User Profile / Identity Endpoints
# ============================================================


async def _mark_onboarding_completed(session: AsyncSession) -> Preference:
    """Pose le marqueur d'onboarding de façon idempotente."""
    result = await session.execute(
        select(Preference).where(Preference.key == "onboarding_completed")
    )
    pref = result.scalar_one_or_none()
    now = datetime.now(UTC)
    if pref:
        pref.value = "true"
        pref.category = "system"
        pref.updated_at = now
    else:
        pref = Preference(
            key="onboarding_completed",
            value="true",
            category="system",
            updated_at=now,
        )
        session.add(pref)
    await session.commit()
    return pref


@router.get("/profile", response_model=UserProfileResponse | None)
async def get_profile(session: AsyncSession = Depends(get_session)):
    """
    Get user profile / identity.

    Returns the configured user profile or null if not set.
    """
    from app.services.user_profile import get_user_profile

    profile = await get_user_profile(session)

    if not profile:
        return None

    return UserProfileResponse(
        name=profile.name,
        nickname=profile.nickname,
        company=profile.company,
        role=profile.role,
        context=profile.context,
        email=profile.email,
        location=profile.location,
        address=profile.address,
        siren=profile.siren,
        tva_intra=profile.tva_intra,
        siret=profile.siret,
        code_ape=profile.code_ape,
        nda=profile.nda,
        display_name=profile.display_name(),
    )


@router.post("/profile", response_model=UserProfileResponse)
async def set_profile(
    request: UserProfileUpdate,
    session: AsyncSession = Depends(get_session),
):
    """
    Set user profile / identity.

    This is used to personalize THÉRÈSE responses and fix the
    issue where the assistant might call the user by wrong names.
    """
    from app.services.user_profile import (
        UserProfile,
        set_cached_profile,
        set_user_profile,
    )

    profile = UserProfile(
        name=request.name,
        nickname=request.nickname,
        company=request.company,
        role=request.role,
        context=request.context,
        email=request.email,
        location=request.location,
        address=request.address,
        siren=request.siren,
        tva_intra=request.tva_intra,
        siret=request.siret,
        code_ape=request.code_ape,
        nda=request.nda,
    )

    saved_profile = await set_user_profile(session, profile)

    # Update cache for LLM service
    set_cached_profile(saved_profile)

    # L'identité est le premier jalon durable de l'onboarding. Le marqueur est
    # posé côté backend dès que ce profil valide est enregistré, afin qu'un
    # arrêt pendant les étapes suivantes ne relance pas le wizard au démarrage.
    await _mark_onboarding_completed(session)

    return UserProfileResponse(
        name=saved_profile.name,
        nickname=saved_profile.nickname,
        company=saved_profile.company,
        role=saved_profile.role,
        context=saved_profile.context,
        email=saved_profile.email,
        location=saved_profile.location,
        address=saved_profile.address,
        siren=saved_profile.siren,
        tva_intra=saved_profile.tva_intra,
        siret=saved_profile.siret,
        code_ape=saved_profile.code_ape,
        nda=saved_profile.nda,
        display_name=saved_profile.display_name(),
    )


@router.delete("/profile")
async def delete_profile(session: AsyncSession = Depends(get_session)):
    """Delete user profile."""
    from app.services.user_profile import delete_user_profile, set_cached_profile

    deleted = await delete_user_profile(session)
    set_cached_profile(None)

    return {"deleted": deleted}


@router.get("/therese-md")
async def get_therese_md() -> dict[str, str | bool]:
    """Lit le contenu de THERESE.md."""
    from pathlib import Path

    md_path = Path(settings.data_dir) / "THERESE.md"
    if not md_path.exists():
        return {"content": "", "path": str(md_path), "exists": False}
    content = md_path.read_text(encoding="utf-8")
    return {"content": content, "path": str(md_path), "exists": True}


@router.post("/therese-md")
async def save_therese_md(request: dict) -> dict[str, str | bool]:  # type: ignore[type-arg]
    """Sauvegarde le contenu de THERESE.md."""
    from pathlib import Path

    md_path = Path(settings.data_dir) / "THERESE.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(request.get("content", ""), encoding="utf-8")
    return {"success": True, "path": str(md_path)}


@router.post("/profile/import-claude-md", response_model=UserProfileResponse)
async def import_claude_md(
    request: ImportClaudeMdRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Import user profile from a THERESE.md file.

    Parses the THERESE.md file to extract user identity information
    like name, nickname, company, role, etc.
    """
    from app.services.user_profile import (
        import_from_claude_md,
        set_cached_profile,
    )

    profile = await import_from_claude_md(session, request.file_path)

    # Update cache
    set_cached_profile(profile)

    return UserProfileResponse(
        name=profile.name,
        nickname=profile.nickname,
        company=profile.company,
        role=profile.role,
        context=profile.context,
        email=profile.email,
        location=profile.location,
        display_name=profile.display_name(),
    )


# ============================================================
# Working Directory Endpoints
# ============================================================


@router.get("/working-directory", response_model=WorkingDirectoryResponse)
async def get_working_directory(session: AsyncSession = Depends(get_session)):
    """Get current working directory setting."""
    from pathlib import Path

    result = await session.execute(
        select(Preference).where(Preference.key == "working_directory")
    )
    pref = result.scalar_one_or_none()

    if not pref:
        return WorkingDirectoryResponse(path=None, exists=False)

    path = Path(pref.value)
    return WorkingDirectoryResponse(
        path=pref.value,
        exists=path.exists() and path.is_dir(),
    )


@router.post("/working-directory", response_model=WorkingDirectoryResponse)
async def set_working_directory(
    request: WorkingDirectoryUpdate,
    session: AsyncSession = Depends(get_session),
):
    """
    Set the working directory for file operations.

    Validates that the path exists and is a directory.
    """
    from pathlib import Path

    path = Path(request.path)

    if not path.exists():
        raise HTTPException(status_code=400, detail="Path does not exist")

    if not path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    # Get or create preference
    result = await session.execute(
        select(Preference).where(Preference.key == "working_directory")
    )
    pref = result.scalar_one_or_none()

    if pref:
        pref.value = str(path.resolve())
        pref.updated_at = datetime.now(UTC)
    else:
        pref = Preference(
            key="working_directory",
            value=str(path.resolve()),
            category="files",
        )
        session.add(pref)

    await session.commit()

    return WorkingDirectoryResponse(
        path=str(path.resolve()),
        exists=True,
    )


# ============================================================
# LLM Configuration Endpoints
# ============================================================


async def _available_models_for(provider_value: str) -> list[str]:
    """
    Liste des modeles disponibles pour un provider donne.

    Source de verite unique utilisee par GET et POST /llm : sans ca, un POST
    de bascule de provider renvoyait une liste vide pour les providers cloud
    (le selecteur frontend tombait a 1 seul modele apres changement).
    """
    available_models: list[str] = []
    # Listes relevées dans la documentation officielle de chaque fournisseur le
    # 24/08/2026, puis contre-vérifiées. Le PREMIER de chaque liste est celui
    # que l'interface pré-sélectionne : l'ordre EST la recommandation.
    #
    # Les identifiants Anthropic sans date sont des instantanés figés, pas des
    # pointeurs perpétuels : une nouvelle version sortira sous un nouveau nom et
    # cette liste devra être reprise à la main.
    #
    # Trois échéances à surveiller : claude-sonnet-4-5 sort de support le
    # 29/09/2026, claude-haiku-4-5 le 15/10/2026, claude-opus-4-5 le 24/11/2026.
    if provider_value == "anthropic":
        available_models = [
            "claude-opus-5",                 # Le plus polyvalent (recommandé)
            "claude-fable-5",                # Puissance maximale, plus lent
            "claude-sonnet-5",               # Équilibre vitesse/intelligence
            "claude-haiku-4-5-20251001",     # Le plus rapide
            "claude-opus-4-8",               # Génération précédente
            "claude-opus-4-7",
            "claude-opus-4-6",
            "claude-sonnet-4-6",
        ]
    elif provider_value == "openai":
        # gpt-5.3-codex est volontairement absent : sa fiche indique qu'il
        # refuse `v1/chat/completions`, le seul point d'appel que nous
        # utilisons. Le proposer garantirait un échec à chaque requête.
        available_models = [
            "gpt-5.6-sol",       # Le plus capable (recommandé)
            "gpt-5.6-terra",     # Équilibre intelligence/coût
            "gpt-5.6-luna",      # Le plus économique de la génération
            "gpt-5.5",           # Génération précédente
            "gpt-5.5-pro",       # Réflexion longue
            "gpt-5.4-mini",      # Petit, rapide, bon marché
        ]
    elif provider_value == "gemini":
        # Aucun Gemini Pro en version stable sur la génération 3 : le seul Pro
        # récent reste en avant-première, vérifié deux fois.
        available_models = [
            "gemini-3.7-flash",           # Le plus récent (recommandé)
            "gemini-3.1-pro-preview",     # Le seul Pro récent
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",      # Le plus économique
            "gemini-2.5-pro",             # Ancienne génération
            "gemini-2.5-flash",
        ]
    elif provider_value == "mistral":
        # Ne JAMAIS utiliser les formes `mistral-medium-3-5-26-04` : ce sont des
        # adresses de pages de documentation, pas des identifiants d'API.
        available_models = [
            "mistral-medium-latest",  # Vaisseau amiral (recommandé)
            "mistral-large-latest",   # Grand modèle, pointeur à jour
            "mistral-large-2512",     # Version figée, Apache 2.0
            "mistral-small-2603",     # Petit modèle
            "codestral-2508",         # Spécialiste du code
            "ministral-8b-2512",      # Léger
            "ministral-3b-2512",      # Le plus petit
        ]
    elif provider_value == "grok":
        available_models = [
            "grok-4.6",                      # Le plus intelligent (recommandé)
            "grok-4.5",                      # Génération précédente
            "grok-4.3",                      # Économique, très grand contexte
            "grok-4.20-0309-reasoning",      # Raisonnement long
            "grok-4.20-0309-non-reasoning",  # Réponse directe
        ]
    elif provider_value == "glm":
        # Z.ai, plateforme internationale. Relevé sur docs.z.ai le 24/08/2026.
        available_models = [
            "glm-5.3",         # Ingénierie logicielle et agents (recommandé)
            "glm-5.2",         # Génération précédente, tâches longues
            "glm-5.1",
            "glm-5",
            "glm-5-turbo",     # Optimisé pour les agents
            "glm-4.7",         # Ancienne génération, bon en code
            "glm-4.7-flashx",  # Léger et rapide
            "glm-4.7-flash",   # Léger, gratuit
        ]
    elif provider_value == "kimi":
        # Moonshot AI. kimi-k3 offre un million de jetons de contexte.
        available_models = [
            "kimi-k3",                    # Le plus capable (recommandé)
            "kimi-k2.7-code",             # Spécialiste du code
            "kimi-k2.7-code-highspeed",   # Même chose, accéléré
            "kimi-k2.6",                  # Génération précédente, multimodal
            "kimi-k2.5",                  # Économique
        ]
    elif provider_value == "qwen":
        # Alibaba Model Studio. L'adresse contient l'identifiant d'espace de
        # travail du compte : elle doit être renseignée dans les réglages.
        available_models = [
            "qwen3.8-max",        # Vaisseau amiral (recommandé)
            "qwen3.7-plus",       # Équilibré, très grand contexte
            "qwen3.7-flash",      # Rapide et économique
            "qwen3-coder-plus",   # Spécialiste du code et des agents
        ]
    elif provider_value == "minimax":
        # La casse compte : l'API refuse les minuscules.
        available_models = [
            "MiniMax-M3",              # Le plus récent (recommandé)
            "MiniMax-M2.7",            # Génération précédente
            "MiniMax-M2.7-highspeed",  # Même modèle, accéléré
            "MiniMax-M2.5",
            "MiniMax-M2.5-highspeed",
        ]
    elif provider_value == "deepseek":
        # `deepseek-chat` et `deepseek-reasoner` ont DISPARU de l'API : absents
        # de la page des tarifs comme du guide de démarrage au 24/08/2026.
        available_models = [
            "deepseek-v4-pro",     # Modèle complet, mode réflexion (recommandé)
            "deepseek-v4-flash",   # Rapide et bon marché
        ]
    elif provider_value == "openrouter":
        # OpenRouter : fetch dynamique des modèles disponibles
        fallback_models = [
            "anthropic/claude-sonnet-4-6",
            "anthropic/claude-opus-4-8",
            "openai/gpt-5.5",
            "google/gemini-3.1-pro",
            "google/gemini-3.5-flash",
            "meta-llama/llama-4-maverick",
        ]
        try:
            from app.services.llm import _get_api_key_from_db
            or_key = _get_api_key_from_db("openrouter") or os.environ.get("OPENROUTER_API_KEY", "")
            if or_key:
                client = await get_http_client()
                resp = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {or_key}"},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m["id"] for m in data.get("data", []) if m.get("id")]
                    # Trier : providers connus en premier, puis alphabétique
                    priority_prefixes = ["anthropic/", "openai/", "google/", "meta-llama/", "mistralai/"]
                    def sort_key(m):
                        for i, p in enumerate(priority_prefixes):
                            if m.startswith(p):
                                return (i, m)
                        return (len(priority_prefixes), m)
                    available_models = sorted(models, key=sort_key)[:50]  # Max 50
                else:
                    available_models = fallback_models
            else:
                available_models = fallback_models
        except Exception as e:
            logger.warning(f"Failed to fetch OpenRouter models: {e}")
            available_models = fallback_models
    elif provider_value == "ollama":
        # F-14 : lister les modèles Ollama installés localement
        try:
            client = await get_http_client()
            resp = await client.get(f"{settings.ollama_base_url}/api/tags", timeout=5.0)
            if resp.status_code == 200:
                from app.services.ollama_capabilites import gere_les_outils

                data = resp.json()
                # BUG-169 : un modèle incapable d'appeler des outils ne peut ni
                # créer un contact, ni poser un rendez-vous, ni produire un
                # document. Le proposer, c'est promettre ce qu'il ne fera pas —
                # un testeur a attendu 3 min 26 s avant une réponse dégradée.
                # Il reste visible plus bas, désactivé et motivé, plutôt que
                # masqué : disparaître sans explication est le défaut qu'on
                # corrige partout ailleurs dans cette version.
                available_models = [
                    m.get("name", "") for m in data.get("models", [])
                    if m.get("name")
                    and _categorize_ollama_model(m["name"]) == "chat"
                    and gere_les_outils(m["name"])
                ]
        except Exception:
            # Ollama non disponible - liste vide, pas d'erreur
            available_models = []
    return available_models


@router.get("/capacites")
async def get_capacites_manifeste() -> dict:
    """Schéma et empreinte du manifeste de capacités (0.44).

    La moitié backend du contrôle de génération : le frontend embarque le même
    fichier canonique dans son bundle et compare au démarrage. Une divergence
    signale un frontend et un sidecar packagés à des moments différents.
    """
    from app.services.capacites import capacites, charger_manifeste, empreinte_manifeste

    return {
        "schema": charger_manifeste().get("schema", 0),
        "empreinte": empreinte_manifeste(),
        "nombre_capacites": len(capacites()),
    }


@router.get("/llm", response_model=LLMConfigResponse)
async def get_llm_config(session: AsyncSession = Depends(get_session)):
    """Get current LLM configuration."""
    from app.services.llm import LLMProvider as LLMProvider_module
    from app.services.llm import get_llm_service

    service = get_llm_service()
    config = service.config

    # Get available models for the provider (source unique partagee avec POST)
    available_models = await _available_models_for(config.provider.value)
    config_available = (
        bool(available_models)
        if config.provider.value == "ollama"
        else bool(config.api_key and config.model)
    )

    # Inclure le modele actif dans la liste s il est custom
    if config.model and config.model not in available_models:
        available_models.append(config.model)

    return LLMConfigResponse(
        provider=config.provider.value,
        model=config.model,
        available_models=available_models,
        available=config_available,
        effort=config.effort,
        base_url=config.base_url if config.provider != LLMProvider_module.OLLAMA else None,
    )


def _base_url_valide(adresse: str) -> bool:
    """Délègue au module neutre : la même règle pour tout lecteur/écrivain."""
    from app.services.providers.base import adresse_fournisseur_valide

    return bool(adresse_fournisseur_valide(adresse))


@router.get("/llm/models/{provider_value}")
async def get_available_models(provider_value: str) -> dict[str, Any]:
    """Catalogue des modèles d'un fournisseur - LA source, servie au frontend.

    Dette 0.43.4 : quatre copies du catalogue vivaient dans le frontend et
    divergeaient déjà (l'onboarding proposait encore gpt-5.3-codex, retiré
    partout ailleurs). Le frontend interroge cette route ; les noms lisibles
    et les badges restent une décoration locale, la LISTE vient d'ici.
    """
    from app.services.llm import LLMProvider

    try:
        LLMProvider(provider_value)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Fournisseur inconnu : {provider_value}"
        )
    return {
        "provider": provider_value,
        "models": await _available_models_for(provider_value),
    }


@router.post("/llm", response_model=LLMConfigResponse)
async def set_llm_config(
    request: LLMConfigUpdate,
    session: AsyncSession = Depends(get_session),
):
    """
    Set LLM provider and model.

    This updates the current LLM configuration for the session.
    """
    import app.services.llm as llm_module
    from app.services.llm import LLMConfig, LLMProvider, LLMService

    # Validate provider
    try:
        provider = LLMProvider(request.provider)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider: {request.provider}",
        )

    # Get the API key for the provider
    api_key = None
    base_url = None

    # Helper: déchiffrer la clé API stockée en DB (chiffrée Fernet)
    def _decrypt_pref_value(pref_value: str) -> str | None:
        if not pref_value:
            return None
        if is_value_encrypted(pref_value):
            try:
                return decrypt_value(pref_value)
            except Exception:
                logger.warning("Échec déchiffrement clé API dans set_llm_config")
                return None
        return pref_value

    env_key_map = {
        LLMProvider.ANTHROPIC: ("ANTHROPIC_API_KEY", "anthropic_api_key"),
        LLMProvider.OPENAI: ("OPENAI_API_KEY", "openai_api_key"),
        LLMProvider.GEMINI: ("GEMINI_API_KEY", "gemini_api_key"),
        LLMProvider.MISTRAL: ("MISTRAL_API_KEY", "mistral_api_key"),
        LLMProvider.GROK: ("XAI_API_KEY", "grok_api_key"),
        LLMProvider.OPENROUTER: ("OPENROUTER_API_KEY", "openrouter_api_key"),
        LLMProvider.PERPLEXITY: ("PERPLEXITY_API_KEY", "perplexity_api_key"),
        LLMProvider.DEEPSEEK: ("DEEPSEEK_API_KEY", "deepseek_api_key"),
        LLMProvider.GLM: ("GLM_API_KEY", "glm_api_key"),
        LLMProvider.KIMI: ("KIMI_API_KEY", "kimi_api_key"),
        LLMProvider.QWEN: ("QWEN_API_KEY", "qwen_api_key"),
        LLMProvider.MINIMAX: ("MINIMAX_API_KEY", "minimax_api_key"),
        LLMProvider.INFOMANIAK: ("INFOMANIAK_API_KEY", "infomaniak_api_key"),
    }

    if provider == LLMProvider.OLLAMA:
        base_url = settings.ollama_base_url
    elif provider in env_key_map:
        env_var, pref_key = env_key_map[provider]
        api_key = os.environ.get(env_var)
        if provider == LLMProvider.GEMINI and not api_key:
            api_key = os.environ.get("GOOGLE_API_KEY")
        result = await session.execute(
            select(Preference).where(Preference.key == pref_key)
        )
        pref = result.scalar_one_or_none()
        if pref and not api_key:
            api_key = _decrypt_pref_value(pref.value)

    # Adresse personnalisée (dette 0.43.4). Portée par fournisseur - l'adresse
    # d'espace de travail Qwen n'a aucun sens pour OpenAI. None = conserver
    # l'existante, chaîne vide = effacer.
    if provider != LLMProvider.OLLAMA:
        cle_base_url = f"{provider.value}_base_url"
        result = await session.execute(
            select(Preference).where(Preference.key == cle_base_url)
        )
        pref_base = result.scalar_one_or_none()
        if request.base_url is None:
            base_url = pref_base.value or None if pref_base else None
            # Defense en profondeur : une adresse invalide arrivee par un autre
            # chemin d'ecriture ne doit jamais atteindre le fournisseur.
            if base_url and not _base_url_valide(base_url):
                logger.warning(
                    "Adresse %s stockee invalide (%r) : ignoree", cle_base_url, base_url
                )
                base_url = None
        else:
            demandee = request.base_url.strip()
            if demandee and not _base_url_valide(demandee):
                raise HTTPException(
                    status_code=400,
                    detail="Adresse invalide : http(s):// avec un hôte, sans espace",
                )
            base_url = demandee or None
            if pref_base:
                pref_base.value = demandee
                pref_base.updated_at = datetime.now(UTC)
            else:
                session.add(Preference(
                    key=cle_base_url, value=demandee, category="llm",
                ))

    # Effort de raisonnement (10/07/2026) : None = conserver le reglage
    # existant ; "auto" = defaut serveur (rien d'envoye, preference posee).
    if request.effort is None:
        result = await session.execute(
            select(Preference).where(Preference.key == "llm_effort")
        )
        pref_effort = result.scalar_one_or_none()
        stored_effort = pref_effort.value if pref_effort else "auto"
    else:
        stored_effort = request.effort
    effective_effort = None if stored_effort == "auto" else stored_effort

    # Create new config
    config = LLMConfig(
        provider=provider,
        model=request.model,
        api_key=api_key,
        base_url=base_url,
        effort=effective_effort,
    )

    # Create new service with this config
    llm_module._llm_service = LLMService(config)

    # Save to preferences
    result = await session.execute(
        select(Preference).where(Preference.key == "llm_provider")
    )
    pref = result.scalar_one_or_none()
    if pref:
        pref.value = request.provider
        pref.updated_at = datetime.now(UTC)
    else:
        pref = Preference(key="llm_provider", value=request.provider, category="llm")
        session.add(pref)

    result = await session.execute(
        select(Preference).where(Preference.key == "llm_model")
    )
    pref = result.scalar_one_or_none()
    if pref:
        pref.value = request.model
        pref.updated_at = datetime.now(UTC)
    else:
        pref = Preference(key="llm_model", value=request.model, category="llm")
        session.add(pref)

    result = await session.execute(
        select(Preference).where(Preference.key == "llm_effort")
    )
    pref = result.scalar_one_or_none()
    if pref:
        pref.value = stored_effort
        pref.updated_at = datetime.now(UTC)
    else:
        pref = Preference(key="llm_effort", value=stored_effort, category="llm")
        session.add(pref)

    await session.commit()

    # Liste des modèles disponibles : même source que le GET (symétrie GET/POST,
    # sinon le selecteur frontend tombait a 1 seul modele apres bascule cloud).
    post_available_models = await _available_models_for(provider.value)
    config_available = (
        bool(post_available_models)
        if provider == LLMProvider.OLLAMA
        else bool(api_key and request.model)
    )

    # Inclure le modele custom dans la reponse POST aussi
    if request.model and request.model not in post_available_models:
        post_available_models.append(request.model)

    return LLMConfigResponse(
        provider=request.provider,
        model=request.model,
        available_models=post_available_models,
        available=config_available,
        effort=effective_effort,
        base_url=base_url if provider != LLMProvider.OLLAMA else None,
    )


# ============================================================
# Ollama Endpoints
# ============================================================


@router.get("/system-resources", response_model=SystemResourcesResponse)
async def get_system_resources() -> SystemResourcesResponse:
    """Expose la RAM physique et le plafond prudent réservé aux modèles locaux."""
    memory = detect_system_memory()
    safe_limit = memory.total_bytes // 2 if memory.total_bytes is not None else None
    return SystemResourcesResponse(
        total_ram_bytes=memory.total_bytes,
        safe_local_model_ram_bytes=safe_limit,
        ollama_context_margin_bytes=OLLAMA_CONTEXT_MARGIN_BYTES,
        detection_method=memory.detection_method,
    )


def _categorize_ollama_model(model_name: str) -> str:
    """Catégorise un modèle Ollama par usage (BUG-075)."""
    name = model_name.lower().split(":")[0]
    # Embeddings
    if any(x in name for x in ["bge-", "nomic-embed", "all-minilm", "mxbai-embed", "jina-embed", "snowflake-arctic-embed", "stella", "gte-", "e5-", "llama-embed"]):
        return "embedding"
    # Vision
    if any(x in name for x in ["llava", "moondream", "minicpm-v", "cogvlm", "internvl", "bakllava"]):
        return "vision"
    # Transcription
    if "whisper" in name:
        return "transcription"
    return "chat"


def _recommend_ollama_models(model_names: list[str]) -> OllamaModelRecommendation:
    """Recommande le meilleur modèle Ollama installé selon la tâche."""
    # Priorité par catégorie (du meilleur au moins bon)
    general_prio = ["qwen3.5", "qwen3", "mistral-large", "gemma3:27b", "llama4", "mistral-nemo", "gemma3:12b", "mistral", "llama3", "gemma3", "phi3"]
    coding_prio = ["qwen3-coder", "codestral", "deepseek-coder", "starcoder", "qwen3.5", "mistral-large", "mistral-nemo"]
    writing_prio = ["qwen3.5", "mistral-large", "gemma3:27b", "llama4", "mistral-nemo", "gemma3:12b", "mistral"]
    fast_prio = ["phi3:mini", "gemma3:1b", "gemma3:4b", "qwen3:4b", "phi3", "mistral-nemo", "gemma3"]

    def find_best(priorities: list[str]) -> str | None:
        for prio in priorities:
            for name in model_names:
                if prio in name:
                    return name
        return model_names[0] if model_names else None

    return OllamaModelRecommendation(
        general=find_best(general_prio),
        coding=find_best(coding_prio),
        writing=find_best(writing_prio),
        fast=find_best(fast_prio),
    )


@router.get("/ollama/status", response_model=OllamaStatusResponse)
async def get_ollama_status():
    """Check Ollama availability and list installed models."""
    import httpx

    try:
        client = await get_http_client()
        response = await client.get(f"{settings.ollama_base_url}/api/tags", timeout=5.0)

        if response.status_code != 200:
            return OllamaStatusResponse(
                available=False,
                base_url=settings.ollama_base_url,
                error=f"Ollama returned status {response.status_code}",
            )

        from app.services.ollama_capabilites import gere_les_outils, motif_d_exclusion

        data = response.json()
        models = [
            OllamaModelInfo(
                gere_les_outils=gere_les_outils(m.get("name", "")),
                motif_indisponible=motif_d_exclusion(m.get("name", "")),
                name=m.get("name", ""),
                size=m.get("size"),
                modified_at=m.get("modified_at"),
                digest=m.get("digest"),
                usage_type=_categorize_ollama_model(m.get("name", "")),
            )
            for m in data.get("models", [])
        ]

        # Recommandations de modèles selon la tâche
        model_names = [m.name.lower() for m in models]
        recommendations = _recommend_ollama_models(model_names)

        return OllamaStatusResponse(
            available=True,
            base_url=settings.ollama_base_url,
            models=models,
            recommendations=recommendations,
        )

    except httpx.ConnectError:
        return OllamaStatusResponse(
            available=False,
            base_url=settings.ollama_base_url,
            error="Cannot connect to Ollama. Is it running?",
        )
    except Exception as e:
        return OllamaStatusResponse(
            available=False,
            base_url=settings.ollama_base_url,
            error=str(e),
        )


# ============================================================
# Onboarding Endpoints
# ============================================================


@router.get("/onboarding-complete")
async def get_onboarding_status(session: AsyncSession = Depends(get_session)):
    """
    Check if onboarding has been completed.

    Returns the onboarding completion status.
    Detects existing data in DB to avoid re-triggering onboarding after a restore.
    """
    from app.models.entities import Contact, Conversation
    from sqlalchemy import func

    result = await session.execute(
        select(Preference).where(Preference.key == "onboarding_completed")
    )
    pref = result.scalar_one_or_none()

    if pref and pref.value == "true":
        return {
            "completed": True,
            "completed_at": pref.updated_at.isoformat() if pref.updated_at else None,
        }

    # Si pas de flag mais un profil ou des données existent -> onboarding déjà
    # engagé. Cela répare aussi les installations arrêtées juste après l'étape
    # Profil avant l'introduction du marquage immédiat.
    profile_result = await session.execute(
        select(Preference).where(
            Preference.key == "user_profile",
            Preference.category == "identity",
        )
    )
    has_profile = profile_result.scalar_one_or_none() is not None

    conv_count = await session.execute(select(func.count()).select_from(Conversation))
    contact_count = await session.execute(select(func.count()).select_from(Contact))
    has_data = (conv_count.scalar_one() > 0) or (contact_count.scalar_one() > 0)

    if has_profile or has_data:
        repaired_pref = await _mark_onboarding_completed(session)
        return {
            "completed": True,
            "completed_at": repaired_pref.updated_at.isoformat()
            if repaired_pref.updated_at
            else None,
        }

    return {"completed": False, "completed_at": None}


@router.post("/onboarding-complete")
async def set_onboarding_complete(session: AsyncSession = Depends(get_session)):
    """
    Mark onboarding as completed.

    This is called when the user finishes the onboarding wizard.
    """
    pref = await _mark_onboarding_completed(session)

    return {
        "completed": True,
        "completed_at": pref.updated_at.isoformat() if pref.updated_at else datetime.now(UTC).isoformat(),
    }



# ============================================================
# US-006 : Circuit breaker LLM - Endpoint statut
# ============================================================


@router.get("/llm/status")
async def get_llm_status():
    """Retourne l'état du circuit breaker pour chaque provider LLM.

    US-006 : Permet au frontend d'afficher un bandeau
    "Mode dégradé - modèle de secours actif" si un provider est down.

    Returns:
        - providers: dict des états par provider (closed/open/half-open)
        - degraded: bool indiquant si au moins un provider est en mode dégradé
        - degraded_message: message localisé pour le frontend (ou null)
    """
    from app.services.circuit_breaker import get_circuit_breaker

    cb = get_circuit_breaker()
    statuses = cb.get_all_statuses()
    degraded_msg = cb.get_degraded_message()

    return {
        "providers": statuses,
        "degraded": degraded_msg is not None,
        "degraded_message": degraded_msg,
    }


@router.post("/llm/circuit-breaker/reset")
async def reset_circuit_breaker(provider: str | None = None):
    """Reset le circuit breaker pour un provider (ou tous).

    US-006 : Permet a l'utilisateur de forcer la reconnexion
    a un provider marqué comme down.

    Args:
        provider: Nom du provider a reset (ou None pour tous).
    """
    from app.services.circuit_breaker import get_circuit_breaker

    cb = get_circuit_breaker()
    cb.reset(provider)

    return {
        "reset": provider or "all",
        "statuses": cb.get_all_statuses(),
    }
