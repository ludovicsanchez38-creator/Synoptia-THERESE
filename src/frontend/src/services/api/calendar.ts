/**
 * THÉRÈSE v2 - Calendar API Module
 *
 * Gestion Google Calendar - calendriers, événements et synchronisation.
 */

import { API_BASE, apiFetch } from './core';

export interface Calendar {
  id: string;
  account_id: string;
  summary: string;
  description: string | null;
  timezone: string;
  primary: boolean;
  synced_at: string;
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
}

export interface CalendarSyncResponse {
  calendars_synced: number;
  events_synced: number;
  synced_at: string;
}

// Calendars
export async function listCalendars(accountId: string): Promise<Calendar[]> {
  const response = await apiFetch(`${API_BASE}/api/calendar/calendars?account_id=${accountId}`);
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
  accountId: string,
  calendarId: string = 'primary',
  params?: {
    time_min?: string;
    time_max?: string;
    max_results?: number;
  }
): Promise<CalendarEvent[]> {
  const queryParams = new URLSearchParams({
    account_id: accountId,
    calendar_id: calendarId,
    ...(params?.time_min && { time_min: params.time_min }),
    ...(params?.time_max && { time_max: params.time_max }),
    ...(params?.max_results && { max_results: params.max_results.toString() }),
  });

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

export async function createEvent(req: CreateEventRequest, accountId: string): Promise<CalendarEvent> {
  const response = await apiFetch(`${API_BASE}/api/calendar/events?account_id=${accountId}`, {
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
  accountId: string
): Promise<CalendarEvent> {
  const response = await apiFetch(`${API_BASE}/api/calendar/events/${eventId}?calendar_id=${calendarId}&account_id=${accountId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function deleteEvent(eventId: string, calendarId: string, accountId: string): Promise<any> {
  const response = await apiFetch(`${API_BASE}/api/calendar/events/${eventId}?calendar_id=${calendarId}&account_id=${accountId}`, {
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
export async function syncCalendar(accountId: string): Promise<CalendarSyncResponse> {
  const response = await apiFetch(`${API_BASE}/api/calendar/sync?account_id=${accountId}`, {
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
