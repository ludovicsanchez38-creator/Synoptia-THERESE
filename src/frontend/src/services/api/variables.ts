/**
 * THÉRÈSE v2 - Variables utilisateur (chantier 4 Variables V1).
 * Mémoire de travail scalaire ou liste, substituée via {nom} dans le chat.
 * PAS un coffre à secrets : les valeurs partent au modèle à l'usage.
 */
import { API_BASE, apiFetch, ApiError } from './core';

export type VariableKind = 'text' | 'list';

export interface Variable {
  name: string;
  kind: VariableKind;
  value: string | string[];
  description: string | null;
  updated_at: string;
}

export interface VariablesPreview {
  resolved: string;
  unknown: string[];
  errors: string[];
  variables_revision: string;
}

async function _json<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const message = await response.text().catch(() => null);
    throw new ApiError(response.status, response.statusText, message || undefined);
  }
  return response.json() as Promise<T>;
}

export async function listVariables(): Promise<Variable[]> {
  return _json(await apiFetch(`${API_BASE}/api/variables`));
}

export async function createVariable(
  name: string,
  kind: VariableKind,
  value: string | string[],
  description?: string
): Promise<Variable> {
  return _json(
    await apiFetch(`${API_BASE}/api/variables`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, kind, value, description }),
    })
  );
}

export async function replaceVariable(
  name: string,
  value: string | string[]
): Promise<Variable> {
  return _json(
    await apiFetch(`${API_BASE}/api/variables/${encodeURIComponent(name)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value }),
    })
  );
}

export async function deleteVariable(name: string): Promise<void> {
  const response = await apiFetch(
    `${API_BASE}/api/variables/${encodeURIComponent(name)}`,
    { method: 'DELETE' }
  );
  if (!response.ok) {
    throw new ApiError(response.status, response.statusText);
  }
}

export async function previewVariables(text: string): Promise<VariablesPreview> {
  return _json(
    await apiFetch(`${API_BASE}/api/variables/preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    })
  );
}

/** Un token {nom} substituable est-il présent dans le texte ? (garde locale
 * avant d'appeler le preview - même forme que le backend) */
export function hasVariableTokens(text: string): boolean {
  return /(?<!\{)\{[a-z0-9_]{1,32}\}/.test(text);
}
