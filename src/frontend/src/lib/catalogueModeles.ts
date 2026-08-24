/**
 * Catalogue des modèles cloud - servi par le backend, décoré en local.
 *
 * Dette 0.43.4 : quatre copies du catalogue vivaient dans le frontend
 * (onboarding, réglages, et leurs variantes) et divergeaient déjà -
 * l'onboarding proposait encore gpt-5.3-codex, retiré partout ailleurs
 * parce que son API ne supporte pas chat/completions. La LISTE vient
 * désormais de `GET /api/config/llm/models/{provider}`, la même source que
 * le backend utilise pour valider ; les noms lisibles et les badges restent
 * une décoration locale, et un identifiant sans décoration s'affiche tel
 * quel plutôt que de disparaître.
 *
 * Les listes statiques des composants deviennent un REPLI hors-ligne : si la
 * route échoue, on affiche ce qu'on connaît plutôt qu'un sélecteur vide.
 */
import { request } from '../services/api/core';
import type { LLMProvider } from '../services/api/config';

export interface ModeleDecore {
  id: string;
  name: string;
  badge?: string;
}

/** Décorations connues - un id absent d'ici s'affiche par son identifiant. */
export const DECORATIONS: Record<string, { name: string; badge?: string }> = {
  // GLM (Z.ai)
  'glm-5.3': { name: 'GLM 5.3', badge: 'Recommandé' },
  'glm-5.2': { name: 'GLM 5.2' },
  'glm-5.1': { name: 'GLM 5.1' },
  'glm-5': { name: 'GLM 5' },
  'glm-5-turbo': { name: 'GLM 5 Turbo', badge: 'Agents' },
  'glm-4.7': { name: 'GLM 4.7', badge: 'Économique' },
  // Kimi (Moonshot AI)
  'kimi-k3': { name: 'Kimi K3', badge: 'Recommandé' },
  'kimi-k2.7-code': { name: 'Kimi K2.7 Code', badge: 'Code' },
  'kimi-k2.7-code-highspeed': { name: 'Kimi K2.7 Code Rapide' },
  'kimi-k2.6': { name: 'Kimi K2.6' },
  'kimi-k2.5': { name: 'Kimi K2.5', badge: 'Économique' },
  // Qwen (Alibaba)
  'qwen3.8-max': { name: 'Qwen 3.8 Max', badge: 'Recommandé' },
  'qwen3.7-plus': { name: 'Qwen 3.7 Plus' },
  'qwen3.7-flash': { name: 'Qwen 3.7 Flash', badge: 'Économique' },
  'qwen3-coder-plus': { name: 'Qwen 3 Coder Plus', badge: 'Code' },
  // MiniMax
  'MiniMax-M3': { name: 'MiniMax M3', badge: 'Recommandé' },
  'MiniMax-M2.7': { name: 'MiniMax M2.7' },
  'MiniMax-M2.7-highspeed': { name: 'MiniMax M2.7 Rapide' },
  'MiniMax-M2.5': { name: 'MiniMax M2.5' },
  'MiniMax-M2.5-highspeed': { name: 'MiniMax M2.5 Rapide', badge: 'Économique' },
};

const cache = new Map<string, ModeleDecore[]>();

export function decorer(ids: string[]): ModeleDecore[] {
  return ids.map((id) => ({ id, ...(DECORATIONS[id] ?? { name: id }) }));
}

/**
 * Charge le catalogue d'un fournisseur cloud. Cache par session : le
 * catalogue ne change qu'avec le binaire. Retourne null si la route échoue -
 * l'appelant garde alors sa liste de repli, il ne montre jamais un vide.
 */
export async function chargerCatalogue(
  provider: string,
  fetcher: (p: string) => Promise<{ models: string[] }> = (p) =>
    request<{ models: string[] }>(`/api/config/llm/models/${p}`),
): Promise<ModeleDecore[] | null> {
  const connu = cache.get(provider);
  if (connu) return connu;
  try {
    const { models } = await fetcher(provider);
    if (!Array.isArray(models) || models.length === 0) return null;
    const decores = decorer(models);
    cache.set(provider, decores);
    return decores;
  } catch {
    return null;
  }
}

/**
 * Que devient la sélection quand la liste fraîche arrive ?
 *
 * Revue dette 0.43.4 : l'arrivée du catalogue corrigeait la sélection même
 * quand l'utilisateur venait de choisir un modèle à la main - un reclassement
 * silencieux. Règle : un choix EXPLICITE ne se corrige jamais ; un défaut
 * absent de la liste fraîche bascule sur le premier modèle servi.
 */
export function selectionApresCatalogue(
  actuelle: string,
  modeles: ModeleDecore[],
  choisieParLUtilisateur: boolean,
): string {
  if (choisieParLUtilisateur) return actuelle;
  if (modeles.some((m) => m.id === actuelle)) return actuelle;
  return modeles[0]?.id ?? actuelle;
}

/** Pour les tests : le cache est un état de module. */
export function _viderLeCache(): void {
  cache.clear();
}

/**
 * Le catalogue statique de REPLI - une seule copie pour toute l'application.
 *
 * Réglages et onboarding déclaraient chacun leur exemplaire, et ils
 * divergeaient déjà. La liste dynamique du backend reste la source ; ce bloc
 * ne sert que si la route échoue, et il alimente aussi les métadonnées que le
 * backend ne porte pas (nom du fournisseur, préfixe de clé, console).
 */
export interface FournisseurConfig {
  id: LLMProvider;
  name: string;
  description: string;
  keyPrefix?: string;
  keyPlaceholder?: string;
  consoleUrl?: string;
  models: ModeleDecore[];
}

export const FOURNISSEURS: FournisseurConfig[] = [
  {
    id: 'anthropic',
    name: 'Claude (Anthropic)',
    description: 'Recommandé - Excellent coding et français',
    keyPrefix: 'sk-ant-',
    keyPlaceholder: 'sk-ant-...',
    consoleUrl: 'https://console.anthropic.com/settings/keys',
    models: [
      // Fable 5 : modèle frontier Anthropic (1M contexte). Thinking toujours
      // actif, paramètres de sampling refusés - géré côté provider backend.
      { id: 'claude-fable-5', name: 'Claude Fable 5', badge: 'Frontier' },
      { id: 'claude-opus-5', name: 'Claude Opus 5', badge: 'Recommandé' },
      { id: 'claude-fable-5', name: 'Claude Fable 5', badge: 'Puissance max' },
      { id: 'claude-sonnet-5', name: 'Claude Sonnet 5', badge: 'Équilibré' },
      { id: 'claude-opus-4-8', name: 'Claude Opus 4.8' },
      { id: 'claude-sonnet-5', name: 'Claude Sonnet 5', badge: 'Recommandé' },
      { id: 'claude-sonnet-4-6', name: 'Claude Sonnet 4.6', badge: 'Équilibré' },
      { id: 'claude-haiku-4-5-20251001', name: 'Claude Haiku 4.5', badge: 'Rapide' },
    ],
  },
  {
    id: 'openai',
    name: 'GPT (OpenAI)',
    description: 'GPT-5.6 (Sol, Terra, Luna) et 5.5 - Polyvalent et puissant',
    keyPrefix: 'sk-',
    keyPlaceholder: 'sk-...',
    consoleUrl: 'https://platform.openai.com/api-keys',
    models: [
      // GPT-5.6 : GA du 09/07/2026 - trois variantes, six niveaux d'effort.
      { id: 'gpt-5.6-sol', name: 'GPT-5.6 Sol', badge: 'Frontier' },
      { id: 'gpt-5.6-terra', name: 'GPT-5.6 Terra', badge: 'Équilibré' },
      { id: 'gpt-5.6-luna', name: 'GPT-5.6 Luna', badge: 'Rapide' },
      { id: 'gpt-5.5', name: 'GPT-5.5', badge: 'Flagship' },
      { id: 'gpt-5.4', name: 'GPT-5.4' },
      { id: 'gpt-5.4-mini', name: 'GPT-5.4 mini' },
      { id: 'gpt-5.5-pro', name: 'GPT-5.5 pro', badge: 'Raisonnement' },
    ],
  },
  {
    id: 'gemini',
    name: 'Gemini (Google)',
    description: 'Gemini 3.x - Contexte 1M tokens',
    keyPlaceholder: 'AIza...',
    consoleUrl: 'https://aistudio.google.com/app/apikey',
    models: [
      { id: 'gemini-3.1-pro-preview', name: 'Gemini 3.1 Pro', badge: 'Flagship' },
      { id: 'gemini-3.7-flash', name: 'Gemini 3.7 Flash', badge: 'Recommandé' },
      { id: 'gemini-3.5-flash', name: 'Gemini 3.5 Flash' },
      { id: 'gemini-3.1-flash-lite', name: 'Gemini 3.1 Flash Lite', badge: 'Économique' },
    ],
  },
  {
    id: 'mistral',
    name: 'Mistral AI',
    description: 'IA française souveraine',
    keyPlaceholder: '...',
    consoleUrl: 'https://console.mistral.ai/api-keys',
    models: [
      { id: 'mistral-large-latest', name: 'Mistral Large 3', badge: 'Flagship' },
      // Medium 3.5 (avril 2026) : meilleur équilibre coût-performance Mistral.
      { id: 'mistral-medium-latest', name: 'Mistral Medium 3.5', badge: 'Équilibré' },
      { id: 'mistral-small-latest', name: 'Mistral Small 4', badge: 'Économique' },
      { id: 'mistral-large-2512', name: 'Mistral Large 3 (fixé)', badge: 'Stable' },
      { id: 'codestral-latest', name: 'Codestral', badge: 'Coding' },
      { id: 'devstral-small-latest', name: 'Devstral Small', badge: 'Dev' },
    ],
  },
  {
    id: 'grok',
    name: 'Grok (xAI)',
    description: 'Grok 4.5 - co-développé avec Cursor, 500k contexte',
    keyPrefix: 'xai-',
    keyPlaceholder: 'xai-...',
    consoleUrl: 'https://console.x.ai',
    models: [
      // ATTENTION : l'ID API est grok-4.5 avec un POINT (grok-4-5 -> 404).
      { id: 'grok-4.5', name: 'Grok 4.5', badge: 'Flagship' },
      { id: 'grok-4.6', name: 'Grok 4.6', badge: 'Recommandé' },
      { id: 'grok-4.5', name: 'Grok 4.5' },
      { id: 'grok-4.3', name: 'Grok 4.3' },
      { id: 'grok-4.20-0309-reasoning', name: 'Grok 4.20 Reasoning', badge: 'Raisonnement' },
      { id: 'grok-4.20-0309-non-reasoning', name: 'Grok 4.20', badge: 'Rapide' },
    ],
  },
  {
    id: 'openrouter',
    name: 'OpenRouter',
    description: 'Accès unifié à 200+ modèles (Claude, GPT, Gemini, Llama...)',
    keyPrefix: 'sk-or-',
    keyPlaceholder: 'sk-or-v1-...',
    consoleUrl: 'https://openrouter.ai/keys',
    models: [
      { id: 'anthropic/claude-sonnet-4-6', name: 'Claude Sonnet 4.6', badge: 'Recommandé' },
      { id: 'anthropic/claude-opus-5', name: 'Claude Opus 5', badge: 'Premium' },
      { id: 'anthropic/claude-opus-4-8', name: 'Claude Opus 4.8' },
      { id: 'openai/gpt-5.5', name: 'GPT-5.5' },
      { id: 'google/gemini-3.1-pro', name: 'Gemini 3.1 Pro' },
      { id: 'google/gemini-3.5-flash', name: 'Gemini 3.5 Flash' },
      { id: 'meta-llama/llama-4-maverick', name: 'Llama 4 Maverick', badge: 'Open Source' },
    ],
  },
  {
    id: 'perplexity',
    name: 'Perplexity',
    description: 'Recherche augmentée par IA (Sonar)',
    keyPrefix: 'pplx-',
    keyPlaceholder: 'pplx-...',
    consoleUrl: 'https://www.perplexity.ai/settings/api',
    models: [
      { id: 'sonar-pro', name: 'Sonar Pro', badge: 'Recherche' },
      { id: 'sonar', name: 'Sonar', badge: 'Rapide' },
      { id: 'sonar-reasoning-pro', name: 'Sonar Reasoning Pro', badge: 'Raisonnement' },
      { id: 'sonar-deep-research', name: 'Sonar Deep Research', badge: 'Recherche+' },
    ],
  },
  {
    id: 'deepseek',
    name: 'DeepSeek',
    description: 'DeepSeek V4 (Pro et Flash)',
    keyPrefix: 'sk-',
    keyPlaceholder: 'sk-...',
    consoleUrl: 'https://platform.deepseek.com/api_keys',
    models: [
      { id: 'deepseek-v4-pro', name: 'DeepSeek V4 Pro', badge: 'Flagship' },
      { id: 'deepseek-v4-flash', name: 'DeepSeek V4 Flash', badge: 'Rapide' },
    ],
  },
  {
    id: 'glm',
    name: 'GLM (Z.ai)',
    description: 'GLM 5.3 - Taillé pour le code et les agents',
    keyPlaceholder: 'Clé API Z.ai...',
    consoleUrl: 'https://z.ai',
    models: [
      { id: 'glm-5.3', name: 'GLM 5.3', badge: 'Recommandé' },
      { id: 'glm-5.2', name: 'GLM 5.2' },
      { id: 'glm-4.7', name: 'GLM 4.7', badge: 'Économique' },
    ],
  },
  {
    id: 'kimi',
    name: 'Kimi (Moonshot AI)',
    description: 'Kimi K3 - Contexte d\'un million de tokens',
    keyPrefix: 'sk-',
    keyPlaceholder: 'sk-...',
    consoleUrl: 'https://platform.moonshot.ai',
    models: [
      { id: 'kimi-k3', name: 'Kimi K3', badge: 'Recommandé' },
      { id: 'kimi-k2.7-code', name: 'Kimi K2.7 Code', badge: 'Code' },
      { id: 'kimi-k2.5', name: 'Kimi K2.5', badge: 'Économique' },
    ],
  },
  {
    id: 'qwen',
    name: 'Qwen (Alibaba)',
    description: 'Qwen 3.8 - Nécessite l\'adresse de ton espace de travail',
    keyPrefix: 'sk-',
    keyPlaceholder: 'sk-...',
    consoleUrl: 'https://modelstudio.console.alibabacloud.com',
    models: [
      { id: 'qwen3.8-max', name: 'Qwen 3.8 Max', badge: 'Recommandé' },
      { id: 'qwen3.7-flash', name: 'Qwen 3.7 Flash', badge: 'Économique' },
      { id: 'qwen3-coder-plus', name: 'Qwen 3 Coder Plus', badge: 'Code' },
    ],
  },
  {
    id: 'minimax',
    name: 'MiniMax',
    description: 'MiniMax M3 - Généraliste économique',
    keyPlaceholder: 'Clé API MiniMax...',
    consoleUrl: 'https://platform.minimax.io',
    models: [
      { id: 'MiniMax-M3', name: 'MiniMax M3', badge: 'Recommandé' },
      { id: 'MiniMax-M2.7', name: 'MiniMax M2.7' },
      { id: 'MiniMax-M2.5-highspeed', name: 'MiniMax M2.5 Rapide', badge: 'Économique' },
    ],
  },
  {
    id: 'infomaniak',
    name: 'Infomaniak AI',
    description: 'IA souveraine suisse - serveurs en Suisse, RGPD',
    keyPlaceholder: 'Ton token API Infomaniak...',
    consoleUrl: 'https://www.infomaniak.com/fr/hebergement/ai-tools',
    models: [
      { id: 'mix', name: 'Mix', badge: 'Polyvalent' },
      { id: 'mix-large', name: 'Mix Large', badge: 'Puissant' },
    ],
  },
  {
    id: 'ollama',
    name: 'Ollama (Local)',
    description: '100% local - Aucune clé API requise',
    models: [], // Chargé dynamiquement
  },
];
