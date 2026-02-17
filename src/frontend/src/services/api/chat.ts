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
}

export interface ChatResponse {
  id: string;
  conversation_id: string;
  role: 'assistant';
  content: string;
  tokens_in?: number;
  tokens_out?: number;
  model?: string;
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
  type: 'text' | 'done' | 'error' | 'status' | 'tool_result' | 'entities_detected';
  content: string;
  conversation_id?: string;
  message_id?: string;
  entities?: DetectedEntities;
  tool_name?: string;
  usage?: {
    input_tokens: number;
    output_tokens: number;
    cost_eur: number;
    model: string;
  };
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
