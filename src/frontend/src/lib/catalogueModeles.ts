/**
 * Catalogue des modèles cloud - servi par le backend, décoré en local.
 *
 * Dette 0.43.4 : quatre copies du catalogue vivaient dans le frontend
 * (onboarding, réglages, et leurs variantes) et divergeaient déjà -
 * l'onboarding proposait encore gpt-5.3-codex, retiré partout ailleurs
 * parce que son API ne supporte pas chat/completions. La LISTE vient
 * désormais de `GET /api/config/llm/models/{provider}`, la même source que
 * le backend utilise pour valider ; les noms lisibles et les badges restent
 * une décoration locale. Les modèles hors catalogue gardent un nom lisible
 * et un repère lorsque leur fournisseur est inconnu.
 *
 * Les listes statiques des composants deviennent un REPLI hors-ligne : si la
 * route échoue, on affiche ce qu'on connaît plutôt qu'un sélecteur vide.
 */
import catalogueGenere from './modelesCatalogue.generated.json';
import { request } from '../services/api/core';
import type { LLMProvider } from '../services/api/config';

export interface ModeleDecore {
  id: string;
  name: string;
  badge?: string;
}

/** Décorations connues ; les autres noms sont dérivés de leur identifiant. */
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
  // M1, 9 octobre 2026. Mêmes noms que le repli hors ligne.
  'claude-fable-5-1': { name: 'Claude Fable 5.1', badge: 'Le plus capable' },
  'claude-sonnet-5-5': { name: 'Claude Sonnet 5.5', badge: 'Équilibré' },
  'claude-haiku-5-5': { name: 'Claude Haiku 5.5', badge: 'Rapide' },
  'grok-4.7': { name: 'Grok 4.7', badge: 'Recommandé' },
  'gemini-3.8-flash': { name: 'Gemini 3.8 Flash', badge: 'Recommandé' },
  'mistral-medium-3-5': { name: 'Mistral Medium 3.5', badge: 'Équilibré' },
  'mistral-large-4': { name: 'Mistral Large 4', badge: 'Préversion' },
};

const cache = new Map<string, ModeleDecore[]>();

const modelesGeneres = Object.values(catalogueGenere).flat();

/** B-1097 : mêmes règles que libelle_modele, y compris hors catalogue. */
function libelleHorsCatalogue(id: string): string {
  // Un identifiant à étiquette (Ollama : « qwen3:8b ») est le nom que
  // l'utilisateur a installé : il s'affiche tel quel, comme avant B-1097.
  if (id.includes(':')) return id;
  const position = id.lastIndexOf('/');
  const prefixe = position < 0 ? '' : id.slice(0, position);
  const natif = id.slice(position + 1);
  const espacesConnus = new Set([
    ...Object.keys(catalogueGenere),
    ...modelesGeneres.filter((m) => m.id.includes('/')).map((m) => m.id.split('/')[0]),
  ]);
  const repere = prefixe && !espacesConnus.has(prefixe) ? ` (${prefixe})` : '';
  const marques: Record<string, string> = {
    gpt: 'GPT', glm: 'GLM', qwen: 'Qwen', grok: 'Grok', minimax: 'MiniMax', deepseek: 'DeepSeek',
  };
  const texte = natif.replace(/-(?:\d{8}|\d{4})(?=-|$)/g, '')
    .replace(/(\d)-(\d+)(?=-|$)/g, '$1.$2');
  const rendu = texte.replace(/-/g, ' ').split(/\s+/).filter(Boolean).map((m) =>
    /^\d+(?:\.\d+)?b$/i.test(m) ? m.toUpperCase()
      : marques[m.toLowerCase()] ?? m[0].toUpperCase() + m.slice(1).toLowerCase(),
  ).join(' ');
  return (natif.startsWith('gpt-') ? rendu.replace('GPT ', 'GPT-') : rendu) + repere;
}

/** Un modèle local (Ollama) garde le nom installé par l'utilisateur. */
export function decorer(ids: string[], fournisseur?: string): ModeleDecore[] {
  return ids.map((id) => {
    if (fournisseur === 'ollama') return { id, name: id };
    const defaut = Object.values(catalogueGenere).some((modeles) => modeles[0]?.id === id);
    let badge = DECORATIONS[id]?.badge;
    if (badge === 'Recommandé' && !defaut) badge = undefined;
    if (defaut && !badge) badge = 'Recommandé';
    return {
      id,
      name: modelesGeneres.find((m) => m.id === id)?.name ?? DECORATIONS[id]?.name ?? libelleHorsCatalogue(id),
      ...(badge ? { badge } : {}),
    };
  });
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

const METADONNEES_FOURNISSEURS: FournisseurConfig[] = [
  {
    id: 'anthropic',
    name: 'Claude (Anthropic)',
    description: 'Excellent en français, pour écrire et analyser',
    keyPrefix: 'sk-ant-',
    keyPlaceholder: 'sk-ant-...',
    consoleUrl: 'https://console.anthropic.com/settings/keys',
    models: [],
  },
  {
    id: 'openai',
    name: 'GPT (OpenAI)',
    description: 'GPT-6.1 Sol, GPT-6 (Sol, Astra, Luna) et 5.6 - Polyvalent et puissant',
    keyPrefix: 'sk-',
    keyPlaceholder: 'sk-...',
    consoleUrl: 'https://platform.openai.com/api-keys',
    models: [],
  },
  {
    id: 'gemini',
    name: 'Gemini (Google)',
    description: 'Gemini 4 Argon et Gemini Flash - Documents et analyse',
    keyPlaceholder: 'AIza...',
    consoleUrl: 'https://aistudio.google.com/app/apikey',
    models: [],
  },
  {
    id: 'mistral',
    name: 'Mistral AI',
    description: 'IA française souveraine',
    keyPlaceholder: '...',
    consoleUrl: 'https://console.mistral.ai/api-keys',
    models: [],
  },
  {
    id: 'grok',
    name: 'Grok (xAI)',
    description: 'Pour analyser et rédiger avec les modèles Grok',
    keyPrefix: 'xai-',
    keyPlaceholder: 'xai-...',
    consoleUrl: 'https://console.x.ai',
    models: [],
  },
  {
    id: 'openrouter',
    name: 'OpenRouter',
    description: 'Un seul compte pour plus de 200 modèles (Claude, GPT, Gemini, Llama...)',
    keyPrefix: 'sk-or-',
    keyPlaceholder: 'sk-or-v1-...',
    consoleUrl: 'https://openrouter.ai/keys',
    models: [],
  },
  {
    id: 'perplexity',
    name: 'Perplexity',
    description: 'Répond en s’appuyant sur une recherche sur le web',
    keyPrefix: 'pplx-',
    keyPlaceholder: 'pplx-...',
    consoleUrl: 'https://www.perplexity.ai/settings/api',
    models: [],
  },
  {
    id: 'deepseek',
    name: 'DeepSeek',
    description: 'DeepSeek V4 (Pro et Flash)',
    keyPrefix: 'sk-',
    keyPlaceholder: 'sk-...',
    consoleUrl: 'https://platform.deepseek.com/api_keys',
    models: [],
  },
  {
    id: 'glm',
    name: 'GLM (Z.ai)',
    description: 'GLM 5.3 - Conçu pour programmer et automatiser',
    keyPlaceholder: 'Clé API Z.ai...',
    consoleUrl: 'https://z.ai',
    models: [],
  },
  {
    id: 'kimi',
    name: 'Kimi (Moonshot AI)',
    description: 'Kimi K3 - Lit de très longs documents',
    keyPrefix: 'sk-',
    keyPlaceholder: 'sk-...',
    consoleUrl: 'https://platform.moonshot.ai',
    models: [],
  },
  {
    id: 'qwen',
    name: 'Qwen (Alibaba)',
    description: 'Qwen 3.8 - Nécessite l\'adresse de ton espace de travail',
    keyPrefix: 'sk-',
    keyPlaceholder: 'sk-...',
    consoleUrl: 'https://modelstudio.console.alibabacloud.com',
    models: [],
  },
  {
    id: 'minimax',
    name: 'MiniMax',
    description: 'MiniMax M3 - Généraliste économique',
    keyPlaceholder: 'Clé API MiniMax...',
    consoleUrl: 'https://platform.minimax.io',
    models: [],
  },
  {
    id: 'infomaniak',
    name: 'Infomaniak AI',
    description: 'IA souveraine suisse - serveurs en Suisse, RGPD',
    keyPlaceholder: 'Ton token API Infomaniak...',
    consoleUrl: 'https://www.infomaniak.com/fr/hebergement/ai-tools',
    models: [],
  },
  {
    id: 'ollama',
    name: 'Ollama (Local)',
    description: '100% local - Aucune clé API requise',
    models: [], // Chargé dynamiquement
  },
];


/** Généré depuis services/modeles_catalogue.py, ordre et défaut compris. */
export const FOURNISSEURS: FournisseurConfig[] = METADONNEES_FOURNISSEURS.map((f) => ({
  ...f,
  models: decorer((catalogueGenere[f.id as keyof typeof catalogueGenere] ?? []).map((m) => m.id)),
}));

/** Tête du catalogue généré, partagée par la mise en route et les réglages. */
export function modeleParDefaut(fournisseur: LLMProvider): string {
  return FOURNISSEURS.find((p) => p.id === fournisseur)?.models[0]?.id ?? '';
}
