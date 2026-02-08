/**
 * THÉRÈSE v2 - Personalisation API Module
 *
 * Templates, comportement LLM et visibilité des fonctionnalités.
 */

import { request } from './core';

export interface PromptTemplate {
  id: string;
  name: string;
  prompt: string;
  category: string;
  icon: string | null;
  created_at: string;
  updated_at: string;
}

export interface PromptTemplateCreate {
  name: string;
  prompt: string;
  category?: string;
  icon?: string;
}

export interface LLMBehaviorSettings {
  custom_system_prompt: string;
  use_custom_system_prompt: boolean;
  response_style: 'concise' | 'detailed' | 'creative';
  language: 'french' | 'english' | 'auto';
  include_memory_context: boolean;
  max_history_messages: number;
}

export interface FeatureVisibilitySettings {
  show_board: boolean;
  show_calculators: boolean;
  show_image_generation: boolean;
  show_voice_input: boolean;
  show_file_browser: boolean;
  show_mcp_tools: boolean;
  show_guided_prompts: boolean;
  show_entity_suggestions: boolean;
}

export interface PersonalisationStatus {
  templates_count: number;
  templates_by_category: Record<string, number>;
  llm_behavior: LLMBehaviorSettings;
  feature_visibility: FeatureVisibilitySettings;
}

export async function listPromptTemplates(category?: string): Promise<PromptTemplate[]> {
  const url = category
    ? `/api/personalisation/templates?category=${encodeURIComponent(category)}`
    : '/api/personalisation/templates';
  return request<PromptTemplate[]>(url);
}

export async function createPromptTemplate(template: PromptTemplateCreate): Promise<PromptTemplate> {
  return request<PromptTemplate>('/api/personalisation/templates', {
    method: 'POST',
    body: JSON.stringify(template),
  });
}

export async function getPromptTemplate(id: string): Promise<PromptTemplate> {
  return request<PromptTemplate>(`/api/personalisation/templates/${id}`);
}

export async function updatePromptTemplate(
  id: string,
  updates: Partial<PromptTemplateCreate>
): Promise<PromptTemplate> {
  return request<PromptTemplate>(`/api/personalisation/templates/${id}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
}

export async function deletePromptTemplate(id: string): Promise<void> {
  await request<{ deleted: boolean }>(`/api/personalisation/templates/${id}`, {
    method: 'DELETE',
  });
}

export async function getLLMBehavior(): Promise<LLMBehaviorSettings> {
  return request<LLMBehaviorSettings>('/api/personalisation/llm-behavior');
}

export async function setLLMBehavior(settings: LLMBehaviorSettings): Promise<LLMBehaviorSettings> {
  return request<LLMBehaviorSettings>('/api/personalisation/llm-behavior', {
    method: 'POST',
    body: JSON.stringify(settings),
  });
}

export async function getFeatureVisibility(): Promise<FeatureVisibilitySettings> {
  return request<FeatureVisibilitySettings>('/api/personalisation/features');
}

export async function setFeatureVisibility(
  settings: FeatureVisibilitySettings
): Promise<FeatureVisibilitySettings> {
  return request<FeatureVisibilitySettings>('/api/personalisation/features', {
    method: 'POST',
    body: JSON.stringify(settings),
  });
}

export async function getPersonalisationStatus(): Promise<PersonalisationStatus> {
  return request<PersonalisationStatus>('/api/personalisation/status');
}
