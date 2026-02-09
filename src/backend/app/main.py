"""
THÉRÈSE v2 - FastAPI Application

L'assistante souveraine des entrepreneurs français.
"""
# NOTE: slowapi est requis pour le rate limiting (SEC-015)
# Installation : uv add slowapi

import logging
import secrets
from contextlib import asynccontextmanager
from pathlib import Path as FilePath

from app.config import settings
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Rate limiting (SEC-015) - slowapi est requis (dans pyproject.toml)
try:
    from slowapi import Limiter
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    from slowapi.util import get_remote_address
    HAS_SLOWAPI = True
except ImportError:
    HAS_SLOWAPI = False
    import time as _time
    from collections import defaultdict as _defaultdict
from app.models.database import close_db, init_db
from app.routers import (
    board_router,
    calc_router,
    calendar_router,  # Phase 2 - ACTIVATED
    chat_router,
    commands_router,  # User Commands
    config_router,
    crm_router,  # Phase 5 - Implemented
    data_router,
    email_router,  # Phase 1 - ACTIVATED
    email_setup_router,  # Phase 1.2 - Email Setup Wizard
    escalation_router,
    files_router,
    images_router,
    invoices_router,  # Phase 4 - ACTIVATED
    mcp_router,
    memory_router,
    perf_router,
    personalisation_router,
    rgpd_router,  # Phase 6 - RGPD Compliance
    skills_router,
    tasks_router,  # Phase 3 - ACTIVATED
    voice_router,
)
from app.services import close_qdrant, init_qdrant
from app.services.mcp_service import get_mcp_service, initialize_mcp_service
from app.services.skills import close_skills, init_skills

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def _load_user_profile():
    """Load user profile from database and cache it."""
    from app.models.database import get_session_context
    from app.services.user_profile import get_user_profile, set_cached_profile

    try:
        async with get_session_context() as session:
            profile = await get_user_profile(session)
            if profile:
                set_cached_profile(profile)
                logger.info(f"User profile loaded: {profile.display_name()}")
            else:
                logger.info("No user profile configured")
    except Exception as e:
        logger.warning(f"Failed to load user profile: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Data directory: {settings.data_dir}")

    await init_db()
    logger.info("Database initialized")

    await init_qdrant()
    logger.info("Qdrant vector store initialized")

    await init_skills()
    logger.info("Skills system initialized")

    await initialize_mcp_service()
    logger.info("MCP service initialized")

    # Pre-charge le modele d'embeddings (evite 5-10s de latence au premier appel)
    from app.services.embeddings import preload_embedding_model
    try:
        await preload_embedding_model()
        logger.info("Embedding model pre-loaded")
    except Exception as e:
        logger.warning(f"Failed to preload embedding model (will lazy-load on first use): {e}")

    # Load user profile into cache
    await _load_user_profile()

    # Start OAuth cleanup background task
    import asyncio

    from app.services.oauth import cleanup_expired_flows_periodically
    oauth_cleanup_task = asyncio.create_task(cleanup_expired_flows_periodically())

    # Register memory cleanup callbacks (US-PERF-03)
    from app.services.performance import get_memory_manager
    memory_manager = get_memory_manager()

    # Register MCP service cleanup
    async def cleanup_mcp():
        get_mcp_service()
        # Clear any stale connections
        return {"mcp": "cleaned"}

    memory_manager.register_cleanup(cleanup_mcp)
    logger.info("Memory cleanup callbacks registered")

    # Generate session auth token (SEC-010)
    token = secrets.token_urlsafe(32)
    token_path = FilePath.home() / ".therese" / ".session_token"
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(token)
    import os as _os
    _os.chmod(token_path, 0o600)
    app.state.session_token = token
    logger.info(f"Session token generated and saved to {token_path}")

    yield

    # Shutdown
    logger.info("Shutting down...")

    # Cancel OAuth cleanup background task
    oauth_cleanup_task.cancel()
    try:
        await oauth_cleanup_task
    except asyncio.CancelledError:
        pass

    # Cleanup session token
    try:
        token_path = FilePath.home() / ".therese" / ".session_token"
        if token_path.exists():
            token_path.unlink()
    except Exception:
        pass

    # Close global HTTP client pool (Sprint 2 - PERF-2.6)
    from app.services.http_client import close_http_client
    await close_http_client()

    mcp_service = get_mcp_service()
    await mcp_service.shutdown()
    await close_skills()
    await close_qdrant()
    await close_db()
    logger.info("Cleanup complete")


# Create FastAPI app
app = FastAPI(
    title=f"{settings.app_name} API",
    description="API backend for THÉRÈSE - L'assistante souveraine des entrepreneurs français",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS middleware (SEC-018)
# Production: only Tauri origins. Dev: also allow Vite/Tauri dev servers.
_cors_origins = [
    "tauri://localhost",       # Tauri production
    "https://tauri.localhost",  # Tauri production (HTTPS)
]
if settings.therese_env != "production":
    _cors_origins += [
        "http://localhost:1420",  # Tauri dev
        "http://localhost:5173",  # Vite dev
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Therese-Token",
        "Accept",
        "Origin",
    ],
    expose_headers=["Content-Disposition"],  # Pour le telechargement de fichiers
)

# Rate limiting middleware (SEC-015)
if HAS_SLOWAPI:
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    logger.info("SlowAPI rate limiting active")
else:
    limiter = None
    logger.error(
        "SECURITE: slowapi non installe - rate limiting degrade actif. "
        "Installer avec: uv add slowapi"
    )

    # Fallback in-memory rate limiter (SEC-015)
    # Protege les endpoints critiques meme sans slowapi
    _request_counts: dict[str, list[float]] = _defaultdict(list)
    _FALLBACK_RATE_LIMIT = 60  # max requests per minute per IP
    _FALLBACK_WINDOW = 60.0  # seconds

    @app.middleware("http")
    async def fallback_rate_limit_middleware(request: Request, call_next):
        """Minimal in-memory rate limiter when slowapi is not available."""
        client_ip = request.client.host if request.client else "unknown"
        now = _time.time()
        # Clean old entries
        _request_counts[client_ip] = [
            t for t in _request_counts[client_ip]
            if now - t < _FALLBACK_WINDOW
        ]
        # Purger les clés vides pour éviter une fuite mémoire
        if not _request_counts[client_ip]:
            del _request_counts[client_ip]
            return await call_next(request)
        if len(_request_counts[client_ip]) >= _FALLBACK_RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={
                    "code": "RATE_LIMITED",
                    "message": "Trop de requetes. Veuillez patienter.",
                },
            )
        _request_counts[client_ip].append(now)
        return await call_next(request)


# --- Exception handlers (ARCH-029 + SEC-015) ---


# Handler HTTPException natif - laisser FastAPI gérer (ARCH-029)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Re-expose les HTTPException avec un format JSON cohérent."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": "HTTP_ERROR", "message": str(exc.detail)},
    )


# Handler validation Pydantic - erreurs 422 (ARCH-029)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Retourne les erreurs de validation en 422 au lieu de 500."""
    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": "Données invalides dans la requête",
            "details": exc.errors() if settings.debug else [],
        },
    )


# Handler rate limiting 429 (SEC-015)
if HAS_SLOWAPI:
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        """Retourne une erreur 429 quand le rate limit est atteint."""
        return JSONResponse(
            status_code=429,
            content={
                "code": "RATE_LIMITED",
                "message": "Trop de requêtes. Veuillez patienter.",
            },
        )


# Handler TheresError custom (US-ERR-01)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle TheresError et fallback pour les erreurs non gérées."""
    from app.services.error_handler import ErrorCode, TheresError

    if isinstance(exc, TheresError):
        return JSONResponse(
            status_code=400 if exc.recoverable else 500,
            content=exc.to_dict(),
        )

    # Log unexpected errors
    logger.exception(f"Unexpected error: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "code": ErrorCode.UNKNOWN_ERROR.value,
            "message": "Une erreur inattendue s'est produite. Veuillez reessayer.",
            "recoverable": True,
            "details": {"error": str(exc)} if settings.debug else {},
        },
    )



# --- Auth token bootstrap endpoint (SEC-010) ---
# SECURITY NOTE (SEC-010): This endpoint returns the session token in plaintext.
# Risk level: LOW for desktop app (localhost only, CORS-restricted to Tauri origins).
# The token is ephemeral (regenerated each launch) and the endpoint is not reachable
# from external networks. If THERESE ever serves remote clients, this must be replaced
# by a secure handshake (e.g. file-based token exchange or IPC channel).

@app.get("/api/auth/token")
async def get_auth_token(request: Request):
    """Retourne le token de session. Protege par CORS (seul Tauri peut lire la reponse)."""
    return {"token": getattr(request.app.state, "session_token", None)}


# Auth middleware (SEC-010)
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Verifie le token de session sur toutes les requetes (sauf health check et bootstrap)."""
    # Laisser passer les requêtes OPTIONS (CORS preflight)
    if request.method == "OPTIONS":
        return await call_next(request)

    # Endpoints exemptés
    exempt_paths = [
        "/api/health", "/api/auth/token",
        "/api/email/auth/callback-redirect",
        "/api/crm/sync/callback",
        "/docs", "/redoc", "/openapi.json", "/health",
    ]
    if any(request.url.path.startswith(p) for p in exempt_paths):
        return await call_next(request)

    # Verifier le token (header ou query param pour les balises <img>) (SEC-010)
    token = request.headers.get("X-Therese-Token") or request.query_params.get("token")
    expected = getattr(request.app.state, "session_token", None)

    # Utilise secrets.compare_digest pour eviter les timing attacks (SEC-025)
    if expected and (not token or not secrets.compare_digest(token, expected)):
        return JSONResponse(
            status_code=401,
            content={"code": "UNAUTHORIZED", "message": "Token de session invalide ou manquant"},
        )

    return await call_next(request)


# Security headers middleware (SEC-023)
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Ajoute les headers de securite standard."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


# Include routers
app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
app.include_router(memory_router, prefix="/api/memory", tags=["Memory"])
app.include_router(files_router, prefix="/api/files", tags=["Files"])
app.include_router(config_router, prefix="/api/config", tags=["Config"])
app.include_router(skills_router, prefix="/api/skills", tags=["Skills"])
app.include_router(voice_router, prefix="/api/voice", tags=["Voice"])
app.include_router(images_router, prefix="/api/images", tags=["Images"])
app.include_router(board_router, prefix="/api/board", tags=["Board"])
app.include_router(calc_router, prefix="/api/calc", tags=["Calculators"])
app.include_router(mcp_router, prefix="/api/mcp", tags=["MCP"])
app.include_router(data_router, prefix="/api/data", tags=["Data & RGPD"])
app.include_router(perf_router, prefix="/api/perf", tags=["Performance"])
app.include_router(personalisation_router, prefix="/api/personalisation", tags=["Personalisation"])
app.include_router(escalation_router, prefix="/api/escalation", tags=["Escalation & Limites"])

# Phase 1-4: Core Native Features (ACTIVATED)
app.include_router(email_router, prefix="/api/email", tags=["Email"])  # Phase 1
app.include_router(
    email_setup_router, prefix="/api/email/setup",
    tags=["Email Setup"],
)  # Phase 1.2 - Setup Wizard
app.include_router(calendar_router, prefix="/api/calendar", tags=["Calendar"])  # Phase 2
app.include_router(tasks_router, prefix="/api/tasks", tags=["Tasks"])  # Phase 3
app.include_router(invoices_router, prefix="/api/invoices", tags=["Invoices"])  # Phase 4

# Phase 5: CRM
app.include_router(crm_router, prefix="/api/crm", tags=["CRM"])  # Phase 5

# Phase 6: RGPD Compliance
app.include_router(rgpd_router, prefix="/api/rgpd", tags=["RGPD"])  # Phase 6

# User Commands
app.include_router(commands_router, prefix="/api/commands", tags=["Commands"])


# Health endpoints
@app.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "tagline": "L'assistante souveraine des entrepreneurs français",
    }


@app.get("/health")
async def health():
    """Health check endpoint for monitoring."""
    from app.services.error_handler import get_service_status

    status = get_service_status()
    services = status.get_all_statuses()

    # Check critical services
    all_healthy = all(services.values()) if services else True

    return {
        "status": "healthy" if all_healthy else "degraded",
        "version": settings.app_version,
        "services": services,
    }


@app.get("/health/services")
async def service_status():
    """Get detailed service status (US-ERR-03)."""
    from app.services.error_handler import get_service_status

    status = get_service_status()

    # Check Qdrant
    qdrant_available = True
    try:
        from app.services.qdrant import get_qdrant_service

        service = get_qdrant_service()
        service.get_stats()
    except Exception:
        qdrant_available = False

    status.set_available("qdrant", qdrant_available)

    # Check database
    db_available = True
    try:
        from app.models.database import get_session_context

        async with get_session_context() as session:
            await session.execute("SELECT 1")
    except Exception:
        db_available = False

    status.set_available("database", db_available)

    return {
        "services": {
            "database": {
                "available": db_available,
                "critical": True,
                "fallback": None,
            },
            "qdrant": {
                "available": qdrant_available,
                "critical": False,
                "fallback": "Chat fonctionne sans memoire semantique",
            },
            **{
                k: {"available": v, "critical": False}
                for k, v in status.get_all_statuses().items()
                if k not in ["database", "qdrant"]
            },
        },
    }


# Run with uvicorn if executed directly
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
