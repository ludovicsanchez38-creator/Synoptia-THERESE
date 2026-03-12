import {
  Sparkles,
  Brain,
  GitBranch,
  Plus,
  FileText,
  FileSpreadsheet,
  Presentation,
  Globe,
  type LucideIcon,
} from 'lucide-react';

/**
 * Format de fichier généré par un skill
 */
export type FileFormat = 'docx' | 'pptx' | 'xlsx' | 'html' | 'pdf';

/**
 * Provider de génération d'images
 */
export type ImageProvider = 'gpt-image-1.5' | 'nanobanan-pro' | 'fal-flux-pro';

/**
 * Configuration de génération de fichier pour une sous-option
 */
export interface GeneratesFile {
  skillId: string;  // 'docx-pro', 'pptx-pro', 'xlsx-pro'
  format: FileFormat;
  icon?: LucideIcon;
}

/**
 * Configuration de génération d'image pour une sous-option
 */
export interface GeneratesImage {
  provider: ImageProvider;
  defaultSize?: string;
  defaultQuality?: 'low' | 'medium' | 'high';
}

export interface SubOption {
  id: string;
  label: string;
  prompt: string;
  /** ID du skill backend à utiliser (obligatoire pour skills enrichis) */
  skillId?: string;
  /** Si défini, cette option génère un fichier via un skill */
  generatesFile?: GeneratesFile;
  /** Si défini, cette option génère une image */
  generatesImage?: GeneratesImage;
  /** Comportement spécial (P1-A) */
  behavior?: 'create-command' | 'create-skill' | 'create-automation';
}

export interface GuidedAction {
  id: string;
  icon: LucideIcon;
  title: string;
  description: string;
  question: string;
  options: SubOption[];
  /** Variante visuelle (P1-A) */
  variant?: 'default' | 'personnaliser';
}

export const GUIDED_ACTIONS: GuidedAction[] = [
  // ============================================
  // PRODUIRE - Créer du contenu nouveau (8 options)
  // ============================================
  {
    id: 'produire',
    icon: Sparkles,
    title: 'Produire',
    description: 'Créer du contenu nouveau',
    question: 'Que veux-tu produire ?',
    options: [
      {
        id: 'email',
        label: 'Email pro',
        prompt: 'Rédige un email professionnel à propos de [sujet]. Contexte : [destinataire, ton souhaité].',
        skillId: 'email-pro',
      },
      {
        id: 'linkedin',
        label: 'Post LinkedIn',
        prompt: 'Rédige un post LinkedIn engageant sur [sujet]. Style : informatif et personnel.',
        skillId: 'linkedin-post',
      },
      {
        id: 'proposal',
        label: 'Proposition commerciale',
        prompt: 'Aide-moi à rédiger une proposition commerciale pour [client/projet]. Budget estimé : [montant].',
        skillId: 'proposal-pro',
      },
      {
        id: 'document',
        label: 'Document Word',
        prompt: 'Crée un document structuré sur [sujet]. Format souhaité : [rapport, guide, procédure].',
        skillId: 'docx-pro',
        generatesFile: {
          skillId: 'docx-pro',
          format: 'docx',
          icon: FileText,
        },
      },
      {
        id: 'presentation',
        label: 'Présentation PPT',
        prompt: 'Crée une présentation PowerPoint sur [sujet]. [X] slides. Public cible : [audience].',
        skillId: 'pptx-pro',
        generatesFile: {
          skillId: 'pptx-pro',
          format: 'pptx',
          icon: Presentation,
        },
      },
      {
        id: 'dashboard',
        label: 'Tableur Excel',
        prompt: 'Crée un tableau de bord Excel pour suivre [KPIs]. Sources de données : [liste].',
        skillId: 'xlsx-pro',
        generatesFile: {
          skillId: 'xlsx-pro',
          format: 'xlsx',
          icon: FileSpreadsheet,
        },
      },
      {
        id: 'webpage',
        label: 'Page Web',
        prompt: 'Crée une page web pour [sujet/entreprise]. Type : [landing page, portfolio, mini-site]. Sections souhaitées : [hero, services, tarifs, contact].',
        skillId: 'html-web',
        generatesFile: {
          skillId: 'html-web',
          format: 'html',
          icon: Globe,
        },
      },
      {
        id: 'image-openai',
        label: 'Image IA (GPT)',
        prompt: 'Génère une image de [description détaillée]. Style : [réaliste, illustration, artistique].',
        generatesImage: {
          provider: 'gpt-image-1.5',
          defaultSize: '1024x1024',
          defaultQuality: 'high',
        },
      },
      {
        id: 'image-gemini',
        label: 'Image IA (Gemini)',
        prompt: 'Génère une image de [description détaillée]. Style : [réaliste, illustration, artistique].',
        generatesImage: {
          provider: 'nanobanan-pro',
          defaultSize: '2K',
          defaultQuality: 'high',
        },
      },
      {
        id: 'image-fal',
        label: 'Image IA (Fal)',
        prompt: 'Génère une image de [description détaillée]. Style : [réaliste, illustration, artistique].',
        generatesImage: {
          provider: 'fal-flux-pro',
          defaultQuality: 'high',
        },
      },
    ],
  },

  // ============================================
  // COMPRENDRE - Analyser et apprendre (7 options)
  // ============================================
  {
    id: 'comprendre',
    icon: Brain,
    title: 'Comprendre',
    description: 'Analyser et apprendre',
    question: 'Que veux-tu comprendre ?',
    options: [
      {
        id: 'excel',
        label: 'Fichier Excel',
        prompt: 'Analyse ce fichier Excel et identifie les tendances clés, anomalies et insights.',
        skillId: 'analyze-xlsx',
      },
      {
        id: 'pdf',
        label: 'Document PDF',
        prompt: 'Résume les points essentiels de ce PDF et extrais les informations importantes.',
        skillId: 'analyze-pdf',
      },
      {
        id: 'website',
        label: 'Site web',
        prompt: 'Analyse le site [URL] : structure, contenu, points forts et axes d\'amélioration.',
        skillId: 'analyze-website',
      },
      {
        id: 'market',
        label: 'Marché',
        prompt: 'Fais une analyse de marché pour [secteur/produit] : tendances, concurrence, opportunités.',
        skillId: 'market-research',
      },
      {
        id: 'ai-tool',
        label: 'Outil IA',
        prompt: 'Explique-moi [outil IA] : fonctionnalités clés, cas d\'usage, bonnes pratiques pour débuter.',
        skillId: 'analyze-ai-tool',
      },
      {
        id: 'concept',
        label: 'Concept',
        prompt: 'Explique-moi [concept] de manière simple. Exemples concrets et applications pratiques.',
        skillId: 'explain-concept',
      },
      {
        id: 'best-practices',
        label: 'Bonnes pratiques',
        prompt: 'Quelles sont les meilleures pratiques pour [domaine] ? Standards actuels et erreurs courantes.',
        skillId: 'best-practices',
      },
    ],
  },

  // ============================================
  // ORGANISER - Planifier et automatiser (5 options)
  // ============================================
  {
    id: 'organiser',
    icon: GitBranch,
    title: 'Organiser',
    description: 'Planifier et automatiser',
    question: 'Que veux-tu organiser ?',
    options: [
      {
        id: 'meeting',
        label: 'Réunion',
        prompt: 'Prépare une réunion sur [sujet]. Participants : [liste]. Durée : [temps]. Objectifs à atteindre.',
        skillId: 'plan-meeting',
      },
      {
        id: 'project',
        label: 'Projet',
        prompt: 'Crée un plan de projet pour [nom]. Phases, jalons, livrables et estimation des ressources.',
        skillId: 'plan-project',
      },
      {
        id: 'week',
        label: 'Semaine',
        prompt: 'Organise ma semaine. Priorités : [tâches urgentes]. Objectifs : [ce que je veux accomplir].',
        skillId: 'plan-week',
      },
      {
        id: 'goals',
        label: 'Objectifs',
        prompt: 'Définis des objectifs SMART pour [domaine]. Horizon : [trimestre/année]. Métriques de suivi.',
        skillId: 'plan-goals',
      },
      {
        id: 'workflow',
        label: 'Workflow',
        prompt: 'Crée un workflow d\'automatisation pour [tâche]. Plateforme : [n8n/Make/Zapier/autre].',
        skillId: 'workflow-automation',
      },
    ],
  },

  // ============================================
  // PERSONNALISER - Créer ses propres commandes (3 options)
  // ============================================
  {
    id: 'personnaliser',
    icon: Plus,
    title: 'Personnaliser',
    description: 'Créer tes propres outils',
    question: 'Que veux-tu créer ?',
    variant: 'personnaliser',
    options: [
      {
        id: 'create-command',
        label: 'Créer une commande',
        prompt: '',
        behavior: 'create-command',
      },
      {
        id: 'create-skill',
        label: 'Créer une skill',
        prompt: 'Je veux créer une nouvelle skill pour THÉRÈSE. Aide-moi à définir : le nom, la description, les inputs nécessaires et le prompt système.',
        behavior: 'create-skill',
      },
      {
        id: 'create-automation',
        label: 'Créer une automatisation',
        prompt: 'Je veux créer une automatisation personnalisée. Aide-moi à définir : le déclencheur, les étapes et les outils à connecter.',
        behavior: 'create-automation',
      },
    ],
  },
];
