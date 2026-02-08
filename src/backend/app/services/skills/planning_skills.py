"""
THÉRÈSE v2 - Planning Skills

Skills de planification et d'organisation.
"""


from .base import InputField, MarkdownSkill, SkillOutputType


class PlanMeetingSkill(MarkdownSkill):
    """Planification de réunion."""

    skill_id = "plan-meeting"
    name = "Planifier Réunion"
    description = "Crée un plan de réunion structuré"
    output_type = SkillOutputType.TEXT

    def get_input_schema(self) -> dict[str, InputField]:
        return {
            'meeting_topic': InputField(
                type='text',
                label='Sujet de la réunion',
                placeholder='Ex: Point projet THÉRÈSE',
                required=True,
            ),
            'duration': InputField(
                type='text',
                label='Durée',
                placeholder='Ex: 30 min, 1h',
                default='1h',
                required=False,
            ),
            'participants': InputField(
                type='text',
                label='Participants',
                placeholder='Nombre ou noms',
                required=False,
            ),
            'objectives': InputField(
                type='textarea',
                label='Objectifs',
                placeholder='Que veux-tu accomplir ?',
                required=True,
            ),
        }

    def get_system_prompt_addition(self) -> str:
        return """
## Instructions pour planifier une réunion

Crée un plan de réunion structuré :
1. **Infos pratiques** : Titre, durée, participants
2. **Objectifs** : Résultats attendus
3. **Agenda** : Timeline détaillée (avec timings)
4. **Préparation** : Documents/infos à préparer
5. **Actions attendues** : Décisions à prendre
"""

class PlanProjectSkill(MarkdownSkill):
    """Planification de projet."""

    skill_id = "plan-project"
    name = "Planifier Projet"
    description = "Crée un plan de projet structuré"
    output_type = SkillOutputType.TEXT

    def get_input_schema(self) -> dict[str, InputField]:
        return {
            'project_name': InputField(
                type='text',
                label='Nom du projet',
                placeholder='Ex: Lancement newsletter IA',
                required=True,
            ),
            'deadline': InputField(
                type='text',
                label='Échéance',
                placeholder='Ex: 3 mois, 15 mars',
                required=False,
            ),
            'objectives': InputField(
                type='textarea',
                label='Objectifs',
                placeholder='Quels résultats attends-tu ?',
                required=True,
            ),
            'constraints': InputField(
                type='textarea',
                label='Contraintes',
                placeholder='Budget, ressources, délais...',
                required=False,
            ),
        }

    def get_system_prompt_addition(self) -> str:
        return """
## Instructions pour planifier un projet

Crée un plan de projet actionnable :
1. **Vision** : Objectif final et bénéfices
2. **Phases** : Découpage en 3-5 phases claires
3. **Livrables** : Par phase, avec critères de succès
4. **Timeline** : Jalons et deadlines
5. **Risques** : Identification et mitigation
6. **Actions immédiates** : 3-5 prochaines actions
"""

class PlanWeekSkill(MarkdownSkill):
    """Planification de semaine."""

    skill_id = "plan-week"
    name = "Planifier Semaine"
    description = "Organise ta semaine de manière optimale"
    output_type = SkillOutputType.TEXT

    def get_input_schema(self) -> dict[str, InputField]:
        return {
            'priorities': InputField(
                type='textarea',
                label='Priorités',
                placeholder='Quelles sont tes priorités cette semaine ?',
                required=True,
            ),
            'constraints': InputField(
                type='textarea',
                label='Contraintes',
                placeholder='RDV fixes, deadlines, indisponibilités...',
                required=False,
            ),
            'work_style': InputField(
                type='select',
                label='Style de travail',
                options=['Focus intense', 'Équilibré', 'Flexible'],
                default='Équilibré',
                required=False,
            ),
        }

    def get_system_prompt_addition(self) -> str:
        return """
## Instructions pour planifier une semaine

Crée un planning hebdomadaire réaliste :
1. **Vue d'ensemble** : Priorités et objectifs de la semaine
2. **Planning jour par jour** : Blocs de temps avec tâches
3. **Time blocking** : Créneaux dédiés (deep work, admin, perso)
4. **Buffers** : Marges pour les imprévus
5. **Rituals** : Routines (début/fin de journée, pauses)
"""

class PlanGoalsSkill(MarkdownSkill):
    """Planification d'objectifs."""

    skill_id = "plan-goals"
    name = "Planifier Objectifs"
    description = "Décompose un objectif en plan d'action"
    output_type = SkillOutputType.TEXT

    def get_input_schema(self) -> dict[str, InputField]:
        return {
            'goal': InputField(
                type='text',
                label='Objectif',
                placeholder='Ex: Atteindre 10 clients par mois',
                required=True,
            ),
            'timeframe': InputField(
                type='select',
                label='Horizon',
                options=['1 mois', '3 mois', '6 mois', '1 an'],
                default='3 mois',
                required=False,
            ),
            'current_situation': InputField(
                type='textarea',
                label='Situation actuelle',
                placeholder='Où en es-tu aujourd\'hui ?',
                required=False,
            ),
        }

    def get_system_prompt_addition(self) -> str:
        return """
## Instructions pour planifier des objectifs

Transforme l'objectif en plan d'action SMART :
1. **Objectif clarifié** : Spécifique, mesurable, atteignable
2. **Gap analysis** : Situation actuelle vs cible
3. **Stratégies** : 3-5 axes d'action
4. **Plan d'action** : Actions concrètes par mois/semaine
5. **KPIs** : Indicateurs de suivi
6. **Quick wins** : Premiers résultats rapides
"""

class WorkflowSkill(MarkdownSkill):
    """Generateur de workflow d'automatisation (agnostique plateforme)."""

    skill_id = "workflow-automation"
    name = "Workflow Automatisation"
    description = "Génère un workflow d'automatisation pour n'importe quelle plateforme"
    output_type = SkillOutputType.TEXT

    def get_input_schema(self) -> dict[str, InputField]:
        return {
            'task': InputField(
                type='textarea',
                label='Tache a automatiser',
                placeholder='Ex: Envoyer un email quand un formulaire est rempli',
                required=True,
            ),
            'platform': InputField(
                type='select',
                label='Plateforme',
                options=[
                    'Non decide',
                    'n8n',
                    'Make',
                    'Zapier',
                    'Apps Script',
                    'Power Automate',
                    'Autre',
                ],
                default='Non decide',
                required=False,
            ),
            'trigger': InputField(
                type='text',
                label='Declencheur',
                placeholder='Ex: Webhook, Schedule, Form submission',
                required=False,
            ),
            'tools': InputField(
                type='textarea',
                label='Outils connectes',
                placeholder='Ex: Google Sheets, Gmail, Notion, Slack',
                required=False,
            ),
        }

    def get_system_prompt_addition(self) -> str:
        return """
## Instructions pour workflow d'automatisation

Genere un workflow detaille adapte a la plateforme choisie :
1. **Vue d'ensemble** : Schema du workflow (ASCII ou description)
2. **Etapes** : Liste des etapes/nodes avec configuration
3. **Declencheur** : Configuration du trigger
4. **Data mapping** : Transformations et mappings de donnees
5. **Gestion d'erreurs** : Error handling et fallbacks
6. **Guide de mise en place** : Steps pour configurer sur la plateforme

Si la plateforme est "Non decide", recommande la plus adaptee au cas d'usage
et explique pourquoi.
"""

