"""
THÉRÈSE v2 - Email Setup Assistant

Agent intelligent pour guider l'utilisateur dans la configuration email.
"""

import re
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select


@dataclass
class ValidationResult:
    """Résultat de validation des credentials."""
    valid: bool
    field: str
    message: str


@dataclass
class GoogleCredentials:
    """Credentials Google OAuth (depuis MCP ou saisie manuelle).

    B-034 : `client_secret` reste dans le contrat, mais TOUJOURS vide. Le
    secret ne traverse aucune réponse HTTP ; l'écran sait seulement qu'il
    existe (`has_client_secret`), et l'autorisation le retrouve côté serveur.
    Le champ n'est pas retiré à dessein : le supprimer ferait partir un corps
    sans `client_secret` vers /api/email/auth/initiate, donc un 422.
    """
    client_id: str
    client_secret: str = ""
    source: str = "mcp"  # 'mcp' ou 'manual'
    has_client_secret: bool = False


def identifiants_google_mcp() -> tuple[str, str] | None:
    """Les identifiants OAuth Google rangés dans un serveur MCP, déchiffrés.

    Reste côté serveur : c'est le pendant, pour la mise en route e-mail, de ce
    que fait déjà la synchronisation Google Sheets (routers/crm.py).
    """
    from app.services.encryption import decrypt_value, is_value_encrypted

    try:
        from app.services.mcp_service import get_mcp_service

        mcp_service = get_mcp_service()
        for server_id, server in mcp_service.servers.items():
            if 'google' in server.name.lower() or 'google-workspace' in server_id:
                env = server.env or {}
                client_id = env.get('GOOGLE_OAUTH_CLIENT_ID', '')
                client_secret = env.get('GOOGLE_OAUTH_CLIENT_SECRET', '')

                if client_id and is_value_encrypted(client_id):
                    client_id = decrypt_value(client_id)
                if client_secret and is_value_encrypted(client_secret):
                    client_secret = decrypt_value(client_secret)

                if client_id and client_secret:
                    return client_id, client_secret
    except Exception:
        # MCP service not available or no Google server configured
        pass
    return None


@dataclass
class SetupStatus:
    """Status de la configuration email."""
    has_gmail: bool
    has_smtp: bool
    gmail_email: str | None = None
    smtp_email: str | None = None
    # Credentials Google depuis MCP
    google_credentials: GoogleCredentials | None = None


class EmailSetupAssistant:
    """Agent intelligent pour setup email."""

    # Patterns de validation
    CLIENT_ID_PATTERN = re.compile(r'^[0-9]+-[a-z0-9]+\.apps\.googleusercontent\.com$')
    CLIENT_SECRET_PATTERN = re.compile(r'^GOCSPX-[A-Za-z0-9_-]+$')

    # Providers SMTP connus
    SMTP_PROVIDERS = {
        'gmail.com': 'gmail',
        'ovh.net': 'ovh',
        'ovh.com': 'ovh',
        'gandi.net': 'gandi',
        'outlook.com': 'outlook',
        'hotmail.com': 'outlook',
        'yahoo.com': 'yahoo',
    }

    @staticmethod
    async def detect_existing_credentials(session: AsyncSession) -> SetupStatus:
        """Détecte si des credentials email existent déjà."""
        from app.models.entities import EmailAccount

        # Check Gmail OAuth
        stmt = select(EmailAccount)
        result = await session.execute(stmt)
        accounts = result.scalars().all()

        gmail_account = next((acc for acc in accounts if acc.provider == 'gmail'), None)
        smtp_account = next((acc for acc in accounts if acc.provider == 'smtp'), None)

        # Check if Google OAuth credentials exist in MCP servers.
        # B-034 : le client_id n'est pas un secret (il voyage dans l'URL
        # d'autorisation Google) ; le client_secret, si, et il reste ici.
        google_creds = None
        identifiants = identifiants_google_mcp()
        if identifiants is not None:
            client_id, _ = identifiants
            google_creds = GoogleCredentials(
                client_id=client_id,
                client_secret="",
                source='mcp',
                has_client_secret=True,
            )

        return SetupStatus(
            has_gmail=gmail_account is not None,
            has_smtp=smtp_account is not None,
            gmail_email=gmail_account.email if gmail_account else None,
            smtp_email=smtp_account.email if smtp_account else None,
            google_credentials=google_creds,
        )

    @staticmethod
    def suggest_provider(email: str) -> str | None:
        """Détecte le provider SMTP depuis l'email."""
        if not email or '@' not in email:
            return None

        domain = email.split('@')[1].lower()
        return EmailSetupAssistant.SMTP_PROVIDERS.get(domain, 'smtp')

    @staticmethod
    def validate_client_id(client_id: str) -> ValidationResult:
        """Valide le format du Client ID Google."""
        if not client_id:
            return ValidationResult(
                valid=False,
                field='client_id',
                message='Le Client ID est requis'
            )

        if not EmailSetupAssistant.CLIENT_ID_PATTERN.match(client_id):
            return ValidationResult(
                valid=False,
                field='client_id',
                message='Format invalide. Doit se terminer par .apps.googleusercontent.com'
            )

        return ValidationResult(
            valid=True,
            field='client_id',
            message='Format valide'
        )

    @staticmethod
    def validate_client_secret(client_secret: str) -> ValidationResult:
        """Valide le format du Client Secret Google."""
        if not client_secret:
            return ValidationResult(
                valid=False,
                field='client_secret',
                message='Le Client Secret est requis'
            )

        if not EmailSetupAssistant.CLIENT_SECRET_PATTERN.match(client_secret):
            return ValidationResult(
                valid=False,
                field='client_secret',
                message='Format invalide. Doit commencer par GOCSPX-'
            )

        return ValidationResult(
            valid=True,
            field='client_secret',
            message='Format valide'
        )

    @staticmethod
    async def validate_credentials(client_id: str, client_secret: str) -> dict[str, ValidationResult]:
        """Valide les deux credentials."""
        return {
            'client_id': EmailSetupAssistant.validate_client_id(client_id),
            'client_secret': EmailSetupAssistant.validate_client_secret(client_secret),
        }

    @staticmethod
    async def generate_guide_message(provider: str, has_project: bool) -> str:
        """Génère un message de guide personnalisé."""
        if provider == 'gmail':
            if has_project:
                return """Super ! 🎉

Tu as déjà un projet Google Cloud. Voici ce qu'il te faut :

1. Va sur [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Sélectionne ton projet
3. Clique sur "Créer des identifiants" → "ID client OAuth 2.0"
4. Type d'application : **Application de bureau**
5. Copie le **Client ID** et le **Client Secret**

Entre-les dans l'étape suivante !"""
            else:
                return """Pas de souci ! 👍

Je vais te guider pour créer un projet Google Cloud :

1. Va sur [Google Cloud Console](https://console.cloud.google.com/)
2. Crée un nouveau projet (bouton en haut à gauche)
3. Nom du projet : "THÉRÈSE Email" (ou autre)
4. Active l'API Gmail (Bibliothèque → Gmail API → Activer)
5. Va dans "Identifiants" → "Créer des identifiants"
6. Choisis "ID client OAuth 2.0"
7. Type : **Application de bureau**
8. Copie le Client ID et Client Secret

⏱️ Environ 5 minutes. Prends ton temps !"""

        return "Guide non disponible pour ce provider."
