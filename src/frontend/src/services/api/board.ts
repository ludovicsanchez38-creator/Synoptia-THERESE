/**
 * THÉRÈSE v2 - Board API Module
 *
 * Board de Décision Stratégique avec 5 conseillers IA.
 */

import { API_BASE, apiFetch, ApiError, request } from './core';

export type AdvisorRole = 'analyst' | 'strategist' | 'devil' | 'pragmatic' | 'visionary';

export interface AdvisorInfo {
  role: AdvisorRole;
  name: string;
  emoji: string;
  color: string;
  personality: string;
}

export interface BoardRequest {
  question: string;
  context?: string;
  advisors?: AdvisorRole[];
}

export interface BoardDeliberationChunk {
  type: 'web_search_start' | 'web_search_done' | 'advisor_start' | 'advisor_chunk' | 'advisor_done' | 'synthesis_start' | 'synthesis_chunk' | 'done' | 'error';
  role?: AdvisorRole;
  name?: string;
  emoji?: string;
  provider?: string;
  content: string;
}

export interface BoardSynthesis {
  consensus_points: string[];
  divergence_points: string[];
  recommendation: string;
  confidence: 'high' | 'medium' | 'low';
  next_steps: string[];
}

export interface BoardDecisionResponse {
  id: string;
  question: string;
  context?: string;
  recommendation: string;
  confidence: string;
  created_at: string;
}

export async function listAdvisors(): Promise<AdvisorInfo[]> {
  return request<AdvisorInfo[]>('/api/board/advisors');
}

export async function getAdvisor(role: AdvisorRole): Promise<AdvisorInfo> {
  return request<AdvisorInfo>(`/api/board/advisors/${role}`);
}

export async function* streamDeliberation(
  req: BoardRequest
): AsyncGenerator<BoardDeliberationChunk> {
  const url = `${API_BASE}/api/board/deliberate`;
  const response = await apiFetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
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
            const chunk = JSON.parse(data) as BoardDeliberationChunk;
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

export async function listBoardDecisions(limit = 50): Promise<BoardDecisionResponse[]> {
  return request<BoardDecisionResponse[]>(`/api/board/decisions?limit=${limit}`);
}

export async function getBoardDecision(id: string): Promise<{
  id: string;
  question: string;
  context?: string;
  opinions: Array<{
    role: AdvisorRole;
    name: string;
    emoji: string;
    content: string;
  }>;
  synthesis: BoardSynthesis;
  created_at: string;
}> {
  return request(`/api/board/decisions/${id}`);
}

export async function deleteBoardDecision(id: string): Promise<void> {
  await request<{ deleted: boolean }>(`/api/board/decisions/${id}`, {
    method: 'DELETE',
  });
}
