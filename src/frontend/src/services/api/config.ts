/**
 * THÉRÈSE v2 - Config API Module
 *
 * Configuration, preferences, API keys, profile, LLM config, onboarding.
 * Sprint 2 - PERF-2.2: Extracted from monolithic api.ts
 */

import { API_BASE, apiFetch, request, ApiError } from './core';


/**
 * Délais d'attente des appels de configuration (0.43.4).
 *
 * `API_TIMEOUT_MS` vaut 30 secondes et s'applique à TOUT appel passant par
 * `request()`. Douze fichiers de ce dossier posent un opt-out là où l'attente
 * est légitime — indexation, transcription, flux SSE. Ce fichier n'en posait
 * AUCUN, alors qu'il porte tout le parcours de premier usage.
 *
 * Sur la machine d'un testeur (AMD E1-7010, 1,5 GHz), le modèle d'embeddings a
 * mis 68 secondes à se charger et Ollama plusieurs minutes pour un premier
 * jeton. Trois de ses sept rapports partageaient cette cause unique : faux
 * timeout du profil, « Ollama grisé », backend « indisponible ».
 *
 * La réponse n'est pas de tout passer en attente illimitée. Un appel qui ne
 * revient jamais laisse l'utilisateur devant un écran figé, sans recours — ce
 * serait remplacer un défaut par un autre. Chaque famille reçoit donc un délai
 * justifié par ce qu'elle attend réellement.
 */
export const DELAIS_CONFIG = {
  /** Ollama charge le modèle en mémoire avant de répondre. Trente secondes ne
   *  suffisent pas sur une machine modeste ; l'utilisateur voyait
   *  « indisponible » alors qu'il fallait simplement attendre. Borné quand
   *  même : un serveur planté doit finir par le dire. */
  interrogationOllama: 120_000,

  /** Lecture d'un fichier, analyse, puis indexation éventuelle : aucune borne
   *  raisonnable, comme pour l'indexation dans `files.ts`. */
  importProfil: null,

  /** Lectures en base : si elles traînent, c'est une panne, et mieux vaut le
   *  dire vite que faire patienter. */
  lectureSimple: 30_000,
} as const;

// Preferences
export async function getPreferences(): Promise<Record<string, unknown>> {
  return request('/api/config/preferences');
}

export async function setPreference(
  key: string,
  value: unknown,
  category = 'general'
): Promise<void> {
  await request('/api/config/preferences', {
    method: 'POST',
    body: JSON.stringify({ key, value, category }),
  });
}

// API Keys
export interface ApiKeysResult {
  keys: Record<string, boolean>;
  corrupted: string[];
}

export async function getApiKeys(): Promise<Record<string, boolean>> {
  const result = await getApiKeysWithCorrupted();
  return result.keys;
}

export async function getApiKeysWithCorrupted(): Promise<ApiKeysResult> {
  const config = await request<{
    has_anthropic_key: boolean;
    has_mistral_key: boolean;
    has_openai_key: boolean;
    has_gemini_key: boolean;
    has_groq_key: boolean;
    has_grok_key: boolean;
    has_openrouter_key: boolean;
    has_openai_image_key: boolean;
    has_gemini_image_key: boolean;
    has_fal_key: boolean;
    has_brave_key: boolean;
    corrupted_keys: string[];
    api_keys?: Record<string, boolean>;
  }>('/api/config/');
  return {
    keys: {
      anthropic: config.has_anthropic_key,
      mistral: config.has_mistral_key,
      openai: config.has_openai_key,
      gemini: config.has_gemini_key,
      groq: config.has_groq_key,
      grok: config.has_grok_key,
      openrouter: config.has_openrouter_key,
      openai_image: config.has_openai_image_key,
      gemini_image: config.has_gemini_image_key,
      fal: config.has_fal_key,
      brave: config.has_brave_key,
      // Revue dette 0.43.4 : les champs has_*_key n'ont jamais suivi les
      // fournisseurs (perplexity, deepseek, puis glm/kimi/qwen/minimax :
      // clé enregistrée, jamais restituée). La carte générique fait foi.
      ...(config.api_keys ?? {}),
    },
    corrupted: config.corrupted_keys || [],
  };
}

export async function setApiKey(
  provider: string,
  key: string
): Promise<void> {
  await request('/api/config/api-key', {
    method: 'POST',
    body: JSON.stringify({ provider, api_key: key }),
  });
}

// User Profile
export interface UserProfile {
  name: string;
  nickname: string | null;
  company: string | null;
  role: string | null;
  context: string | null;
  email: string | null;
  location: string | null;
  address: string | null;
  siren: string | null;
  tva_intra: string | null;
  siret: string | null;
  code_ape: string | null;
  nda: string | null;
  display_name: string;
}

export interface UserProfileUpdate {
  name: string;
  nickname?: string;
  company?: string;
  role?: string;
  context?: string;
  email?: string;
  location?: string;
  address?: string;
  siren?: string;
  tva_intra?: string;
  siret?: string;
  code_ape?: string;
  nda?: string;
}

export interface WorkingDirectory {
  path: string | null;
  exists: boolean;
}

export async function getProfile(): Promise<UserProfile | null> {
  const response = await apiFetch(`${API_BASE}/api/config/profile`);
  if (response.status === 204 || response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new ApiError(response.status, response.statusText);
  }
  const data = await response.json();
  return data || null;
}

export async function setProfile(profile: UserProfileUpdate): Promise<UserProfile> {
  return request<UserProfile>('/api/config/profile', {
    method: 'POST',
    body: JSON.stringify(profile),
  });
}

export async function deleteProfile(): Promise<void> {
  await request<{ deleted: boolean }>('/api/config/profile', {
    method: 'DELETE',
  });
}

export async function importClaudeMd(filePath: string): Promise<UserProfile> {
  return request<UserProfile>('/api/config/profile/import-claude-md', {
    // Lecture de fichier + analyse + indexation : pas de borne utile.
    timeoutMs: DELAIS_CONFIG.importProfil,
    method: 'POST',
    body: JSON.stringify({ file_path: filePath }),
  });
}

export async function getWorkingDirectory(): Promise<WorkingDirectory> {
  return request<WorkingDirectory>('/api/config/working-directory');
}

export async function setWorkingDirectory(path: string): Promise<WorkingDirectory> {
  return request<WorkingDirectory>('/api/config/working-directory', {
    method: 'POST',
    body: JSON.stringify({ path }),
  });
}

// LLM Configuration
export type LLMProvider = 'anthropic' | 'openai' | 'gemini' | 'mistral' | 'grok' | 'openrouter' | 'perplexity' | 'deepseek' | 'infomaniak' | 'ollama'
  // Ajoutés le 24/08/2026 : compatibles OpenAI, ils héritent de la boucle d'outils.
  | 'glm'
  | 'kimi'
  | 'qwen'
  | 'minimax';

export interface LLMConfig {
  provider: LLMProvider;
  model: string;
  available_models: string[];
  /** Disponibilité réelle du modèle actif : clé cloud présente ou Ollama opérationnel. */
  available?: boolean;
  effort?: string | null;
  /** Adresse personnalisée du fournisseur courant (Qwen : espace de travail). */
  base_url?: string | null;
}

export interface OllamaModel {
  name: string;
  size: number | null;
  modified_at: string | null;
  digest: string | null;
  /** BUG-169 : un modèle sans outils ne peut déclencher aucune action. */
  gere_les_outils?: boolean;
  motif_indisponible?: string | null;
}

export interface OllamaStatus {
  available: boolean;
  base_url: string;
  models: OllamaModel[];
  error: string | null;
}

export interface SystemResources {
  total_ram_bytes: number | null;
  safe_local_model_ram_bytes: number | null;
  ollama_context_margin_bytes: number;
  detection_method: string;
}

export async function getLLMConfig(): Promise<LLMConfig> {
  // Cette route interroge Ollama et OpenRouter pour lister les modèles
  // disponibles : elle hérite donc de leur lenteur éventuelle.
  return request<LLMConfig>('/api/config/llm', {
    timeoutMs: DELAIS_CONFIG.interrogationOllama,
  });
}

export type LLMEffort = 'auto' | 'low' | 'medium' | 'high' | 'max';

export async function setLLMConfig(
  provider: LLMProvider,
  model: string,
  effort?: LLMEffort,
  baseUrl?: string
): Promise<LLMConfig> {
  // effort omis = conserver le reglage existant cote backend ; meme contrat
  // pour base_url (dette 0.43.4 : adresse d'espace de travail Qwen). Chaine
  // vide = effacer l'adresse enregistree.
  const corps: Record<string, string> = { provider, model };
  if (effort) corps.effort = effort;
  if (baseUrl !== undefined) corps.base_url = baseUrl;
  return request<LLMConfig>('/api/config/llm', {
    method: 'POST',
    body: JSON.stringify(corps),
  });
}

export async function getOllamaStatus(): Promise<OllamaStatus> {
  // Ollama peut charger un modèle avant de répondre : voir DELAIS_CONFIG.
  return request<OllamaStatus>('/api/config/ollama/status', {
    timeoutMs: DELAIS_CONFIG.interrogationOllama,
  });
}

export async function getSystemResources(): Promise<SystemResources> {
  return request<SystemResources>('/api/config/system-resources');
}

// Onboarding
export interface OnboardingStatus {
  completed: boolean;
  completed_at: string | null;
}

export async function getOnboardingStatus(): Promise<OnboardingStatus> {
  return request<OnboardingStatus>('/api/config/onboarding-complete');
}

export async function completeOnboarding(): Promise<OnboardingStatus> {
  return request<OnboardingStatus>('/api/config/onboarding-complete', {
    method: 'POST',
  });
}

// Web Search
export interface WebSearchStatus {
  enabled: boolean;
  providers: {
    gemini: string;
    others: string;
  };
  description: string;
}

export async function getWebSearchStatus(): Promise<WebSearchStatus> {
  return request<WebSearchStatus>('/api/config/web-search');
}

export async function setWebSearchEnabled(enabled: boolean): Promise<{ success: boolean; enabled: boolean }> {
  return request<{ success: boolean; enabled: boolean }>(`/api/config/web-search?enabled=${enabled}`, {
    method: 'POST',
  });
}

export async function hasGroqKey(): Promise<boolean> {
  const config = await request<{ has_groq_key: boolean }>('/api/config/');
  return config.has_groq_key;
}

// THERESE.md - Fichier de contexte personnel
export async function getThereseMd(): Promise<{ content: string; path: string; exists: boolean }> {
  return request('/api/config/therese-md');
}

export async function saveThereseMd(content: string): Promise<{ success: boolean; path: string }> {
  return request('/api/config/therese-md', {
    method: 'POST',
    body: JSON.stringify({ content }),
  });
}
