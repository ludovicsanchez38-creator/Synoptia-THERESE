import { request } from './core';
export interface MemoryDraft { id: string; kind: 'devis' | 'facture' | 'avoir' | 'document' | 'email'; title: string; status: string; account_id?: string | null; updated_at?: string }
export interface LocalEmailDraft { id: string; account_id: string; subject: string; to_emails: string[]; cc_emails: string[]; bcc_emails: string[]; body_plain: string | null; body_html: string | null }
export const listMemoryDrafts = (offset = 0): Promise<{ items: MemoryDraft[]; total: number }> => request(`/api/memory/drafts?offset=${offset}&limit=50`);
export const getLocalEmailDraft = (id: string): Promise<LocalEmailDraft> => request(`/api/memory/drafts/email/${encodeURIComponent(id)}`);
