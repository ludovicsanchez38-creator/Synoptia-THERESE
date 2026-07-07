/**
 * THÉRÈSE v2 - Documents API Module
 *
 * Atelier documentaire : CRUD documents/sections/pistes, génération de
 * trame, rédaction en streaming SSE, validation et export md/docx.
 * Miroir typé du router backend `app/routers/documents.py` (tâche D1).
 */

import { API_BASE, apiFetch, request, ApiError } from './core';

// ============================================================
// Types - Documents
// ============================================================

export type DocumentStatus = 'en_cours' | 'termine';
export type SectionStatus = 'vide' | 'brouillon' | 'validee';
export type PisteStatus = 'nouvelle' | 'exploree' | 'ignoree';

/** Document tel que renvoyé par la liste (sans trame ni pistes). */
export interface DocumentResponse {
  id: string;
  title: string;
  brief: string;
  status: DocumentStatus;
  project_id: string | null;
  contact_id: string | null;
  created_at: string;
  updated_at: string;
  sections_total: number;
  sections_validees: number;
}

export interface DocumentSection {
  id: string;
  document_id: string;
  title: string;
  brief: string;
  order: number;
  depth: number;
  content: string;
  summary: string;
  status: SectionStatus;
  orphan: boolean;
  created_at: string;
  updated_at: string;
}

export interface DocumentPiste {
  id: string;
  document_id: string;
  section_origine_id: string | null;
  texte: string;
  status: PisteStatus;
  created_at: string;
}

/** Document complet : trame (sections triées) + pistes (`GET /api/documents/{id}`). */
export interface DocumentDetail extends DocumentResponse {
  sections: DocumentSection[];
  pistes: DocumentPiste[];
}

export interface DocumentCreateRequest {
  title: string;
  brief: string;
  project_id?: string | null;
  contact_id?: string | null;
}

export interface SectionCreateRequest {
  title: string;
  brief?: string;
  order: number;
  depth?: number;
}

export interface SectionUpdateRequest {
  title?: string;
  brief?: string;
  content?: string;
  order?: number;
  depth?: number;
}

export interface SectionsReorderItem {
  id: string;
  order: number;
  depth: number;
}

export interface PisteCreateRequest {
  texte: string;
  section_origine_id?: string | null;
}

export interface DraftRequest {
  instruction?: string;
}

/** Chunk SSE émis par `POST /api/documents/sections/{id}/draft`. */
export interface DraftStreamChunk {
  type: 'text' | 'done' | 'error';
  content?: string;
  section_id?: string;
}

export interface DocumentExportResponse {
  success: boolean;
  format: 'md' | 'docx';
  file_name: string;
  download_url: string;
}

// ============================================================
// Erreur structurée du conflit de réorganisation (409)
// ============================================================

/**
 * Corps JSON renvoyé par `POST /{id}/sections/reorder` sur désaccord
 * d'ensemble d'ids (garde-fou anti-perte de données du backend). Forme
 * structurée dédiée - PAS l'enveloppe {code,message} générique des autres
 * erreurs de l'API.
 */
export interface ReorderConflictBody {
  code: string;
  message: string;
  missing_ids: string[];
  unknown_ids: string[];
}

export class ReorderConflictError extends Error {
  code: string;
  missing_ids: string[];
  unknown_ids: string[];

  constructor(body: ReorderConflictBody) {
    super(body.message);
    this.name = 'ReorderConflictError';
    this.code = body.code;
    this.missing_ids = body.missing_ids;
    this.unknown_ids = body.unknown_ids;
  }
}

// ============================================================
// Documents - CRUD
// ============================================================

export async function createDocument(payload: DocumentCreateRequest): Promise<DocumentResponse> {
  return request<DocumentResponse>('/api/documents', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function listDocuments(): Promise<DocumentResponse[]> {
  return request<DocumentResponse[]>('/api/documents');
}

export async function getDocument(id: string): Promise<DocumentDetail> {
  return request<DocumentDetail>(`/api/documents/${id}`);
}

export async function deleteDocument(id: string): Promise<{ success: boolean; message: string }> {
  return request<{ success: boolean; message: string }>(`/api/documents/${id}`, {
    method: 'DELETE',
  });
}

// ============================================================
// Trame - Génération et sections
// ============================================================

export async function generateOutline(documentId: string): Promise<DocumentSection[]> {
  return request<DocumentSection[]>(`/api/documents/${documentId}/outline`, {
    method: 'POST',
  });
}

export async function createSection(
  documentId: string,
  payload: SectionCreateRequest
): Promise<DocumentSection> {
  return request<DocumentSection>(`/api/documents/${documentId}/sections`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateSection(
  sectionId: string,
  payload: SectionUpdateRequest
): Promise<DocumentSection> {
  return request<DocumentSection>(`/api/documents/sections/${sectionId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

/**
 * Réorganise la trame d'un document. Sur désaccord d'ensemble d'ids, le
 * backend renvoie 409 avec un corps structuré {code,message,missing_ids,
 * unknown_ids} (PAS l'enveloppe {code,message} générique) - on le parse
 * nous-mêmes plutôt que de passer par `request()` pour ne pas perdre
 * missing_ids/unknown_ids dans un message d'erreur applati.
 */
export async function reorderSections(
  documentId: string,
  items: SectionsReorderItem[]
): Promise<DocumentSection[]> {
  const url = `${API_BASE}/api/documents/${documentId}/sections/reorder`;
  let response: Response;
  try {
    response = await apiFetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items }),
    });
  } catch {
    throw new ApiError(0, 'NetworkError', 'Impossible de contacter le serveur');
  }

  if (response.status === 409) {
    const body = await response.json().catch(() => null);
    if (body && Array.isArray(body.missing_ids) && Array.isArray(body.unknown_ids)) {
      throw new ReorderConflictError(body as ReorderConflictBody);
    }
    throw new ApiError(409, response.statusText, body?.message || body?.detail || 'Conflit de réorganisation');
  }

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    const message = data?.detail || data?.message || `Erreur ${response.status}`;
    throw new ApiError(response.status, response.statusText, message);
  }

  return response.json();
}

// ============================================================
// Rédaction - Streaming SSE + validation
// ============================================================

/**
 * Rédige (ou retouche) une section via le LLM, en streaming SSE. Suit le
 * pattern `streamMessage` (chat.ts:130) : parsing des lignes `data: {...}`,
 * arrêt sur le chunk terminal `done` ou `error`.
 */
export async function* draftSection(
  sectionId: string,
  instruction?: string,
  signal?: AbortSignal
): AsyncGenerator<DraftStreamChunk> {
  const url = `${API_BASE}/api/documents/sections/${sectionId}/draft`;
  const body: DraftRequest = instruction ? { instruction } : {};

  const response = await apiFetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => null);
    throw new ApiError(response.status, response.statusText, errorText || undefined);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('No response body');

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          if (!data || data === '[DONE]') continue;
          try {
            const chunk = JSON.parse(data) as DraftStreamChunk;
            yield chunk;
            if (chunk.type === 'done' || chunk.type === 'error') {
              return;
            }
          } catch {
            // Ignore parse errors for malformed chunks
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export async function validateSection(sectionId: string): Promise<DocumentSection> {
  return request<DocumentSection>(`/api/documents/sections/${sectionId}/validate`, {
    method: 'POST',
  });
}

// ============================================================
// Pistes
// ============================================================

export async function listPistes(documentId: string): Promise<DocumentPiste[]> {
  return request<DocumentPiste[]>(`/api/documents/${documentId}/pistes`);
}

export async function createPiste(
  documentId: string,
  payload: PisteCreateRequest
): Promise<DocumentPiste> {
  return request<DocumentPiste>(`/api/documents/${documentId}/pistes`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updatePiste(pisteId: string, status: PisteStatus): Promise<DocumentPiste> {
  return request<DocumentPiste>(`/api/documents/pistes/${pisteId}`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}

// ============================================================
// Export (md/docx)
// ============================================================

export async function exportDocument(
  documentId: string,
  format: 'md' | 'docx' = 'md'
): Promise<DocumentExportResponse> {
  return request<DocumentExportResponse>(`/api/documents/${documentId}/export?format=${format}`);
}

/**
 * Déclenche le téléchargement navigateur depuis les métadonnées renvoyées
 * par `exportDocument` (qui, lui, ne télécharge rien - décision D1). Même
 * mécanique que `exportConversation` (chat.ts:282) : fetch du blob, lien
 * `<a download>` éphémère cliqué puis retiré, URL objet révoquée.
 */
export async function downloadExportedDocument(exported: DocumentExportResponse): Promise<void> {
  const response = await apiFetch(exported.download_url);
  if (!response.ok) {
    throw new ApiError(response.status, response.statusText, 'Téléchargement impossible');
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = exported.file_name;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
