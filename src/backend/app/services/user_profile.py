"""
THÉRÈSE v2 - User Profile Service

Manages user identity and profile for personalized interactions.
Fixes the bug where THÉRÈSE calls the user "Pierre" instead of their real name.
"""

import json
import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from app.models.entities import Preference
from app.services.encryption import decrypt_value, encrypt_value, is_value_encrypted
from app.services.qdrant import get_qdrant_service
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    """User profile data structure."""

    name: str                      # "Ludovic Sanchez"
    nickname: str = ""             # "Ludo"
    company: str = ""              # "Synoptïa"
    role: str = ""                 # "Entrepreneur IA"
    context: str = ""              # Extended context from THERESE.md
    email: str = ""                # Contact email
    location: str = ""             # "Manosque, France"
    address: str = ""              # "294 Montee des Genets, 04100 Manosque"
    siren: str = ""                # "991 606 781"
    tva_intra: str = ""            # "FR 08 991 606 781"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            nickname=data.get("nickname", ""),
            company=data.get("company", ""),
            role=data.get("role", ""),
            context=data.get("context", ""),
            email=data.get("email", ""),
            location=data.get("location", ""),
            address=data.get("address", ""),
            siren=data.get("siren", ""),
            tva_intra=data.get("tva_intra", ""),
        )

    def display_name(self) -> str:
        """Get display name (nickname or full name)."""
        return self.nickname if self.nickname else self.name.split()[0] if self.name else "Utilisateur"

    def format_for_llm(self) -> str:
        """Format profile for injection into LLM system prompt."""
        parts = []

        # Main identity
        if self.name:
            parts.append(f"Tu assistes **{self.name}**")
            if self.nickname:
                parts.append(f" (appelle-le **{self.nickname}**)")
            parts.append(".")

        # Role and company
        if self.role or self.company:
            role_parts = []
            if self.role:
                role_parts.append(self.role)
            if self.company:
                role_parts.append(f"chez {self.company}")
            parts.append(f" {' '.join(role_parts)}.")

        # Location
        if self.location:
            parts.append(f" Basé à {self.location}.")

        # Extended context (truncated if too long)
        if self.context:
            # Limit context to ~2000 chars to not overwhelm the prompt
            context_text = self.context[:2000]
            if len(self.context) > 2000:
                context_text += "..."
            parts.append(f"\n\n### Contexte utilisateur:\n{context_text}")

        return "".join(parts) if parts else ""


# Preference keys
PROFILE_KEY = "user_profile"
PROFILE_CATEGORY = "identity"


async def get_user_profile(
    session: AsyncSession,
    *,
    allow_decrypt: bool = True,
) -> UserProfile | None:
    """
    Retrieve user profile from database.

    Returns None if no profile is configured.
    The profile is decrypted automatically if stored encrypted (RGPD compliance).
    """
    try:
        result = await session.execute(
            select(Preference).where(
                Preference.key == PROFILE_KEY,
                Preference.category == PROFILE_CATEGORY,
            )
        )
        pref = result.scalar_one_or_none()

        if not pref or not pref.value:
            return None

        # Déchiffrer si le profil est chiffré (migration transparente)
        value = pref.value
        if is_value_encrypted(value):
            if not allow_decrypt:
                # Evite de déclencher un prompt trousseau bloquant pendant le startup.
                logger.info("User profile preload skipped: encrypted profile requires keychain access")
                return None
            try:
                value = decrypt_value(value)
            except Exception as e:
                logger.error(f"Failed to decrypt user profile: {e}")
                return None

        data = json.loads(value)
        return UserProfile.from_dict(data)

    except Exception as e:
        logger.error(f"Failed to load user profile: {e}")
        return None


async def set_user_profile(
    session: AsyncSession,
    profile: UserProfile,
    embed_in_qdrant: bool = True,
) -> UserProfile:
    """
    Save user profile to database and optionally embed in Qdrant.

    Args:
        session: Database session
        profile: UserProfile to save
        embed_in_qdrant: Whether to create a searchable embedding

    Returns:
        The saved profile
    """
    from datetime import UTC, datetime

    try:
        # Get or create preference
        result = await session.execute(
            select(Preference).where(Preference.key == PROFILE_KEY)
        )
        pref = result.scalar_one_or_none()

        # Chiffrer le profil avant stockage (RGPD - données personnelles)
        value_json = json.dumps(profile.to_dict(), ensure_ascii=False)
        encrypted_value = encrypt_value(value_json)

        if pref:
            pref.value = encrypted_value
            pref.category = PROFILE_CATEGORY
            pref.updated_at = datetime.now(UTC)
        else:
            pref = Preference(
                key=PROFILE_KEY,
                value=encrypted_value,
                category=PROFILE_CATEGORY,
            )
            session.add(pref)

        await session.commit()

        # Embed in Qdrant for semantic search
        if embed_in_qdrant:
            await _embed_profile(profile)

        logger.info(f"User profile saved: {profile.name}")
        return profile

    except Exception as e:
        logger.error(f"Failed to save user profile: {e}")
        await session.rollback()
        raise


async def _embed_profile(profile: UserProfile) -> None:
    """
    Embed user profile in Qdrant for semantic search.

    This allows the memory system to find the owner's identity
    when questions like "Qui suis-je?" are asked.
    """
    try:
        qdrant = get_qdrant_service()

        # Create a rich text representation for embedding
        text_parts = [
            f"Propriétaire de THÉRÈSE: {profile.name}",
        ]

        if profile.nickname:
            text_parts.append(f"Surnom: {profile.nickname}")
        if profile.company:
            text_parts.append(f"Entreprise: {profile.company}")
        if profile.role:
            text_parts.append(f"Rôle: {profile.role}")
        if profile.email:
            text_parts.append(f"Email: {profile.email}")
        if profile.location:
            text_parts.append(f"Localisation: {profile.location}")

        # Add some searchable context
        text_parts.extend([
            "L'utilisateur principal de cette application.",
            "La personne qui utilise THÉRÈSE.",
            "Le propriétaire du compte.",
        ])

        text = "\n".join(text_parts)

        # Use special ID for owner profile
        # Supprimer l'ancien embedding si existant
        try:
            qdrant.delete_by_entity("owner_profile")
        except Exception:
            pass  # Pas grave si rien à supprimer

        qdrant.add_memory(
            text=text,
            memory_type="owner",
            entity_id="owner_profile",
            metadata={
                "name": profile.name,
                "nickname": profile.nickname,
                "company": profile.company,
                "role": profile.role,
                "is_owner": True,
            },
        )

        logger.debug("User profile embedded in Qdrant")

    except Exception as e:
        logger.warning(f"Failed to embed profile in Qdrant: {e}")
        # Non-critical error, don't raise


async def delete_user_profile(session: AsyncSession) -> bool:
    """
    Delete user profile from database and Qdrant.

    Returns True if deleted, False if not found.
    """
    try:
        result = await session.execute(
            select(Preference).where(Preference.key == PROFILE_KEY)
        )
        pref = result.scalar_one_or_none()

        if not pref:
            return False

        await session.delete(pref)
        await session.commit()

        # Remove from Qdrant
        try:
            qdrant = get_qdrant_service()
            qdrant.delete_by_entity("owner_profile")
        except Exception:
            pass  # Non-critical

        logger.info("User profile deleted")
        return True

    except Exception as e:
        logger.error(f"Failed to delete user profile: {e}")
        await session.rollback()
        raise


def parse_claude_md(content: str) -> UserProfile:
    """
    Parse a THERESE.md file and extract user profile information.

    Looks for common patterns like:
    - **Owner** : Name
    - **Marque** : Company
    - **Tagline** or **Positionnement** : Role
    - **Localisation** : Location

    Args:
        content: Raw THERESE.md file content

    Returns:
        UserProfile with extracted information
    """
    profile = UserProfile(name="")

    # Extract Owner name
    owner_match = re.search(r'\*\*Owner\*\*\s*:\s*(.+?)(?:\n|$)', content)
    if owner_match:
        # Format: "Ludovic "Ludo" Sanchez"
        owner_text = owner_match.group(1).strip()

        # Check for nickname in quotes
        nickname_match = re.search(r'"([^"]+)"', owner_text)
        if nickname_match:
            profile.nickname = nickname_match.group(1)
            # Remove nickname from full name
            profile.name = re.sub(r'\s*"[^"]+"\s*', ' ', owner_text).strip()
        else:
            profile.name = owner_text

    # Extract Company/Marque
    company_match = re.search(r'\*\*Marque\*\*\s*:\s*(.+?)(?:\s*\(|$|\n)', content)
    if company_match:
        profile.company = company_match.group(1).strip()

    # Extract Role from Positionnement
    role_match = re.search(r'\*\*Positionnement\*\*\s*:\s*(.+?)(?:\n|$)', content)
    if role_match:
        profile.role = role_match.group(1).strip()

    # Extract Location
    location_match = re.search(r'\*\*Localisation\*\*\s*:\s*(.+?)(?:\n|$)', content)
    if location_match:
        profile.location = location_match.group(1).strip()

    # Extract Email
    email_match = re.search(r'\*\*Contact pro\*\*\s*:\s*(\S+@\S+)', content)
    if email_match:
        profile.email = email_match.group(1).strip()

    # Extract condensed context
    # Focus on Identité and Phase actuelle sections
    context_parts = []

    # Get Identité section
    identite_match = re.search(
        r'## Identité\n(.*?)(?=\n## |\Z)',
        content,
        re.DOTALL
    )
    if identite_match:
        context_parts.append(identite_match.group(1).strip()[:500])

    # Get Infos personnelles
    infos_match = re.search(
        r'## Infos personnelles\n(.*?)(?=\n## |\Z)',
        content,
        re.DOTALL
    )
    if infos_match:
        context_parts.append(infos_match.group(1).strip()[:300])

    # Get Phase actuelle
    phase_match = re.search(
        r'## Phase actuelle\n(.*?)(?=\n## |\Z)',
        content,
        re.DOTALL
    )
    if phase_match:
        context_parts.append(phase_match.group(1).strip()[:300])

    profile.context = "\n\n".join(context_parts)

    return profile


async def import_from_claude_md(
    session: AsyncSession,
    file_path: str,
) -> UserProfile:
    """
    Import user profile from a THERESE.md file.

    Args:
        session: Database session
        file_path: Path to THERESE.md file

    Returns:
        Imported and saved UserProfile
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not path.is_file():
        raise ValueError(f"Not a file: {file_path}")

    content = path.read_text(encoding="utf-8")
    profile = parse_claude_md(content)

    if not profile.name:
        raise ValueError("Could not extract user name from THERESE.md")

    # Save the profile
    return await set_user_profile(session, profile)


# Cached profile for performance (refreshed on update)
_cached_profile: UserProfile | None = None


def get_cached_profile() -> UserProfile | None:
    """Get cached profile without async call."""
    return _cached_profile


def set_cached_profile(profile: UserProfile | None) -> None:
    """Update cached profile."""
    global _cached_profile
    _cached_profile = profile
