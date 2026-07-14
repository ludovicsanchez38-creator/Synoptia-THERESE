/**
 * THÉRÈSE v2 - Chat API Module
 *
 * Chat, streaming, and conversation management.
 * Sprint 2 - PERF-2.2: Extracted from monolithic api.ts
 */

import { API_BASE, apiFetch, request, ApiError } from './core';

// Types
export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  include_memory?: boolean;
  stream?: boolean;
  skill_id?: string;
  file_paths?: string[];
  disable_tools?: boolean;  // BUG-097 : RFC mini-chat - pas d'outils pour éviter les boucles
}

export interface ChatResponse {
  id: string;
  conversation_id: string;
  role: 'assistant';
  content: string;
  tokens_in?: number;
  tokens_out?: number;
  model?: string;
  confirmations?: Array<{
    confirmation_id: string;
    tool_name: string;
    arguments: Record<string, unknown>;
  }>;
  created_at: string;
}

export interface ExtractedContact {
  name: string;
  company: string | null;
  role: string | null;
  email: string | null;
  phone: string | null;
  confidence: number;
}

export interface ExtractedProject {
  name: string;
  description: string | null;
  budget: number | null;
  status: string | null;
  confidence: number;
}

export interface DetectedEntities {
  contacts: ExtractedContact[];
  projects: ExtractedProject[];
}

export interface StreamChunk {
  type: 'text' | 'done' | 'error' | 'status' | 'tool_result' | 'entities_detected' | 'conversation_id' | 'sources' | 'decomposition' | 'searching' | 'search_done' | 'synthesizing' | 'skill_file' | 'skill_file_error' | 'confirmation_required' | 'client_action';
  content: string;
  conversation_id?: string;
  message_id?: string;
  entities?: DetectedEntities;
  tool_name?: string;
  skill_file?: {
    skill_id: string;
    file_id: string;
    file_name: string;
    file_size: number;
    download_url: string;
    format: string;
  };
  confirmation?: {
    confirmation_id: string;
    tool_name: string;
    arguments: Record<string, unknown>;
  };
  client_action?: {
    action: string;
    action_id: string;
    target?: string;
  };
  usage?: {
    input_tokens: number;
    output_tokens: number;
    cost_eur: number;
    model: string;
    provider?: string; // P0-IA-3 : badge local/cloud
  };
  provider?: string; // P0-IA-3 : provider LLM (event done)
  uncertainty?: {
    is_uncertain: boolean;
    confidence_level: 'high' | 'medium' | 'low';
    confidence_score: number;
    uncertainty_phrases: string[];
  };
}

export interface ConversationResponse {
  id: string;
  title: string | null;
  summary: string | null;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface MessageResponse {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  tokens_in: number | null;
  tokens_out: number | null;
  model: string | null;
  provider?: string | null; // P0-IA-3 : badge local/cloud par message
  extra_data?: string | null; // BUG-130 : JSON {skill_file: {...}} pour restaurer le fichier généré
  created_at: string;
}

// Chat - Non-streaming
export async function sendMessage(req: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>('/api/chat/send', {
    method: 'POST',
    body: JSON.stringify({ ...req, stream: false }),
  });
}

// Chat - Streaming (SSE)
export async function* streamMessage(
  req: ChatRequest,
  signal?: AbortSignal,
): AsyncGenerator<StreamChunk> {
  const url = `${API_BASE}/api/chat/send`;
  const response = await apiFetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...req, stream: true }),
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
            const chunk = JSON.parse(data) as StreamChunk;
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

// Deep Research - Streaming (SSE)
export interface DeepResearchRequest {
  question: string;
  conversation_id?: string;
  max_queries?: number;
}

export async function* streamDeepResearch(
  req: DeepResearchRequest,
  signal?: AbortSignal,
): AsyncGenerator<StreamChunk> {
  const url = `${API_BASE}/api/chat/deep-research`;
  const response = await apiFetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
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
            const chunk = JSON.parse(data) as StreamChunk;
            yield chunk;
            if (chunk.type === 'done' || chunk.type === 'error') {
              return;
            }
          } catch {
            // Ignore parse errors
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

// Conversations
export async function listConversations(
  limit = 50,
  offset = 0
): Promise<ConversationResponse[]> {
  return request<ConversationResponse[]>(
    `/api/chat/conversations?limit=${limit}&offset=${offset}`
  );
}

export async function getConversation(id: string): Promise<ConversationResponse> {
  return request<ConversationResponse>(`/api/chat/conversations/${id}`);
}

export async function createConversation(title?: string): Promise<ConversationResponse> {
  return request<ConversationResponse>('/api/chat/conversations', {
    method: 'POST',
    body: JSON.stringify({ title: title || 'Nouvelle conversation' }),
  });
}

export async function renameConversation(id: string, title: string): Promise<ConversationResponse> {
  return request<ConversationResponse>(`/api/chat/conversations/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ title }),
  });
}

export async function getConversationMessages(
  conversationId: string,
  limit = 100
): Promise<MessageResponse[]> {
  return request<MessageResponse[]>(
    `/api/chat/conversations/${conversationId}/messages?limit=${limit}`
  );
}

export async function deleteConversation(id: string): Promise<void> {
  await request<{ deleted: boolean }>(`/api/chat/conversations/${id}`, {
    method: 'DELETE',
  });
}

export interface ConversationExportResponse {
  success: boolean;
  format: 'md' | 'docx';
  file_name: string;
  download_url: string;
}

/**
 * Exporte une conversation en fichier (md/docx) puis déclenche le
 * téléchargement.
 *
 * `download_url` renvoyé par le backend est un chemin RELATIF - `apiFetch`
 * ne le préfixe jamais (revue finale du 07/07/2026, jumeau du finding
 * bloquant 2 de `documents.ts::downloadExportedDocument`, même bug, même
 * fix). Sans `API_BASE`, cassé dès que le front n'est pas sur l'origine
 * backend (toujours le cas : localhost:1420 en dev, tauri://localhost
 * packagé).
 */
export async function exportConversation(
  id: string,
  format: 'md' | 'docx'
): Promise<void> {
  const exported = await request<ConversationExportResponse>(
    `/api/chat/conversations/${id}/export?format=${format}`
  );
  const response = await apiFetch(`${API_BASE}${exported.download_url}`);
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

export interface ConfirmToolResponse {
  status: 'executed' | 'cancelled';
  tool_name: string;
  result?: string;
}

// US-002 : valide (ou annule) une action sensible mise en attente (ex. send_email).
export async function confirmTool(
  confirmationId: string,
  approved: boolean
): Promise<ConfirmToolResponse> {
  return request<ConfirmToolResponse>('/api/chat/confirm-tool', {
    method: 'POST',
    body: JSON.stringify({ confirmation_id: confirmationId, approved }),
  });
}
