/**
 * THÉRÈSE - API Bibliothèque de prompts
 *
 * Service d'accès à la bibliothèque de prompts prêts à l'emploi.
 */

import { request } from './core';

export interface PromptItem {
  id: string;
  title: string;
  category: string;
  description: string;
  prompt: string;
  tags: string[];
}

export interface PromptCategory {
  category: string;
  label: string;
  prompts: PromptItem[];
}

export interface PromptLibraryResponse {
  total: number;
  categories: PromptCategory[];
}

export interface PromptSearchResponse {
  query: string;
  total: number;
  categories: PromptCategory[];
}

/**
 * Récupère la bibliothèque complète groupée par catégorie.
 */
export async function getPromptLibrary(): Promise<PromptLibraryResponse> {
  return request<PromptLibraryResponse>('/api/prompts/library');
}

/**
 * Recherche dans la bibliothèque par mots-clés.
 */
export async function searchPromptLibrary(query: string): Promise<PromptSearchResponse> {
  return request<PromptSearchResponse>(
    `/api/prompts/library/search?q=${encodeURIComponent(query)}`
  );
}
