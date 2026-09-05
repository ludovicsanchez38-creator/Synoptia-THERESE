"""
THÉRÈSE v2 - Email Response Generator

Génère des brouillons de réponse intelligents via LLM.
US-EMAIL-09
"""

import logging
from typing import TYPE_CHECKING

from app.services.llm import get_llm_service
from app.services.user_profile import get_cached_profile

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class GenerationImpossible(RuntimeError):
    """La rédaction assistée a échoué, avec une cause dicible à l'utilisateur."""


# Causes reconnues, de la plus specifique a la plus generale. Le message dit ce
# qui s'est passe ET ce que l'utilisateur peut faire : un diagnostic sans issue
# ne vaut pas mieux qu'un silence.
_CAUSES_CONNUES: tuple[tuple[tuple[str, ...], str], ...] = (
    (
        ("api key", "unauthorized", "401", "invalid_api_key", "authentication"),
        "La clé d'API du fournisseur est refusée. Vérifie-la dans Réglages, "
        "rubrique IA.",
    ),
    (
        ("does not support tools", "tool", "function calling"),
        "Le modèle choisi ne sait pas rédiger de réponse assistée. Choisis un "
        "autre modèle dans Réglages, rubrique IA.",
    ),
    (
        ("timed out", "timeout", "deadline"),
        "Le modèle a mis trop de temps à répondre. Réessaie, ou choisis un "
        "modèle plus rapide.",
    ),
    (
        ("connection refused", "connect", "unreachable", "network", "dns"),
        "Impossible de joindre le fournisseur. Vérifie ta connexion, ou que "
        "ton serveur local est bien démarré.",
    ),
    (
        ("rate limit", "429", "quota", "insufficient_quota"),
        "Le fournisseur a refusé la demande : quota atteint. Réessaie plus "
        "tard, ou vérifie ton compte.",
    ),
    (
        ("context length", "too many tokens", "maximum context"),
        "Le message est trop long pour ce modèle. Choisis un modèle à plus "
        "grande fenêtre, ou réponds à un extrait.",
    ),
)


def cause_lisible(erreur_brute: str) -> str:
    """Traduit une erreur technique en phrase utile, sans rien laisser fuiter.

    L'erreur brute d'un fournisseur contient parfois une URL interne, un nom
    d'hote ou un fragment de cle. Elle n'est JAMAIS recopiee : seule une phrase
    ecrite d'avance remonte a l'ecran, le detail restant au journal.
    """
    minuscule = (erreur_brute or "").lower()

    for marqueurs, message in _CAUSES_CONNUES:
        if any(marqueur in minuscule for marqueur in marqueurs):
            return message

    return (
        "La rédaction assistée n'a pas abouti. Le détail est dans le journal "
        "de l'application ; tu peux réessayer ou changer de modèle dans "
        "Réglages, rubrique IA."
    )


def build_email_system_prompt(
    user_name: str,
    user_role: str,
    user_company: str,
    tone: str = "formal",
    length: str = "medium",
) -> str:
    """Construit le prompt système du générateur de réponses email.

    Extrait pour être testable (US-003). La consigne « ne mentionne jamais que
    tu es une IA » a été retirée (IA Act art. 50) ; la signature au nom de
    l'utilisateur et la protection des données CRM sont conservées.
    """
    tone_instructions = {
        "formal": "Ton professionnel et formel. Vouvoiement. Formules de politesse complètes.",
        "friendly": "Ton amical et décontracté. Tutoiement si approprié. Style direct et chaleureux.",
        "neutral": "Ton équilibré et courtois. Ni trop formel ni trop familier.",
    }
    length_instructions = {
        "short": "Réponse courte et concise (2-3 phrases maximum).",
        "medium": "Réponse de longueur moyenne (1 paragraphe).",
        "detailed": "Réponse détaillée et complète (2-3 paragraphes).",
    }

    return f"""Tu es l'assistant email de {user_name}, {user_role} chez {user_company}.

Tu rédiges des réponses professionnelles et pertinentes aux emails reçus.

{tone_instructions.get(tone, tone_instructions['neutral'])}
{length_instructions.get(length, length_instructions['medium'])}

Règles importantes :
- Signe toujours avec le nom de {user_name} (pas "Assistant IA")
- Réponds directement aux questions posées
- Sois concret et actionnable
- Propose des créneaux/dates si pertinent
- Ne mentionne JAMAIS le score CRM, le stage commercial, les notes internes, les informations de pipeline, ni aucune donnée confidentielle issue du CRM dans ta réponse."""


class EmailResponseGenerator:
    """Génère des réponses emails via LLM."""

    @staticmethod
    async def generate_response(
        subject: str,
        from_name: str,
        from_email: str,
        body: str,
        tone: str = 'formal',  # formal | friendly | neutral
        length: str = 'medium',  # short | medium | detailed
        contact_context: str | None = None,
        thread_context: str | None = None,
        session: "AsyncSession | None" = None,
    ) -> str:
        """
        Génère un brouillon de réponse.

        Args:
            subject: Sujet de l'email original
            from_name: Nom expéditeur
            from_email: Email expéditeur
            body: Contenu email original
            tone: Ton de la réponse (formal/friendly/neutral)
            length: Longueur (short/medium/detailed)
            contact_context: Contexte CRM du contact
            thread_context: Emails précédents du thread

        Returns:
            Brouillon de réponse en texte
        """
        # Récupérer profil utilisateur
        profile = get_cached_profile()
        if profile is None and session is not None:
            # B-394 (05/09/2026) : le préchargement au démarrage ne déchiffre
            # pas le profil (pas de prompt trousseau bloquant), donc sur un
            # poste au profil chiffré le cache reste vide jusqu'à la première
            # sauvegarde, et le brouillon partait signé « Ludo / Synoptïa »
            # chez une utilisatrice qui s'appelle Marie. Lecture de secours en
            # session, qui répare le cache au passage (même remède que le
            # statut de facturation en juillet).
            from app.services.user_profile import get_user_profile

            profile = await get_user_profile(session)

        user_name = (profile.name if profile else None) or 'Ludo'
        user_company = (profile.company if profile else None) or 'Synoptïa'
        user_role = (profile.role if profile else None) or 'Consultant IA'

        # Prompt système (US-003 : sans consigne de dissimulation IA)
        system_prompt = build_email_system_prompt(
            user_name, user_role, user_company, tone, length
        )

        # B-035. Le corps d'un e-mail reçu, son sujet et son expéditeur sont
        # des données TIERCES : elles entrent dans le prompt encadrées par
        # [Source: email]...[End email], et les marqueurs qu'elles portent
        # sont neutralisés — exactement ce que fait déjà _summarize_emails sur
        # le même contenu. Sans cette enveloppe, un faux [End email] placé
        # dans le corps sortait de l'encadrement et le reste du message était
        # lu comme une consigne.
        from app.services.prompt_security import get_prompt_security

        securite = get_prompt_security()
        message_recu = securite.sanitize_for_context(
            f"De : {from_name} ({from_email})\nSujet : {subject}\n\n{body}",
            source="email",
        )

        # Contexte additionnel
        additional_context = ""
        if contact_context:
            # Le CRM vient de la base de l'utilisateur, pas d'un tiers.
            additional_context += f"\n\nContexte CRM du contact :\n{contact_context}"
        if thread_context:
            # Même origine non fiable que le corps : même enveloppe.
            historique = securite.sanitize_for_context(thread_context, source="email")
            additional_context += f"\n\nHistorique de la conversation :\n{historique}"

        # Prompt utilisateur
        user_prompt = f"""Email reçu :

{message_recu}
{additional_context}

Rédige une réponse appropriée en français."""

        # Appeler le LLM
        llm_service = get_llm_service()

        try:
            response = await llm_service.generate_content(
                prompt=user_prompt,
                system_prompt=system_prompt,
            )

            # Nettoyer la réponse (retirer signatures multiples, etc.)
            response_text = (response or "").strip()
            if not response_text:
                # B-461 (05/09/2026) : un flux vide (coupure, filtre de
                # contenu silencieux, modèle qui ne rend que du raisonnement)
                # devenait un brouillon réduit à « Cordialement, Marie ».
                raise GenerationImpossible(
                    "Le modèle n'a rendu aucun texte : réessaie, ou change de modèle dans les réglages."
                )

            # S'assurer qu'il y a une signature
            if f'{user_name}' not in response_text:
                response_text += f"\n\nCordialement,\n{user_name}"

            return response_text

        except GenerationImpossible:
            raise
        except Exception as e:
            # BUG-171. Ce bloc renvoyait un brouillon FABRIQUE (« Je reviens
            # vers vous rapidement ») avec un HTTP 200. L'utilisateur recevait
            # donc un texte qu'aucune IA n'avait ecrit, sans savoir que la
            # generation avait echoue — et pouvait l'envoyer tel quel a son
            # client.
            #
            # Entre un echec annonce et un faux succes, l'echec annonce est
            # toujours preferable. Le detail technique va au journal, la cause
            # traduite remonte a l'ecran.
            logger.warning("Generation de reponse email impossible : %s", e, exc_info=True)
            raise GenerationImpossible(cause_lisible(str(e))) from e
