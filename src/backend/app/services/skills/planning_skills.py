"""
THÉRÈSE v2 - Planning Skills

Skills de planification et d'organisation.
"""

from pathlib import Path
from typing import Any

from .base import BaseSkill, InputField, SkillParams, SkillResult, SkillOutputType, FileFormat


class PlanMeetingSkill(BaseSkill):
    """Planification de réunion."""

    skill_id = "plan-meeting"
    name = "Planifier Réunion"
    description = "Crée un plan de réunion structuré"
    output_type = SkillOutputType.TEXT
    output_format = FileFormat.DOCX

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

    async def execute(self, params: SkillParams) -> SkillResult:
        file_id = self.generate_file_id()
        return SkillResult(
            file_id=file_id,
            file_path=Path(""),
            file_name="",
            file_size=0,
            mime_type="text/plain",
            format=FileFormat.DOCX,
        )


class PlanProjectSkill(BaseSkill):
    """Planification de projet."""

    skill_id = "plan-project"
    name = "Planifier Projet"
    description = "Crée un plan de projet structuré"
    output_type = SkillOutputType.TEXT
    output_format = FileFormat.DOCX

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

    async def execute(self, params: SkillParams) -> SkillResult:
        file_id = self.generate_file_id()
        return SkillResult(
            file_id=file_id,
            file_path=Path(""),
            file_name="",
            file_size=0,
            mime_type="text/plain",
            format=FileFormat.DOCX,
        )


class PlanWeekSkill(BaseSkill):
    """Planification de semaine."""

    skill_id = "plan-week"
    name = "Planifier Semaine"
    description = "Organise ta semaine de manière optimale"
    output_type = SkillOutputType.TEXT
    output_format = FileFormat.DOCX

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

    async def execute(self, params: SkillParams) -> SkillResult:
        file_id = self.generate_file_id()
        return SkillResult(
            file_id=file_id,
            file_path=Path(""),
            file_name="",
            file_size=0,
            mime_type="text/plain",
            format=FileFormat.DOCX,
        )


class PlanGoalsSkill(BaseSkill):
    """Planification d'objectifs."""

    skill_id = "plan-goals"
    name = "Planifier Objectifs"
    description = "Décompose un objectif en plan d'action"
    output_type = SkillOutputType.TEXT
    output_format = FileFormat.DOCX

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

    async def execute(self, params: SkillParams) -> SkillResult:
        file_id = self.generate_file_id()
        return SkillResult(
            file_id=file_id,
            file_path=Path(""),
            file_name="",
            file_size=0,
            mime_type="text/plain",
            format=FileFormat.DOCX,
        )


class WorkflowN8nSkill(BaseSkill):
    """Générateur de workflow n8n."""

    skill_id = "workflow-n8n"
    name = "Workflow n8n"
    description = "Génère un workflow n8n pour automatiser une tâche"
    output_type = SkillOutputType.TEXT
    output_format = FileFormat.DOCX

    def get_input_schema(self) -> dict[str, InputField]:
        return {
            'task': InputField(
                type='textarea',
                label='Tâche à automatiser',
                placeholder='Ex: Envoyer un email quand un formulaire est rempli',
                required=True,
            ),
            'trigger': InputField(
                type='text',
                label='Déclencheur',
                placeholder='Ex: Webhook, Schedule, Form submission',
                required=False,
            ),
            'tools': InputField(
                type='textarea',
                label='Outils connectés',
                placeholder='Ex: Google Sheets, Gmail, Notion',
                required=False,
            ),
        }

    def get_system_prompt_addition(self) -> str:
        return """
## Instructions pour workflow n8n

Génère un workflow n8n détaillé :
1. **Vue d'ensemble** : Schéma du workflow (ASCII ou description)
2. **Nodes** : Liste des nodes avec configuration
3. **Trigger** : Configuration du déclencheur
4. **Data mapping** : Transformations et mappings
5. **Error handling** : Gestion des erreurs
6. **Setup** : Steps pour configurer dans n8n
"""

    async def execute(self, params: SkillParams) -> SkillResult:
        file_id = self.generate_file_id()
        return SkillResult(
            file_id=file_id,
            file_path=Path(""),
            file_name="",
            file_size=0,
            mime_type="text/plain",
            format=FileFormat.DOCX,
        )


class AppsScriptGeneratorSkill(BaseSkill):
    """Générateur Apps Script."""

    skill_id = "apps-script-generator"
    name = "Apps Script"
    description = "Génère du code Google Apps Script"
    output_type = SkillOutputType.TEXT
    output_format = FileFormat.DOCX

    def get_input_schema(self) -> dict[str, InputField]:
        return {
            'task': InputField(
                type='textarea',
                label='Tâche à automatiser',
                placeholder='Ex: Copier données d\'un Sheet à un autre chaque jour',
                required=True,
            ),
            'google_service': InputField(
                type='select',
                label='Service Google',
                options=['Sheets', 'Docs', 'Gmail', 'Calendar', 'Drive', 'Multiple'],
                default='Sheets',
                required=False,
            ),
        }

    def get_system_prompt_addition(self) -> str:
        return """
## Instructions pour Apps Script

Génère du code Google Apps Script fonctionnel :
1. **Code complet** : Avec commentaires explicatifs
2. **Setup** : Comment l'installer et le configurer
3. **Triggers** : Configuration des déclencheurs (time-driven, event-driven)
4. **Permissions** : Autorisations nécessaires
5. **Testing** : Comment tester le script
6. **Best practices** : Optimisations et bonnes pratiques
"""

    async def execute(self, params: SkillParams) -> SkillResult:
        file_id = self.generate_file_id()
        return SkillResult(
            file_id=file_id,
            file_path=Path(""),
            file_name="",
            file_size=0,
            mime_type="text/plain",
            format=FileFormat.DOCX,
        )


class WorkflowMakeSkill(BaseSkill):
    """Générateur de scénario Make."""

    skill_id = "workflow-make"
    name = "Scénario Make"
    description = "Génère un scénario Make (ex-Integromat)"
    output_type = SkillOutputType.TEXT
    output_format = FileFormat.DOCX

    def get_input_schema(self) -> dict[str, InputField]:
        return {
            'task': InputField(
                type='textarea',
                label='Tâche à automatiser',
                placeholder='Ex: Synchroniser contacts CRM avec newsletter',
                required=True,
            ),
            'apps': InputField(
                type='textarea',
                label='Applications',
                placeholder='Ex: Airtable, Mailchimp, Slack',
                required=False,
            ),
        }

    def get_system_prompt_addition(self) -> str:
        return """
## Instructions pour scénario Make

Génère un scénario Make détaillé :
1. **Vue d'ensemble** : Flow du scénario
2. **Modules** : Configuration de chaque module
3. **Data mapping** : Mapping des champs
4. **Filters & routers** : Logique conditionnelle
5. **Error handling** : Gestion des erreurs
6. **Setup guide** : Steps pour créer dans Make
"""

    async def execute(self, params: SkillParams) -> SkillResult:
        file_id = self.generate_file_id()
        return SkillResult(
            file_id=file_id,
            file_path=Path(""),
            file_name="",
            file_size=0,
            mime_type="text/plain",
            format=FileFormat.DOCX,
        )


class WorkflowZapierSkill(BaseSkill):
    """Générateur de Zap."""

    skill_id = "workflow-zapier"
    name = "Zap Zapier"
    description = "Génère un Zap Zapier"
    output_type = SkillOutputType.TEXT
    output_format = FileFormat.DOCX

    def get_input_schema(self) -> dict[str, InputField]:
        return {
            'task': InputField(
                type='textarea',
                label='Tâche à automatiser',
                placeholder='Ex: Créer tâche Trello depuis email Gmail',
                required=True,
            ),
            'trigger_app': InputField(
                type='text',
                label='App déclencheur',
                placeholder='Ex: Gmail, Google Forms, Typeform',
                required=False,
            ),
            'action_app': InputField(
                type='text',
                label='App action',
                placeholder='Ex: Trello, Notion, Slack',
                required=False,
            ),
        }

    def get_system_prompt_addition(self) -> str:
        return """
## Instructions pour Zap Zapier

Génère un Zap complet :
1. **Trigger** : Configuration du déclencheur
2. **Actions** : Étapes et configurations
3. **Filters** : Conditions et filtres
4. **Field mapping** : Mapping des données
5. **Testing** : Comment tester le Zap
6. **Setup guide** : Steps pour créer dans Zapier
"""

    async def execute(self, params: SkillParams) -> SkillResult:
        file_id = self.generate_file_id()
        return SkillResult(
            file_id=file_id,
            file_path=Path(""),
            file_name="",
            file_size=0,
            mime_type="text/plain",
            format=FileFormat.DOCX,
        )


class DocumentProcessSkill(BaseSkill):
    """Documentation de processus."""

    skill_id = "document-process"
    name = "Documenter Processus"
    description = "Documente un processus métier"
    output_type = SkillOutputType.TEXT
    output_format = FileFormat.DOCX

    def get_input_schema(self) -> dict[str, InputField]:
        return {
            'process_name': InputField(
                type='text',
                label='Nom du processus',
                placeholder='Ex: Onboarding client',
                required=True,
            ),
            'steps': InputField(
                type='textarea',
                label='Étapes',
                placeholder='Liste les grandes étapes (optionnel)',
                required=False,
            ),
            'format': InputField(
                type='select',
                label='Format',
                options=['Standard', 'SOP (procédure)', 'Flowchart description', 'Checklist'],
                default='Standard',
                required=False,
            ),
        }

    def get_system_prompt_addition(self) -> str:
        return """
## Instructions pour documenter un processus

Crée une documentation claire et actionnable :
1. **Overview** : Objectif et scope du processus
2. **Prérequis** : Ce qu'il faut avant de commencer
3. **Steps détaillés** : Chaque étape avec actions et responsables
4. **Decision points** : Conditions et alternatives
5. **Templates/outils** : Documents et outils nécessaires
6. **KPIs** : Comment mesurer le succès
7. **FAQ** : Questions fréquentes
"""

    async def execute(self, params: SkillParams) -> SkillResult:
        file_id = self.generate_file_id()
        return SkillResult(
            file_id=file_id,
            file_path=Path(""),
            file_name="",
            file_size=0,
            mime_type="text/plain",
            format=FileFormat.DOCX,
        )
