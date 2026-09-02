import { type LucideIcon } from 'lucide-react';

/**
 * Format de fichier généré par un skill
 */
export type FileFormat = 'docx' | 'pptx' | 'xlsx' | 'html' | 'pdf';

/**
 * Provider de génération d'images
 */
export type ImageProvider = 'gpt-image-2' | 'nanobanan-pro' | 'fal-flux-pro';

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

// B-094 : `GUIDED_ACTIONS` a été retiré avec `GuidedPrompts`, son unique
// lecteur. Les types ci-dessus restent utilisés par CommandExecutor et les
// panneaux de skills ; c'est le catalogue de l'ancien écran guidé qui part.
