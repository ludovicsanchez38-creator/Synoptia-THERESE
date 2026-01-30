"""
THÉRÈSE v2 - Email Setup Router

API endpoints pour le wizard de configuration email.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_session
from app.services.email_setup_assistant import EmailSetupAssistant, SetupStatus, ValidationResult, GoogleCredentials


router = APIRouter()


# Schemas
class ValidateCredentialsRequest(BaseModel):
    client_id: str
    client_secret: str


class ValidateCredentialsResponse(BaseModel):
    client_id: ValidationResult
    client_secret: ValidationResult
    all_valid: bool


class GenerateGuideRequest(BaseModel):
    provider: str
    has_project: bool


class GenerateGuideResponse(BaseModel):
    message: str


# Endpoints
@router.get("/status")
async def get_setup_status(
    session: AsyncSession = Depends(get_session),
) -> SetupStatus:
    """Récupère le status de configuration email actuelle."""
    return await EmailSetupAssistant.detect_existing_credentials(session)


@router.post("/validate")
async def validate_credentials(request: ValidateCredentialsRequest) -> ValidateCredentialsResponse:
    """Valide les credentials Gmail OAuth."""
    results = await EmailSetupAssistant.validate_credentials(
        request.client_id,
        request.client_secret
    )

    all_valid = all(r.valid for r in results.values())

    return ValidateCredentialsResponse(
        client_id=results['client_id'],
        client_secret=results['client_secret'],
        all_valid=all_valid
    )


@router.post("/guide")
async def generate_guide(request: GenerateGuideRequest) -> GenerateGuideResponse:
    """Génère un guide personnalisé selon le contexte."""
    message = await EmailSetupAssistant.generate_guide_message(
        request.provider,
        request.has_project
    )

    return GenerateGuideResponse(message=message)


@router.post("/detect-provider")
async def detect_provider(email: str) -> dict:
    """Détecte le provider SMTP depuis l'email."""
    provider = EmailSetupAssistant.suggest_provider(email)
    return {
        "email": email,
        "provider": provider,
        "suggested": provider is not None
    }
