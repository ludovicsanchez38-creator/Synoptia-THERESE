"""
THÉRÈSE v2 - Text Skills

Skills de génération de contenu textuel (emails, posts, propositions).
"""

from typing import Any

from .base import InputField, MarkdownSkill, SkillOutputType


class EmailProSkill(MarkdownSkill):
    """
    Skill de génération d'emails professionnels personnalisés.

    Génère des emails formels enrichis avec le contexte utilisateur.
    """

    skill_id = "email-pro"
    name = "Email Professionnel"
    description = "Rédige un email professionnel personnalisé"
    output_type = SkillOutputType.TEXT

    def get_input_schema(self) -> dict[str, InputField]:
        """Schéma des champs pour l'email professionnel."""
        return {
            'recipient': InputField(
                type='text',
                label='Destinataire',
                placeholder='Nom de la personne',
                required=True,
                help_text='À qui s\'adresse cet email ?'
            ),
            'subject': InputField(
                type='text',
                label='Sujet',
                placeholder='Objet de l\'email',
                required=True,
                help_text='De quoi parle cet email ?'
            ),
            'context': InputField(
                type='textarea',
                label='Contexte',
                placeholder='Que veux-tu dire ? Quel est le contexte ?',
                required=True,
                help_text='Fournis le maximum de détails pour un email pertinent'
            ),
            'tone': InputField(
                type='select',
                label='Ton',
                options=['formel', 'amical', 'neutre'],
                default='formel',
                required=False,
                help_text='Style de communication souhaité'
            ),
        }

    def get_enrichment_context(self, user_profile: dict[str, Any], memory_context: dict[str, Any]) -> dict[str, Any]:
        """Enrichit avec le profil utilisateur et éventuellement le contexte du destinataire."""
        enrichment = super().get_enrichment_context(user_profile, memory_context)

        # Chercher le destinataire dans les contacts
        recipient_name = memory_context.get('inputs', {}).get('recipient', '')
        if recipient_name and 'contacts' in memory_context:
            for contact in memory_context['contacts']:
                if recipient_name.lower() in contact.get('name', '').lower():
                    enrichment['recipient_context'] = f"""
Informations sur {contact['name']} :
- Entreprise : {contact.get('company', 'Non renseignée')}
- Email : {contact.get('email', 'Non renseigné')}
- Notes : {contact.get('notes', 'Aucune note')}
"""
                    break

        return enrichment

    def get_system_prompt_addition(self) -> str:
        """Instructions pour le LLM."""
        return """
## Instructions pour la génération d'emails professionnels

Tu es un assistant de rédaction d'emails professionnels.

**Consignes** :
1. Utilise un ton professionnel adapté au contexte
2. Structure : Salutation → Corps → Formule de politesse
3. Sois concis et direct (pas de blabla inutile)
4. Adapte-toi au ton demandé (formel/amical/neutre)
5. Ne génère PAS la signature (elle sera ajoutée automatiquement)

**Format de sortie** :
Génère uniquement le corps de l'email, sans signature.
"""

class LinkedInPostSkill(MarkdownSkill):
    """
    Skill de génération de posts LinkedIn engageants.

    Génère des posts LinkedIn avec le style Synoptïa.
    """

    skill_id = "linkedin-post"
    name = "Post LinkedIn"
    description = "Génère un post LinkedIn engageant"
    output_type = SkillOutputType.TEXT

    def get_input_schema(self) -> dict[str, InputField]:
        """Schéma des champs pour le post LinkedIn."""
        return {
            'topic': InputField(
                type='text',
                label='Sujet',
                placeholder='De quoi veux-tu parler ?',
                required=True,
                help_text='Thème principal du post'
            ),
            'key_message': InputField(
                type='textarea',
                label='Message clé',
                placeholder='Quel est le message principal ?',
                required=True,
                help_text='Ce que tu veux faire passer comme idée'
            ),
            'style': InputField(
                type='select',
                label='Style',
                options=['storytelling', 'éducatif', 'inspirant', 'débat'],
                default='storytelling',
                required=False,
                help_text='Format du post'
            ),
            'length': InputField(
                type='select',
                label='Longueur',
                options=['court (< 500 car)', 'moyen (500-1000)', 'long (> 1000)'],
                default='moyen (500-1000)',
                required=False,
                help_text='Longueur cible du post'
            ),
        }

    def get_system_prompt_addition(self) -> str:
        """Instructions pour le LLM."""
        return """
## Instructions pour la génération de posts LinkedIn

Tu es un expert en création de contenu LinkedIn engageant.

**Style Synoptïa** :
- Ton fluide, incarné, drôle, nuancé, anti-corporate
- Pas de tirets longs (–), seulement tirets courts (-)
- Évite le jargon corporate ("leverage", "synergy", etc.)
- Privilégie les exemples concrets et les anecdotes
- Utilise des émojis avec parcimonie (1-3 max)

**Structure recommandée** :
1. Hook : Accroche les 2 premières lignes
2. Développement : Storytelling ou argumentation
3. Call-to-action : Invitation à commenter/partager

**Format** :
- Paragraphes courts (2-3 lignes max)
- Ligne vide entre chaque paragraphe
- Pas de hashtags à la fin (sauf si explicitement demandé)
"""

class ProposalSkill(MarkdownSkill):
    """
    Skill de génération de propositions commerciales.

    Génère des propositions commerciales structurées pour Synoptïa.
    """

    skill_id = "proposal-pro"
    name = "Proposition Commerciale"
    description = "Génère une proposition commerciale structurée"
    output_type = SkillOutputType.TEXT

    def get_input_schema(self) -> dict[str, InputField]:
        """Schéma des champs pour la proposition commerciale."""
        return {
            'client_name': InputField(
                type='text',
                label='Nom du client',
                placeholder='Entreprise ou personne',
                required=True,
                help_text='À qui s\'adresse cette proposition ?'
            ),
            'project_title': InputField(
                type='text',
                label='Titre du projet',
                placeholder='Ex: Formation IA pour équipe commerciale',
                required=True,
                help_text='Nom du projet ou de la prestation'
            ),
            'objectives': InputField(
                type='textarea',
                label='Objectifs',
                placeholder='Quels sont les objectifs du client ?',
                required=True,
                help_text='Besoins identifiés et résultats attendus'
            ),
            'offer': InputField(
                type='select',
                label='Offre Synoptïa',
                options=['VOIR (149 EUR)', 'FORGER (490 EUR)', 'PROPULSER (2 490 EUR)', 'RAYONNER (2 990 EUR)', 'Sur mesure'],
                default='Sur mesure',
                required=False,
                help_text='Quelle offre proposer ?'
            ),
            'budget': InputField(
                type='text',
                label='Budget (optionnel)',
                placeholder='Ex: 2 500 EUR HT',
                required=False,
                help_text='Montant de la proposition si sur mesure'
            ),
        }

    def get_enrichment_context(self, user_profile: dict[str, Any], memory_context: dict[str, Any]) -> dict[str, Any]:
        """Enrichit avec le profil utilisateur et le contexte client."""
        enrichment = super().get_enrichment_context(user_profile, memory_context)

        # Chercher le client dans les contacts
        client_name = memory_context.get('inputs', {}).get('client_name', '')
        if client_name and 'contacts' in memory_context:
            for contact in memory_context['contacts']:
                if client_name.lower() in contact.get('name', '').lower():
                    enrichment['client_context'] = f"""
Informations sur {contact['name']} :
- Entreprise : {contact.get('company', 'Non renseignée')}
- Email : {contact.get('email', 'Non renseigné')}
- Stage : {contact.get('stage', 'Non renseigné')}
- Score : {contact.get('score', 'Non renseigné')}/100
- Notes : {contact.get('notes', 'Aucune note')}
"""
                    break

        return enrichment

    def get_system_prompt_addition(self) -> str:
        """Instructions pour le LLM."""
        return """
## Instructions pour la génération de propositions commerciales

Tu es un expert en rédaction de propositions commerciales pour Synoptïa.

**Structure obligatoire** :

1. **En-tête**
   - Titre : "Proposition commerciale - [Titre du projet]"
   - Client : [Nom du client]
   - Date : [Date du jour]

2. **Contexte et objectifs**
   - Problématique identifiée
   - Objectifs du client

3. **Solution proposée**
   - Description de l'offre
   - Déroulement / Planning
   - Livrables

4. **Tarification**
   - Montant HT
   - Conditions de paiement

5. **Prochaines étapes**
   - Actions concrètes
   - Délais de réponse

**Ton** :
- Professionnel mais humain
- Confiant et rassurant
- Anti-corporate (évite le jargon)

**Offres Synoptïa (pour référence)** :
- VOIR : 149 EUR HT - Audit flash (45 min)
- FORGER : 490 EUR HT - Session one-shot outils IA (2h30)
- PROPULSER : 2 490 EUR HT - Parcours 3 séances + vidéos async
- RAYONNER : 2 990 EUR HT - Journée présentiel
"""

