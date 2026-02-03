/**
 * THERESE v2 - User Commands API
 *
 * CRUD pour les commandes utilisateur personnalisees.
 */

import { request } from './core';

// --- Types ---

export interface UserCommand {
  name: string;
  description: string;
  category: string;
  icon: string;
  show_on_home: boolean;
  content: string;
  created_at?: string;
  updated_at?: string;
}

export interface CreateCommandRequest {
  name: string;
  description?: string;
  category?: string;
  icon?: string;
  show_on_home?: boolean;
  content?: string;
}

// --- Functions ---

export async function listUserCommands(): Promise<UserCommand[]> {
  return request<UserCommand[]>('/api/commands/user');
}

export async function getUserCommand(name: string): Promise<UserCommand> {
  return request<UserCommand>(`/api/commands/user/${encodeURIComponent(name)}`);
}

export async function createUserCommand(data: CreateCommandRequest): Promise<UserCommand> {
  return request<UserCommand>('/api/commands/user', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateUserCommand(
  name: string,
  data: Partial<CreateCommandRequest>,
): Promise<UserCommand> {
  return request<UserCommand>(`/api/commands/user/${encodeURIComponent(name)}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteUserCommand(name: string): Promise<void> {
  await request(`/api/commands/user/${encodeURIComponent(name)}`, {
    method: 'DELETE',
  });
}
