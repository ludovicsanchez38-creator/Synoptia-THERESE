import {
  Sparkles,
  Brain,
  GitBranch,
  Plus,
  FileText,
  FileSpreadsheet,
  Presentation,
  type LucideIcon,
} from 'lucide-react';

/**
 * Format de fichier genere par un skill
 */
export type FileFormat = 'docx' | 'pptx' | 'xlsx' | 'pdf';

/**
 * Provider de generation d'images
 */
export type ImageProvider = 'gpt-image-1.5' | 'nanobanan-pro' | 'fal-flux-pro';

/**
 * Configuration de generation de fichier pour une sous-option
 */
export interface GeneratesFile {
  skillId: string;  // 'docx-pro', 'pptx-pro', 'xlsx-pro'
  format: FileFormat;
  icon?: LucideIcon;
}

/**
 * Configuration de generation d'image pour une sous-option
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
  /** ID du skill backend a utiliser (obligatoire pour skills enrichis) */
  skillId?: string;
  /** Si defini, cette option genere un fichier via un skill */
  generatesFile?: GeneratesFile;
  /** Si defini, cette option genere une image */
  generatesImage?: GeneratesImage;
  /** Comportement special (P1-A) */
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
  // PRODUIRE - Creer du contenu nouveau (8 options)
  // ============================================
  {
    id: 'produire',
    icon: Sparkles,
    title: 'Produire',
    description: 'Creer du contenu nouveau',
    question: 'Que veux-tu produire ?',
    options: [
      {
        id: 'email',
        label: 'Email pro',
        prompt: 'Redige un email professionnel a propos de [sujet]. Contexte : [destinataire, ton souhaite].',
        skillId: 'email-pro',
      },
      {
        id: 'linkedin',
        label: 'Post LinkedIn',
        prompt: 'Redige un post LinkedIn engageant sur [sujet]. Style : informatif et personnel.',
        skillId: 'linkedin-post',
      },
      {
        id: 'proposal',
        label: 'Proposition commerciale',
        prompt: 'Aide-moi a rediger une proposition commerciale pour [client/projet]. Budget estime : [montant].',
        skillId: 'proposal-pro',
      },
      {
        id: 'document',
        label: 'Document Word',
        prompt: 'Cree un document structure sur [sujet]. Format souhaite : [rapport, guide, procedure].',
        skillId: 'docx-pro',
        generatesFile: {
          skillId: 'docx-pro',
          format: 'docx',
          icon: FileText,
        },
      },
      {
        id: 'presentation',
        label: 'Presentation PPT',
        prompt: 'Cree une presentation PowerPoint sur [sujet]. [X] slides. Public cible : [audience].',
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
        prompt: 'Cree un tableau de bord Excel pour suivre [KPIs]. Sources de donnees : [liste].',
        skillId: 'xlsx-pro',
        generatesFile: {
          skillId: 'xlsx-pro',
          format: 'xlsx',
          icon: FileSpreadsheet,
        },
      },
      {
        id: 'image-openai',
        label: 'Image IA (GPT)',
        prompt: 'Genere une image de [description detaillee]. Style : [realiste, illustration, artistique].',
        generatesImage: {
          provider: 'gpt-image-1.5',
          defaultSize: '1024x1024',
          defaultQuality: 'high',
        },
      },
      {
        id: 'image-gemini',
        label: 'Image IA (Gemini)',
        prompt: 'Genere une image de [description detaillee]. Style : [realiste, illustration, artistique].',
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
        prompt: 'Analyse ce fichier Excel et identifie les tendances cles, anomalies et insights.',
        skillId: 'analyze-xlsx',
      },
      {
        id: 'pdf',
        label: 'Document PDF',
        prompt: 'Resume les points essentiels de ce PDF et extrais les informations importantes.',
        skillId: 'analyze-pdf',
      },
      {
        id: 'website',
        label: 'Site web',
        prompt: 'Analyse le site [URL] : structure, contenu, points forts et axes d\'amelioration.',
        skillId: 'analyze-website',
      },
      {
        id: 'market',
        label: 'Marche',
        prompt: 'Fais une analyse de marche pour [secteur/produit] : tendances, concurrence, opportunites.',
        skillId: 'market-research',
      },
      {
        id: 'ai-tool',
        label: 'Outil IA',
        prompt: 'Explique-moi [outil IA] : fonctionnalites cles, cas d\'usage, bonnes pratiques pour debuter.',
        skillId: 'analyze-ai-tool',
      },
      {
        id: 'concept',
        label: 'Concept',
        prompt: 'Explique-moi [concept] de maniere simple. Exemples concrets et applications pratiques.',
        skillId: 'explain-concept',
      },
      {
        id: 'best-practices',
        label: 'Best practices',
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
        label: 'Reunion',
        prompt: 'Prepare une reunion sur [sujet]. Participants : [liste]. Duree : [temps]. Objectifs a atteindre.',
        skillId: 'plan-meeting',
      },
      {
        id: 'project',
        label: 'Projet',
        prompt: 'Cree un plan de projet pour [nom]. Phases, jalons, livrables et estimation des ressources.',
        skillId: 'plan-project',
      },
      {
        id: 'week',
        label: 'Semaine',
        prompt: 'Organise ma semaine. Priorites : [taches urgentes]. Objectifs : [ce que je veux accomplir].',
        skillId: 'plan-week',
      },
      {
        id: 'goals',
        label: 'Objectifs',
        prompt: 'Definis des objectifs SMART pour [domaine]. Horizon : [trimestre/annee]. Metriques de suivi.',
        skillId: 'plan-goals',
      },
      {
        id: 'workflow',
        label: 'Workflow',
        prompt: 'Cree un workflow d\'automatisation pour [tache]. Plateforme : [n8n/Make/Zapier/autre].',
        skillId: 'workflow-automation',
      },
    ],
  },

  // ============================================
  // PERSONNALISER - Creer ses propres commandes (3 options)
  // ============================================
  {
    id: 'personnaliser',
    icon: Plus,
    title: 'Personnaliser',
    description: 'Creer tes propres outils',
    question: 'Que veux-tu creer ?',
    variant: 'personnaliser',
    options: [
      {
        id: 'create-command',
        label: 'Creer une commande',
        prompt: '',
        behavior: 'create-command',
      },
      {
        id: 'create-skill',
        label: 'Creer une skill',
        prompt: 'Je veux creer une nouvelle skill pour THERESE. Aide-moi a definir : le nom, la description, les inputs necessaires et le prompt systeme.',
        behavior: 'create-skill',
      },
      {
        id: 'create-automation',
        label: 'Creer une automatisation',
        prompt: 'Je veux creer une automatisation personnalisee. Aide-moi a definir : le declencheur, les etapes et les outils a connecter.',
        behavior: 'create-automation',
      },
    ],
  },
];
