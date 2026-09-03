"""
THÉRÈSE v2 - User Profile Service

Manages user identity and profile for personalized interactions.
Fixes the bug where THÉRÈSE calls the user "Pierre" instead of their real name.
"""

import asyncio
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

    name: str                      # "Marie Exemple"
    nickname: str = ""             # "Marie"
    company: str = ""              # "Exemple SARL"
    role: str = ""                 # "Entrepreneur IA"
    context: str = ""              # Extended context from THERESE.md
    email: str = ""                # Contact email
    location: str = ""             # "Manosque, France"
    address: str = ""              # "12 rue de l'Exemple, 04100 Manosque"
    siren: str = ""                # "123 456 789"
    tva_intra: str = ""            # "FR 00 123 456 789"
    siret: str = ""                # "123 456 789 00010" (identite emetteur facture)
    code_ape: str = ""             # "0000Z" (code NAF)
    nda: str = ""                  # Numero declaration activite (organisme de formation)

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
            siret=data.get("siret", ""),
            code_ape=data.get("code_ape", ""),
            nda=data.get("nda", ""),
        )

    def is_billing_complete(self) -> bool:
        """Profil émetteur minimal pour émettre une facture conforme (P0-PROD-2)."""
        return bool((self.company or self.name) and self.siret and self.address)

    def missing_billing_fields(self) -> list[str]:
        """Champs manquants pour une facture conforme."""
        missing: list[str] = []
        if not (self.company or self.name):
            missing.append("raison sociale ou nom")
        if not self.siret:
            missing.append("SIRET")
        if not self.address:
            missing.append("adresse")
        return missing

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

        # Identité légale / facturation : injectée pour que l'assistant ne l'INVENTE
        # JAMAIS dans les documents (P0-PROD-2, constat C7 : SIRET/NDA hallucinés).
        legal = []
        if self.siret:
            legal.append(f"SIRET {self.siret}")
        if self.tva_intra:
            legal.append(f"TVA intra {self.tva_intra}")
        if self.nda:
            legal.append(f"déclaration d'activité (OF) {self.nda}")
        if legal:
            parts.append(
                f" Identité légale exacte (à reprendre telle quelle, ne jamais inventer) : "
                f"{', '.join(legal)}."
            )

        # Extended context (truncated if too long)
        if self.context:
            # Limit context to ~2000 chars to not overwhelm the prompt
            context_text = self.context[:2000]
            if len(self.context) > 2000:
                context_text += "..."
            parts.append(f"\n\n### Contexte utilisateur:\n{context_text}")

        return "".join(parts) if parts else ""

    def format_brief(self) -> str:
        """
        Variante allegee pour les conseillers du Board de decision.

        On y met qui est l'utilisateur, son metier et son contexte, mais PAS
        l'identite legale de facturation (SIRET/TVA/NDA) : elle est utile au
        chat et aux documents (anti-hallu) mais c'est du bruit pour une
        deliberation strategique (constat test global : profil emetteur trop
        verbeux injecte dans le Board).
        """
        parts = []
        if self.name:
            parts.append(f"Tu conseilles **{self.name}**")
            if self.nickname:
                parts.append(f" (appelle-le **{self.nickname}**)")
            parts.append(".")
        if self.role or self.company:
            role_parts = []
            if self.role:
                role_parts.append(self.role)
            if self.company:
                role_parts.append(f"chez {self.company}")
            parts.append(f" {' '.join(role_parts)}.")
        if self.location:
            parts.append(f" Basé à {self.location}.")
        if self.context:
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
        profile = UserProfile.from_dict(data)
        # Auto-réparation du cache process : le préchargement au démarrage ne
        # déchiffre pas (allow_decrypt=False pour ne pas bloquer sur le
        # trousseau), donc un profil chiffré laissait le cache vide jusqu'à la
        # prochaine sauvegarde et les statuts de facturation mentaient.
        set_cached_profile(profile)
        return profile

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
        # Get or create preference (BUG-026 : aligner sur key + category)
        result = await session.execute(
            select(Preference).where(
                Preference.key == PROFILE_KEY,
                Preference.category == PROFILE_CATEGORY,
            )
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

        # BUG-172. Le profil est ecrit : le travail durable est fait. Calculer
        # son vecteur semantique prend 19 secondes sur une machine modeste, et
        # attendre ce calcul pour repondre faisait voir a l'utilisateur
        # « Delai de 30 000 ms depasse » sur le tout premier ecran du logiciel,
        # alors que son profil etait bien enregistre.
        #
        # Allonger le delai cote client aurait deplace le seuil sans supprimer
        # l'attente : une machine plus lente l'aurait franchi a nouveau.
        # L'indexation part donc en tache de fond, et son echec eventuel ne
        # remet pas en cause une sauvegarde deja acquise.
        if embed_in_qdrant:
            global _GENERATION_PROFIL
            _GENERATION_PROFIL += 1
            tache = asyncio.create_task(
                _indexer_en_arriere_plan(profile, _GENERATION_PROFIL)
            )
            _INDEXATIONS_EN_COURS.add(tache)
            tache.add_done_callback(_INDEXATIONS_EN_COURS.discard)

        logger.info(f"User profile saved: {profile.name}")
        return profile

    except Exception as e:
        logger.error(f"Failed to save user profile: {e}")
        await session.rollback()
        raise


# Les taches asyncio ne sont retenues que par une reference forte : sans cet
# ensemble, le ramasse-miettes peut annuler une indexation en cours de route.
_INDEXATIONS_EN_COURS: set[asyncio.Task[None]] = set()

# Revue : deux sauvegardes rapprochees lancaient deux indexations CONCURRENTES
# sur la meme entite, et chacune commence par supprimer l'ancienne. Entre la
# suppression de la seconde et son ecriture, le profil n'existait plus dans
# l'index : « qui suis-je ? » restait sans reponse, sans que rien ne le signale.
#
# C'est exactement le scenario du testeur : « j'ai refait Continuer et c'est
# passe ».
#
# Un simple verrou ne suffit PAS : il serialise, mais ne garantit pas l'ordre de
# DEMARRAGE. L'ordonnanceur peut lancer la seconde tache avant la premiere, et
# l'index garderait alors l'ANCIEN nom - le testeur corrige son prenom, la
# correction est perdue.
#
# Annuler la tache perimee ne marche pas non plus, et c'est PIRE : les
# operations Qdrant passent par `asyncio.to_thread`, qui n'est pas annulable.
# Annuler libere le verrou, mais le travail deja lance dans le thread continue.
# Reproduit en revue : une ancienne suppression se terminait APRES le nouvel
# ajout, et l'etat final ne contenait plus aucun profil.
#
# D'ou le NUMERO DE GENERATION. Chaque sauvegarde en prend un ; une tache
# renonce AVANT d'entrer dans la section critique si sa generation est deja
# depassee, et une tache deja entree va au bout - la suivante repassera derriere
# elle. Rien n'est interrompu en vol, et le dernier enregistre gagne quand meme.
_VERROU_INDEXATION = asyncio.Lock()
_GENERATION_PROFIL = 0


async def _indexer_en_arriere_plan(profile: UserProfile, generation: int) -> None:
    """Indexe le profil sans jamais faire echouer sa sauvegarde.

    Une indexation qui echoue prive la recherche semantique de son proprietaire,
    ce qui merite un journal ; elle ne justifie pas de perdre un profil que
    l'utilisateur vient de saisir.
    """
    try:
        async with _VERROU_INDEXATION:
            # Sa generation a-t-elle ete depassee pendant l'attente du verrou ?
            # Si oui, indexer un profil perime effacerait le plus recent : on
            # renonce ici, AVANT toute ecriture, et non en pleine operation.
            if generation != _GENERATION_PROFIL:
                logger.debug(
                    "Indexation du profil abandonnee : generation %s depassee par %s",
                    generation, _GENERATION_PROFIL,
                )
                return
            await _embed_profile(profile)
    except Exception:
        logger.warning(
            "Profil enregistre mais non indexe : la question « qui suis-je ? » "
            "restera sans reponse jusqu'a la prochaine sauvegarde",
            exc_info=True,
        )


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
            # Meme piege que l'ajout : `delete_by_entity` est SYNCHRONE et
            # gelerait la boucle d'evenements pendant tout l'appel.
            await asyncio.to_thread(qdrant.delete_by_entity, "owner_profile")
        except Exception as e:
            logger.debug("Qdrant operation non critique echouee: %s", e)

        # Revue : `add_memory` est SYNCHRONE. Appelee telle quelle depuis une
        # tache asyncio, elle gelerait la boucle d'evenements pendant tout le
        # calcul — le serveur n'a qu'un processus, donc une requete d'un autre
        # ecran attendrait ces 19 secondes sans raison. La version asynchrone
        # deporte le travail hors de la boucle.
        await qdrant.async_add_memory(
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
        # BUG-026 : aligner sur key + category (comme get_user_profile)
        result = await session.execute(
            select(Preference).where(
                Preference.key == PROFILE_KEY,
                Preference.category == PROFILE_CATEGORY,
            )
        )
        pref = result.scalar_one_or_none()

        if not pref:
            return False

        await session.delete(pref)
        await session.commit()

        # RGPD : une suppression doit TENIR. Deux protections, car une seule ne
        # suffit pas.
        #
        # Avancer la generation fait renoncer les indexations qui attendent
        # encore le verrou. Mais une indexation DEJA entree dans la section
        # critique a franchi ce controle : elle ecrirait apres la suppression,
        # et les donnees personnelles reapparaitraient. La suppression prend
        # donc le verrou a son tour - elle attend celle qui est en vol, puis
        # supprime pour de bon.
        global _GENERATION_PROFIL
        _GENERATION_PROFIL += 1

        # Remove from Qdrant
        try:
            qdrant = get_qdrant_service()
            async with _VERROU_INDEXATION:
                # Appel synchrone deporte : il gelait la boucle d'evenements,
                # comme le faisait l'indexation avant sa correction.
                await asyncio.to_thread(qdrant.delete_by_entity, "owner_profile")
        except Exception as e:
            logger.debug("Qdrant operation non critique echouee: %s", e)

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
        # Format: "Marie "Mimi" Exemple"
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
