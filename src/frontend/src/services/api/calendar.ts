/**
 * THÉRÈSE v2 - Calendar API Module
 *
 * Gestion Google Calendar - calendriers, événements et synchronisation.
 */

import { API_BASE, apiFetch } from './core';

export interface Calendar {
  id: string;
  account_id: string | null;
  summary: string;
  description: string | null;
  timezone: string;
  primary: boolean;
  provider: 'local' | 'google' | 'caldav' | string;
  synced_at: string | null;
}

export interface CalendarEvent {
  id: string;
  calendar_id: string;
  summary: string;
  description: string | null;
  location: string | null;
  start_datetime: string | null;
  end_datetime: string | null;
  start_date: string | null;
  end_date: string | null;
  all_day: boolean;
  attendees: string[] | null;
  recurrence: string[] | null;
  status: string;
  synced_at: string;
}

export interface CreateEventRequest {
  calendar_id?: string;
  summary: string;
  description?: string;
  location?: string;
  start_datetime?: string;
  end_datetime?: string;
  start_date?: string;
  end_date?: string;
  attendees?: string[];
  recurrence?: string[];
  /** Fuseau IANA du poste (ex: "America/Toronto") pour les événements horodatés. */
  timezone?: string;
}

export interface UpdateEventRequest {
  summary?: string;
  description?: string;
  location?: string;
  start_datetime?: string;
  end_datetime?: string;
  start_date?: string;
  end_date?: string;
  attendees?: string[];
  recurrence?: string[];
  timezone?: string;
}

export interface CalendarSyncResponse {
  calendars_synced: number;
  events_synced: number;
  synced_at: string;
}

// Calendars
export async function listCalendars(
  accountId?: string,
  options?: { createDefault?: boolean },
): Promise<Calendar[]> {
  const params = new URLSearchParams();
  if (accountId) params.set('account_id', accountId);
  if (options?.createDefault === false) params.set('create_default', 'false');
  const query = params.size > 0 ? `?${params}` : '';
  const response = await apiFetch(`${API_BASE}/api/calendar/calendars${query}`);
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || data.message || `Erreur ${response.status}`);
  }
  return response.json();
}

export async function getCalendar(calendarId: string, accountId: string): Promise<Calendar> {
  const response = await apiFetch(`${API_BASE}/api/calendar/calendars/${calendarId}?account_id=${accountId}`);
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function createCalendar(
  accountId: string,
  summary: string,
  description?: string,
  timezone: string = 'Europe/Paris'
): Promise<Calendar> {
  const response = await apiFetch(`${API_BASE}/api/calendar/calendars`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ account_id: accountId, summary, description, timezone }),
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function deleteCalendar(calendarId: string, accountId: string): Promise<any> {
  const response = await apiFetch(`${API_BASE}/api/calendar/calendars/${calendarId}?account_id=${accountId}`, {
    method: 'DELETE',
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

// Events
export async function listEvents(
  accountId: string | undefined,
  calendarId: string = 'primary',
  params?: {
    time_min?: string;
    time_max?: string;
    max_results?: number;
  }
): Promise<CalendarEvent[]> {
  const queryParams = new URLSearchParams({ calendar_id: calendarId });
  if (accountId) queryParams.set('account_id', accountId);
  if (params?.time_min) queryParams.set('time_min', params.time_min);
  if (params?.time_max) queryParams.set('time_max', params.time_max);
  if (params?.max_results) queryParams.set('max_results', params.max_results.toString());

  const response = await apiFetch(`${API_BASE}/api/calendar/events?${queryParams}`);
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || data.message || `Erreur ${response.status}`);
  }
  return response.json();
}

export async function getEvent(eventId: string, calendarId: string, accountId: string): Promise<CalendarEvent> {
  const response = await apiFetch(`${API_BASE}/api/calendar/events/${eventId}?calendar_id=${calendarId}&account_id=${accountId}`);
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function createEvent(req: CreateEventRequest, accountId?: string): Promise<CalendarEvent> {
  const params = new URLSearchParams();
  if (accountId) params.set('account_id', accountId);
  const query = params.size > 0 ? `?${params}` : '';
  const response = await apiFetch(`${API_BASE}/api/calendar/events${query}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function updateEvent(
  eventId: string,
  req: UpdateEventRequest,
  calendarId: string,
  accountId?: string
): Promise<CalendarEvent> {
  const params = new URLSearchParams({ calendar_id: calendarId });
  if (accountId) params.set('account_id', accountId);
  const response = await apiFetch(`${API_BASE}/api/calendar/events/${eventId}?${params}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function deleteEvent(eventId: string, calendarId: string, accountId?: string): Promise<any> {
  const params = new URLSearchParams({ calendar_id: calendarId });
  if (accountId) params.set('account_id', accountId);
  const response = await apiFetch(`${API_BASE}/api/calendar/events/${eventId}?${params}`, {
    method: 'DELETE',
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function quickAddEvent(text: string, calendarId: string, accountId: string): Promise<CalendarEvent> {
  const response = await apiFetch(`${API_BASE}/api/calendar/events/quick-add?account_id=${accountId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ calendar_id: calendarId, text }),
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

// Sync
export async function syncCalendar(accountId?: string): Promise<CalendarSyncResponse> {
  const params = new URLSearchParams();
  if (accountId) params.set('account_id', accountId);
  const query = params.size > 0 ? `?${params}` : '';
  const response = await apiFetch(`${API_BASE}/api/calendar/sync${query}`, {
    method: 'POST',
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || data.message || `Erreur ${response.status}`);
  }
  return response.json();
}

export async function getCalendarSyncStatus(accountId: string): Promise<any> {
  const response = await apiFetch(`${API_BASE}/api/calendar/sync/status?account_id=${accountId}`);
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function importICSFile(file: File, calendarId?: string): Promise<{ imported: number; skipped: number; message: string }> {
  const formData = new FormData();
  formData.append('file', file);
  const params = calendarId ? `?calendar_id=${calendarId}` : '';
  const response = await apiFetch(`${API_BASE}/api/calendar/import-ics${params}`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

// Export ICS
export async function exportICSFile(calendarId?: string): Promise<Blob> {
  const params = calendarId ? `?calendar_id=${calendarId}` : '';
  const response = await apiFetch(`${API_BASE}/api/calendar/export-ics${params}`);
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    throw new Error(d.detail || d.message || `Erreur ${response.status}`);
  }
  return response.blob();
}
