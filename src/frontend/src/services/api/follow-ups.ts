import { request } from './core';

export type FollowUpStatus = 'pending' | 'done' | 'cancelled';

export interface EmailFollowUp {
  id: string;
  email_message_id: string;
  contact_id: string | null;
  due_date: string;
  note: string | null;
  status: FollowUpStatus;
  created_at: string;
  email_subject: string | null;
  email_from: string | null;
  contact_name: string | null;
}

export interface CreateFollowUpRequest {
  email_message_id: string;
  contact_id?: string;
  due_date: string;
  note?: string;
}

export interface UpdateFollowUpRequest {
  due_date?: string;
  note?: string;
  status?: FollowUpStatus;
  contact_id?: string;
}

export function listFollowUps(status?: FollowUpStatus): Promise<EmailFollowUp[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : '';
  return request(`/api/follow-ups${query}`);
}

export function createFollowUp(payload: CreateFollowUpRequest): Promise<EmailFollowUp> {
  return request('/api/follow-ups', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function updateFollowUp(
  id: string,
  payload: UpdateFollowUpRequest,
): Promise<EmailFollowUp> {
  return request(`/api/follow-ups/${encodeURIComponent(id)}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function deleteFollowUp(id: string): Promise<{ deleted: boolean; id: string }> {
  return request(`/api/follow-ups/${encodeURIComponent(id)}`, { method: 'DELETE' });
}
