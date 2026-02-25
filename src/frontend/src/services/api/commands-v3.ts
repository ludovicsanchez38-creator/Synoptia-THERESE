/**
 * THÉRÈSE V3 - Commands API Client
 *
 * Client API pour le endpoint /api/v3/commands (commandes unifiées).
 */

import { request } from './core';
import type {
  CommandDefinition,
  CreateUserCommandRequest,
  UpdateUserCommandRequest,
  GenerateTemplateRequest,
  GenerateTemplateResponse,
} from '../../types/command';

/**
 * Liste toutes les commandes avec filtres optionnels.
 */
export async function fetchCommands(filters?: {
  category?: string;
  show_on_home?: boolean;
  show_in_slash?: boolean;
  source?: string;
}): Promise<CommandDefinition[]> {
  const params = new URLSearchParams();
  if (filters?.category) params.set('category', filters.category);
  if (filters?.show_on_home !== undefined) params.set('show_on_home', String(filters.show_on_home));
  if (filters?.show_in_slash !== undefined) params.set('show_in_slash', String(filters.show_in_slash));
  if (filters?.source) params.set('source', filters.source);

  const query = params.toString();
  const url = query ? `/api/v3/commands?${query}` : '/api/v3/commands';
  return request<CommandDefinition[]>(url);
}

/**
 * Récupère une commande par son ID.
 */
export async function fetchCommand(commandId: string): Promise<CommandDefinition> {
  return request<CommandDefinition>(`/api/v3/commands/${encodeURIComponent(commandId)}`);
}

/**
 * Récupère le schéma de formulaire d'une commande (si skill_id).
 */
export async function fetchCommandSchema(commandId: string): Promise<{
  command_id: string;
  skill_id: string;
  output_type: string;
  schema: Record<string, any>;
}> {
  return request(`/api/v3/commands/${encodeURIComponent(commandId)}/schema`);
}

/**
 * Crée une commande utilisateur.
 */
export async function createUserCommand(data: CreateUserCommandRequest): Promise<CommandDefinition> {
  return request<CommandDefinition>('/api/v3/commands/user', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Met à jour une commande utilisateur.
 */
export async function updateUserCommand(
  commandId: string,
  data: UpdateUserCommandRequest,
): Promise<CommandDefinition> {
  return request<CommandDefinition>(`/api/v3/commands/user/${encodeURIComponent(commandId)}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

/**
 * Supprime une commande utilisateur.
 */
export async function deleteUserCommand(commandId: string): Promise<void> {
  await request(`/api/v3/commands/user/${encodeURIComponent(commandId)}`, {
    method: 'DELETE',
  });
}

/**
 * RFC : Génère un template de commande depuis un brief.
 */
export async function generateTemplate(data: GenerateTemplateRequest): Promise<GenerateTemplateResponse> {
  return request<GenerateTemplateResponse>('/api/v3/commands/generate-template', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
