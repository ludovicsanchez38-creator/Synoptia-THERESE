/**
 * THÉRÈSE v2 - Config API Module
 *
 * Configuration, preferences, API keys, profile, LLM config, onboarding.
 * Sprint 2 - PERF-2.2: Extracted from monolithic api.ts
 */

import { API_BASE, apiFetch, request, ApiError } from './core';

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
export async function getApiKeys(): Promise<Record<string, boolean>> {
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
  }>('/api/config/');
  return {
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
export type LLMProvider = 'anthropic' | 'openai' | 'gemini' | 'mistral' | 'grok' | 'openrouter' | 'ollama';

export interface LLMConfig {
  provider: LLMProvider;
  model: string;
  available_models: string[];
}

export interface OllamaModel {
  name: string;
  size: number | null;
  modified_at: string | null;
  digest: string | null;
}

export interface OllamaStatus {
  available: boolean;
  base_url: string;
  models: OllamaModel[];
  error: string | null;
}

export async function getLLMConfig(): Promise<LLMConfig> {
  return request<LLMConfig>('/api/config/llm');
}

export async function setLLMConfig(
  provider: LLMProvider,
  model: string
): Promise<LLMConfig> {
  return request<LLMConfig>('/api/config/llm', {
    method: 'POST',
    body: JSON.stringify({ provider, model }),
  });
}

export async function getOllamaStatus(): Promise<OllamaStatus> {
  return request<OllamaStatus>('/api/config/ollama/status');
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
