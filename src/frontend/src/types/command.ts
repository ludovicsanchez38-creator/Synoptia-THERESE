/**
 * THÉRÈSE V3 - Types CommandDefinition
 *
 * Types TypeScript miroir du modèle Python backend.
 */

export type CommandSource = 'builtin' | 'skill' | 'user' | 'mcp';

export type CommandAction =
  | 'prompt'
  | 'form_then_prompt'
  | 'form_then_file'
  | 'image'
  | 'navigate'
  | 'rfc';

export interface CommandDefinition {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: string;
  source: CommandSource;
  action: CommandAction;
  prompt_template: string;
  skill_id: string | null;
  system_prompt: string | null;
  show_on_home: boolean;
  show_in_slash: boolean;
  sort_order: number;
  image_config: ImageConfig | null;
  navigate_target: string | null;
  is_editable: boolean;
}

export interface ImageConfig {
  provider: string;
  default_size?: string;
  default_quality?: string;
}

export interface CreateUserCommandRequest {
  name: string;
  description?: string;
  icon?: string;
  category?: string;
  prompt_template?: string;
  show_on_home?: boolean;
  show_in_slash?: boolean;
}

export interface UpdateUserCommandRequest {
  name?: string;
  description?: string;
  icon?: string;
  category?: string;
  prompt_template?: string;
  show_on_home?: boolean;
  show_in_slash?: boolean;
}

export interface GenerateTemplateRequest {
  brief: string;
  context?: Array<{ role: string; content: string }>;
}

export interface GenerateTemplateResponse {
  name: string;
  description: string;
  icon: string;
  category: string;
  prompt_template: string;
}

/** Catégories ordonnées pour l'affichage accueil */
export const COMMAND_CATEGORIES = [
  { id: 'production', label: 'Produire', icon: 'Sparkles' },
  { id: 'analyse', label: 'Comprendre', icon: 'Brain' },
  { id: 'organisation', label: 'Organiser', icon: 'GitBranch' },
] as const;

export type CommandCategory = typeof COMMAND_CATEGORIES[number]['id'];
