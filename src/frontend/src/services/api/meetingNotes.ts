import { request } from './core';
export interface MeetingChoice { id: string; calendar_id: string; summary: string; date: string | null }
export const listMeetingEvents = (query = '', skip = 0): Promise<MeetingChoice[]> => request(`/api/crm/meeting-events?query=${encodeURIComponent(query)}&skip=${skip}&limit=50`);
export const createMeetingNote = (data: { calendar_event_id: string; calendar_id: string; contact_id: string | null; description: string }): Promise<{ id: string }> => request('/api/crm/meeting-notes', { method: 'POST', body: JSON.stringify(data) });
