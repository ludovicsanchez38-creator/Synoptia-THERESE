"""
THÉRÈSE v2 - Analysis Skills

Skills d'analyse et de compréhension.
"""

from typing import Any

from .base import MarkdownSkill, InputField, SkillOutputType


class AnalyzeXlsxSkill(MarkdownSkill):
    """Analyse de fichiers Excel."""

    skill_id = "analyze-xlsx"
    name = "Analyser Fichier Excel"
    description = "Analyse un fichier Excel et identifie les tendances"
    output_type = SkillOutputType.ANALYSIS

    def get_input_schema(self) -> dict[str, InputField]:
        return {
            'file_path': InputField(
                type='file',
                label='Fichier Excel',
                placeholder='Sélectionne un fichier .xlsx',
                required=True,
                help_text='Fichier à analyser'
            ),
            'focus': InputField(
                type='textarea',
                label='Focus de l\'analyse',
                placeholder='Que cherches-tu spécifiquement ?',
                required=False,
                help_text='Aspects particuliers à analyser'
            ),
        }

    def get_system_prompt_addition(self) -> str:
        return """
## Instructions pour l'analyse Excel

Analyse le fichier Excel et fournis :
1. **Structure** : Onglets, colonnes, types de données
2. **Insights** : Tendances, patterns, anomalies
3. **Statistiques** : Moyennes, totaux, distributions
4. **Recommandations** : Actions suggérées
"""

class AnalyzePdfSkill(MarkdownSkill):
    """Analyse de documents PDF."""

    skill_id = "analyze-pdf"
    name = "Analyser Document PDF"
    description = "Résume et extrait les informations d'un PDF"
    output_type = SkillOutputType.ANALYSIS

    def get_input_schema(self) -> dict[str, InputField]:
        return {
            'file_path': InputField(
                type='file',
                label='Document PDF',
                placeholder='Sélectionne un fichier .pdf',
                required=True,
            ),
            'focus': InputField(
                type='select',
                label='Type d\'analyse',
                options=['Résumé global', 'Points clés', 'Extraction données', 'Analyse critique'],
                default='Résumé global',
                required=False,
            ),
        }

    def get_system_prompt_addition(self) -> str:
        return """
## Instructions pour l'analyse PDF

Fournis une analyse structurée :
1. **Résumé** : Idée principale en 3-5 phrases
2. **Points clés** : 5-10 points essentiels
3. **Informations extraites** : Données chiffrées, dates, noms
4. **Évaluation** : Qualité, pertinence, limites
"""

class AnalyzeWebsiteSkill(MarkdownSkill):
    """Analyse de sites web."""

    skill_id = "analyze-website"
    name = "Analyser Site Web"
    description = "Analyse la structure et le contenu d'un site"
    output_type = SkillOutputType.ANALYSIS

    def get_input_schema(self) -> dict[str, InputField]:
        return {
            'url': InputField(
                type='text',
                label='URL du site',
                placeholder='https://exemple.com',
                required=True,
            ),
            'aspects': InputField(
                type='select',
                label='Aspects à analyser',
                options=['Global', 'UX/Design', 'Contenu/SEO', 'Performance', 'Concurrence'],
                default='Global',
                required=False,
            ),
        }

    def get_system_prompt_addition(self) -> str:
        return """
## Instructions pour l'analyse web

Analyse le site web et fournis :
1. **Structure** : Navigation, architecture, pages principales
2. **Design/UX** : Ergonomie, accessibilité, responsive
3. **Contenu** : Qualité, SEO, messaging
4. **Points forts** : Ce qui fonctionne bien
5. **Axes d'amélioration** : Recommandations concrètes
"""

class MarketResearchSkill(MarkdownSkill):
    """Recherche et analyse de marché."""

    skill_id = "market-research"
    name = "Recherche Marché"
    description = "Analyse de marché complète"
    output_type = SkillOutputType.ANALYSIS

    def get_input_schema(self) -> dict[str, InputField]:
        return {
            'sector': InputField(
                type='text',
                label='Secteur/Produit',
                placeholder='Ex: Formation IA pour TPE',
                required=True,
            ),
            'geography': InputField(
                type='text',
                label='Zone géographique',
                placeholder='Ex: France, Europe, Monde',
                default='France',
                required=False,
            ),
            'focus': InputField(
                type='select',
                label='Focus',
                options=['Vue d\'ensemble', 'Tendances', 'Concurrence', 'Opportunités'],
                default='Vue d\'ensemble',
                required=False,
            ),
        }

    def get_system_prompt_addition(self) -> str:
        return """
## Instructions pour l'analyse de marché

Fournis une analyse structurée :
1. **Marché** : Taille, croissance, segments
2. **Tendances** : Évolutions clés, drivers, freins
3. **Concurrence** : Acteurs principaux, positionnement
4. **Opportunités** : Niches, besoins non couverts
5. **Recommandations** : Stratégies d'entrée/développement
"""

class AnalyzeAIToolSkill(MarkdownSkill):
    """Analyse d'outils IA."""

    skill_id = "analyze-ai-tool"
    name = "Analyser Outil IA"
    description = "Explique un outil IA et ses cas d'usage"
    output_type = SkillOutputType.ANALYSIS

    def get_input_schema(self) -> dict[str, InputField]:
        return {
            'tool_name': InputField(
                type='text',
                label='Nom de l\'outil',
                placeholder='Ex: Claude, Midjourney, n8n',
                required=True,
            ),
            'context': InputField(
                type='textarea',
                label='Contexte d\'usage',
                placeholder='Comment veux-tu l\'utiliser ?',
                required=False,
            ),
        }

    def get_system_prompt_addition(self) -> str:
        return """
## Instructions pour l'analyse d'outil IA

Explique l'outil de manière claire et pratique :
1. **Présentation** : Qu'est-ce que c'est, à quoi ça sert
2. **Fonctionnalités clés** : Top 5 features
3. **Cas d'usage** : Exemples concrets par profil (solopreneur, TPE)
4. **Tarification** : Plans disponibles, rapport qualité-prix
5. **Comment débuter** : Steps pour commencer
6. **Alternatives** : Outils similaires
"""

class ExplainConceptSkill(MarkdownSkill):
    """Explication de concepts."""

    skill_id = "explain-concept"
    name = "Expliquer Concept"
    description = "Explique un concept de manière claire"
    output_type = SkillOutputType.TEXT

    def get_input_schema(self) -> dict[str, InputField]:
        return {
            'concept': InputField(
                type='text',
                label='Concept',
                placeholder='Ex: RAG, embeddings, fine-tuning',
                required=True,
            ),
            'level': InputField(
                type='select',
                label='Niveau',
                options=['Débutant', 'Intermédiaire', 'Avancé'],
                default='Débutant',
                required=False,
            ),
        }

    def get_system_prompt_addition(self) -> str:
        return """
## Instructions pour l'explication de concept

Explique le concept de manière pédagogique :
1. **Définition simple** : En une phrase claire
2. **Analogie** : Comparaison avec quelque chose de connu
3. **Fonctionnement** : Comment ça marche (adapté au niveau)
4. **Cas d'usage** : Quand l'utiliser
5. **Exemple concret** : Mise en pratique
6. **Pour aller plus loin** : Ressources
"""

class BestPracticesSkill(MarkdownSkill):
    """Best practices."""

    skill_id = "best-practices"
    name = "Best Practices"
    description = "Fournis les meilleures pratiques pour un domaine"
    output_type = SkillOutputType.TEXT

    def get_input_schema(self) -> dict[str, InputField]:
        return {
            'domain': InputField(
                type='text',
                label='Domaine',
                placeholder='Ex: Prompting IA, gestion de projet, SEO',
                required=True,
            ),
            'context': InputField(
                type='textarea',
                label='Contexte',
                placeholder='Ton contexte spécifique (optionnel)',
                required=False,
            ),
        }

    def get_system_prompt_addition(self) -> str:
        return """
## Instructions pour les best practices

Fournis un guide pratique et actionnable :
1. **Principes fondamentaux** : 3-5 règles d'or
2. **Do's** : Ce qu'il faut faire (liste claire)
3. **Don'ts** : Erreurs à éviter
4. **Checklist** : Actions concrètes à implémenter
5. **Exemples** : Avant/après ou cas d'usage
6. **Ressources** : Pour approfondir
"""

