/**
 * THÉRÈSE v2 - API Core Module
 *
 * Base types, helpers, and authentication for API communication.
 * Sprint 2 - PERF-2.2: Extracted from monolithic api.ts
 */

export const API_BASE = 'http://127.0.0.1:8000';

// Auth token de session (SEC-010)
let _sessionToken: string | null = null;

export async function initializeAuth(): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/api/auth/token`);
    if (response.ok) {
      const data = await response.json();
      _sessionToken = data.token;
      console.log('Auth token loaded');
    }
  } catch (e) {
    console.warn('Could not load auth token:', e);
  }
}

export function getSessionToken(): string | null {
  return _sessionToken;
}

export function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers);
  if (_sessionToken) {
    headers.set('X-Therese-Token', _sessionToken);
  }
  return fetch(url, { ...options, headers });
}

// API Error
export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    message?: string
  ) {
    super(message || `${status} ${statusText}`);
    this.name = 'ApiError';
  }
}

// HTTP helpers
export async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  let response: Response;
  try {
    response = await apiFetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
  } catch (_e: any) {
    // Erreur réseau (Load failed / Failed to fetch)
    throw new ApiError(0, 'NetworkError', 'Impossible de contacter le serveur');
  }

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    const message = data?.detail || data?.message || `Erreur ${response.status}`;
    throw new ApiError(response.status, response.statusText, message);
  }

  return response.json();
}

// Health & Status
export interface HealthStatus {
  status: string;
  version: string;
}

export interface Stats {
  entities: {
    contacts: number;
    projects: number;
    conversations: number;
    messages: number;
    files: number;
  };
  uptime_seconds: number;
  data_dir: string;
  db_path: string;
}

export async function checkHealth(): Promise<HealthStatus> {
  return request<HealthStatus>('/health');
}

export async function getStats(): Promise<Stats> {
  return request<Stats>('/api/config/stats');
}
