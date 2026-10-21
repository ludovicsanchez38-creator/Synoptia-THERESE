import { request } from './core';

export type MemoryKind = 'preference' | 'fait' | 'decision' | 'correction';
export interface MemoryCard {
  id: string; kind: MemoryKind; subject: string; title: string; content: string; reason: string;
  version: number; protected: boolean; state: 'active' | 'archivee';
  author: string; last_author: string; created_at: string; updated_at: string;
  scope: 'global' | 'project'; scope_id?: string | null; scope_name: string;
  contact_id?: string | null; contact_name?: string | null;
  conversation_id?: string | null; message_id?: string | null; source_deleted?: boolean;
}
export interface CardPage { items: MemoryCard[]; total: number }
export function getMemoryCards(params: Record<string, string | number> = {}): Promise<CardPage> {
  const query = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)]));
  return request(`/api/memory/cards?${query}`);
}
export const getMemoryCard = (id: string): Promise<MemoryCard> => request(`/api/memory/cards/${encodeURIComponent(id)}`);
export const getMemoryScopes = (): Promise<Array<{ id: string; name: string }>> => request('/api/memory/cards/scopes');
export const patchMemoryCard = (id: string, patch: Partial<MemoryCard> & { version: number }): Promise<MemoryCard> => request(`/api/memory/cards/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify(patch) });
export const deleteMemoryCard = (id: string, version: number): Promise<void> => request(`/api/memory/cards/${encodeURIComponent(id)}?version=${version}`, { method: 'DELETE' });
export const releaseMemoryCard = (id: string, version: number): Promise<MemoryCard> => request(`/api/memory/cards/${encodeURIComponent(id)}/release`, { method: 'POST', body: JSON.stringify({ version }) });

const EVENT = 'therese:memory-cards-changed';
export function notifyMemoryChange(): void {
  window.dispatchEvent(new Event(EVENT));
  if (typeof window.BroadcastChannel !== 'undefined') {
    const canal = new BroadcastChannel(EVENT); canal.postMessage('changed'); canal.close();
  }
}
export function listenMemoryChanges(callback: () => void): () => void {
  window.addEventListener(EVENT, callback);
  const canal = typeof window.BroadcastChannel !== 'undefined' ? new BroadcastChannel(EVENT) : null;
  if (canal) canal.onmessage = callback;
  return () => { window.removeEventListener(EVENT, callback); canal?.close(); };
}
