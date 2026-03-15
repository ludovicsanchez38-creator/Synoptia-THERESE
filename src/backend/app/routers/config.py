"""
THÉRÈSE v2 - Config Router

Endpoints for application configuration.
"""

import json
import logging
import os
from datetime import UTC, datetime

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
    UserProfileResponse,
    UserProfileUpdate,
    WorkingDirectoryResponse,
    WorkingDirectoryUpdate,
)
from app.services.audit import AuditAction, log_activity
from app.services.encryption import decrypt_value, encrypt_value, is_value_encrypted
from app.services.http_client import get_http_client
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

logger = logging.getLogger(__name__)

router = APIRouter()

# Track startup time
_startup_time = datetime.now(UTC)


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
    except Exception:
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
    except Exception:
        pass

    corrupted_keys: list[str] = []

    # Check API keys from environment (updated dynamically) or DB
    has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY") or settings.anthropic_api_key)
    has_mistral = bool(os.environ.get("MISTRAL_API_KEY") or settings.mistral_api_key)
    has_openai = bool(os.environ.get("OPENAI_API_KEY"))
    has_gemini = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    has_groq = bool(os.environ.get("GROQ_API_KEY"))
    has_grok = bool(os.environ.get("XAI_API_KEY"))

    # BUG-051 : vérifier que les clés DB sont déchiffrables (pas juste "is not None")
    key_checks = {
        "anthropic": ("anthropic_api_key", has_anthropic),
        "mistral": ("mistral_api_key", has_mistral),
        "openai": ("openai_api_key", has_openai),
        "gemini": ("gemini_api_key", has_gemini),
        "groq": ("groq_api_key", has_groq),
        "grok": ("grok_api_key", has_grok),
    }
    for provider_id, (db_key, has_env) in key_checks.items():
        if not has_env:
            has_db, is_corrupted = await _check_key_decryptable(session, db_key)
            if is_corrupted:
                corrupted_keys.append(provider_id)
            # has_key = True seulement si la clé existe ET est lisible
            if provider_id == "anthropic":
                has_anthropic = has_db and not is_corrupted
            elif provider_id == "mistral":
                has_mistral = has_db and not is_corrupted
            elif provider_id == "openai":
                has_openai = has_db and not is_corrupted
            elif provider_id == "gemini":
                has_gemini = has_db and not is_corrupted
            elif provider_id == "groq":
                has_groq = has_db and not is_corrupted
            elif provider_id == "grok":
                has_grok = has_db and not is_corrupted

    has_openrouter = bool(os.environ.get("OPENROUTER_API_KEY"))
    if not has_openrouter:
        has_db, is_corrupted = await _check_key_decryptable(session, "openrouter_api_key")
        if is_corrupted:
            corrupted_keys.append("openrouter")
        has_openrouter = has_db and not is_corrupted

    # Check for image-specific API keys
    has_openai_image = bool(os.environ.get("OPENAI_IMAGE_API_KEY"))
    if not has_openai_image:
        has_db, is_corrupted = await _check_key_decryptable(session, "openai_image_api_key")
        if is_corrupted:
            corrupted_keys.append("openai_image")
        has_openai_image = has_db and not is_corrupted

    has_gemini_image = bool(os.environ.get("GEMINI_IMAGE_API_KEY"))
    if not has_gemini_image:
        has_db, is_corrupted = await _check_key_decryptable(session, "gemini_image_api_key")
        if is_corrupted:
            corrupted_keys.append("gemini_image")
        has_gemini_image = has_db and not is_corrupted

    has_fal = bool(os.environ.get("FAL_API_KEY"))
    if not has_fal:
        has_db, is_corrupted = await _check_key_decryptable(session, "fal_api_key")
        if is_corrupted:
            corrupted_keys.append("fal")
        has_fal = has_db and not is_corrupted

    has_brave = bool(os.environ.get("BRAVE_API_KEY"))
    if not has_brave:
        has_db, is_corrupted = await _check_key_decryptable(session, "brave_api_key")
        if is_corrupted:
            corrupted_keys.append("brave")
        has_brave = has_db and not is_corrupted

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
    elif provider == "gemini" and not key.startswith("AIza"):
        raise HTTPException(
            status_code=400,
            detail="La clé API Gemini doit commencer par 'AIza'"
        )
    elif provider == "gemini_image" and not key.startswith("AIza"):
        raise HTTPException(
            status_code=400,
            detail="La clé API Gemini (Image) doit commencer par 'AIza'"
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
    from app.services.llm import invalidate_api_key_cache
    invalidate_api_key_cache()

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
    )

    saved_profile = await set_user_profile(session, profile)

    # Update cache for LLM service
    set_cached_profile(saved_profile)

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


@router.get("/llm", response_model=LLMConfigResponse)
async def get_llm_config(session: AsyncSession = Depends(get_session)):
    """Get current LLM configuration."""
    from app.services.llm import get_llm_service

    service = get_llm_service()
    config = service.config

    # Get available models for the provider
    available_models = []
    if config.provider.value == "anthropic":
        # Claude 4.5/4.6 series (février 2026)
        available_models = [
            "claude-opus-4-6",               # Flagship, best overall
            "claude-sonnet-4-6",             # Best coding model
            "claude-haiku-4-5-20251001",     # Fast & cost-efficient
        ]
    elif config.provider.value == "openai":
        # GPT-5 series (février 2026)
        available_models = [
            "gpt-5.2",           # Latest flagship
            "gpt-5",             # Previous flagship
            "gpt-4.1",           # Coding specialist
            "o3",                # Reasoning model
            "o3-mini",           # Fast reasoning
        ]
    elif config.provider.value == "gemini":
        # Gemini 3 + 2.5 series (janvier 2026)
        available_models = [
            "gemini-3.1-pro-preview",   # Latest flagship
            "gemini-3-flash-preview", # Fast Gemini 3
            "gemini-2.5-pro",         # High capability
            "gemini-3.1-flash-lite-preview",  # Ultra-rapide, économique
            "gemini-2.5-flash",       # Fast & capable
        ]
    elif config.provider.value == "mistral":
        # Mistral latest (janvier 2026)
        available_models = [
            "mistral-large-latest",   # Top-tier
            "codestral-latest",       # Coding specialist
            "devstral-small-latest",  # Dev tasks
            "mistral-small-latest",   # Fast & efficient
        ]
    elif config.provider.value == "grok":
        # Grok 4 series (février 2026)
        available_models = [
            "grok-4",                       # Flagship
            "grok-4-1-fast-non-reasoning",  # Fast variant
            "grok-3-beta",                  # Previous gen
        ]
    elif config.provider.value == "openrouter":
        # OpenRouter : accès unifié à 200+ modèles
        available_models = [
            "anthropic/claude-sonnet-4-6",     # Recommandé
            "anthropic/claude-opus-4-6",       # Premium
            "openai/gpt-5.2",                  # GPT-5.2
            "google/gemini-3.1-pro",             # Gemini 3.1 Pro
            "google/gemini-3.1-flash-lite-preview",  # Ultra-rapide
            "meta-llama/llama-4-maverick",     # Open Source
        ]
    elif config.provider.value == "ollama":
        # F-14 : lister les modèles Ollama installés localement
        try:
            client = await get_http_client()
            resp = await client.get(f"{settings.ollama_base_url}/api/tags", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                available_models = [
                    m.get("name", "") for m in data.get("models", [])
                    if m.get("name") and _categorize_ollama_model(m["name"]) == "chat"
                ]
        except Exception:
            # Ollama non disponible - liste vide, pas d'erreur
            available_models = []

    return LLMConfigResponse(
        provider=config.provider.value,
        model=config.model,
        available_models=available_models,
    )


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

    # Create new config
    config = LLMConfig(
        provider=provider,
        model=request.model,
        api_key=api_key,
        base_url=base_url,
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

    await session.commit()

    # Récupérer la liste des modèles disponibles pour le provider
    post_available_models: list[str] = []
    if provider == LLMProvider.OLLAMA:
        try:
            client = await get_http_client()
            resp = await client.get(f"{settings.ollama_base_url}/api/tags", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                post_available_models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
        except Exception:
            pass

    return LLMConfigResponse(
        provider=request.provider,
        model=request.model,
        available_models=post_available_models,
    )


# ============================================================
# Ollama Endpoints
# ============================================================


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

        data = response.json()
        models = [
            OllamaModelInfo(
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

    # Si pas de flag mais DB contient des donnees -> onboarding deja fait
    # (cas d'une DB restauree depuis un backup anterieur au flag)
    conv_count = await session.execute(select(func.count()).select_from(Conversation))
    contact_count = await session.execute(select(func.count()).select_from(Contact))
    has_data = (conv_count.scalar_one() > 0) or (contact_count.scalar_one() > 0)

    if has_data:
        new_pref = Preference(key="onboarding_completed", value="true", category="system")
        session.add(new_pref)
        await session.commit()
        return {"completed": True, "completed_at": None}

    return {"completed": False, "completed_at": None}


@router.post("/onboarding-complete")
async def set_onboarding_complete(session: AsyncSession = Depends(get_session)):
    """
    Mark onboarding as completed.

    This is called when the user finishes the onboarding wizard.
    """
    # Get or create preference
    result = await session.execute(
        select(Preference).where(Preference.key == "onboarding_completed")
    )
    pref = result.scalar_one_or_none()

    if pref:
        pref.value = "true"
        pref.updated_at = datetime.now(UTC)
    else:
        pref = Preference(
            key="onboarding_completed",
            value="true",
            category="system",
        )
        session.add(pref)

    await session.commit()

    return {
        "completed": True,
        "completed_at": pref.updated_at.isoformat() if pref.updated_at else datetime.now(UTC).isoformat(),
    }
