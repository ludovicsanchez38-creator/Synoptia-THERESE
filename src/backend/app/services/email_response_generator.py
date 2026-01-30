"""
THÉRÈSE v2 - Email Response Generator

Génère des brouillons de réponse intelligents via LLM.
US-EMAIL-09
"""

from typing import Optional
from app.services.llm import get_llm_service
from app.services.user_profile import get_cached_profile


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
        contact_context: Optional[str] = None,
        thread_context: Optional[str] = None,
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

        user_name = (profile.name if profile else None) or 'Ludo'
        user_company = (profile.company if profile else None) or 'Synoptïa'
        user_role = (profile.role if profile else None) or 'Consultant IA'

        # Construire le prompt selon le ton
        tone_instructions = {
            'formal': "Ton professionnel et formel. Vouvoiement. Formules de politesse complètes.",
            'friendly': "Ton amical et décontracté. Tutoiement si approprié. Style direct et chaleureux.",
            'neutral': "Ton équilibré et courtois. Ni trop formel ni trop familier."
        }

        length_instructions = {
            'short': "Réponse courte et concise (2-3 phrases maximum).",
            'medium': "Réponse de longueur moyenne (1 paragraphe).",
            'detailed': "Réponse détaillée et complète (2-3 paragraphes)."
        }

        # Prompt système
        system_prompt = f"""Tu es l'assistant email de {user_name}, {user_role} chez {user_company}.

Tu rédiges des réponses professionnelles et pertinentes aux emails reçus.

{tone_instructions.get(tone, tone_instructions['neutral'])}
{length_instructions.get(length, length_instructions['medium'])}

Règles importantes :
- Signe toujours avec le nom de {user_name} (pas "Assistant IA")
- Réponds directement aux questions posées
- Sois concret et actionnable
- Propose des créneaux/dates si pertinent
- Ne mentionne jamais que tu es une IA"""

        # Contexte additionnel
        additional_context = ""
        if contact_context:
            additional_context += f"\n\nContexte CRM du contact :\n{contact_context}"
        if thread_context:
            additional_context += f"\n\nHistorique de la conversation :\n{thread_context}"

        # Prompt utilisateur
        user_prompt = f"""Email reçu de {from_name} ({from_email}) :

Sujet : {subject}

{body}
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
            response_text = response.strip()

            # S'assurer qu'il y a une signature
            if f'{user_name}' not in response_text:
                response_text += f"\n\nCordialement,\n{user_name}"

            return response_text

        except Exception as e:
            # Fallback si erreur LLM
            return f"""Bonjour {from_name},

Merci pour votre email concernant : {subject}

Je reviens vers vous rapidement.

Cordialement,
{user_name}"""
