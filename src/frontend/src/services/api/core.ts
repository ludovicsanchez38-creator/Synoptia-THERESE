/**
 * THÉRÈSE v2 - API Core Module
 *
 * Base types, helpers, and authentication for API communication.
 * Sprint 2 - PERF-2.2: Extracted from monolithic api.ts
 */

/** URL de base du backend (port dynamique en release, 8000 en dev) */
export let API_BASE = 'http://127.0.0.1:8000';

/**
 * Singleton : une seule promesse d'init partagée entre toutes les fenêtres/appels.
 * Évite la race condition quand SplashScreen et PanelWindow appellent initApiBase()
 * en parallèle (chaque fenêtre Tauri a son propre contexte JS).
 */
let _initPromise: Promise<void> | null = null;

/**
 * Initialise API_BASE avec le port dynamique du sidecar (via Tauri IPC).
 *
 * Retry jusqu'à 10 fois avec 300ms de délai si l'IPC échoue ou retourne
 * le port par défaut (8000). Sur certains Mac (M1), le bridge IPC Tauri
 * n'est pas prêt immédiatement au chargement du WebView.
 */
export function initApiBase(): Promise<void> {
  if (_initPromise) return _initPromise;
  _initPromise = (async () => {
    const MAX_RETRIES = 10;
    const RETRY_DELAY = 300;

    for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
      try {
        const { invoke } = await import('@tauri-apps/api/core');
        const port: number = await invoke('get_backend_port');
        if (port && port !== 8000) {
          API_BASE = `http://127.0.0.1:${port}`;
          console.log(`[API] Port backend : ${port} (tentative ${attempt + 1})`);
          return;
        }
        // Port 8000 = valeur initiale, le setup Rust n'a peut-être pas encore mis à jour
        console.log(`[API] Port 8000 reçu, retry ${attempt + 1}/${MAX_RETRIES}...`);
      } catch {
        console.log(`[API] IPC échoué, retry ${attempt + 1}/${MAX_RETRIES}...`);
      }
      await new Promise((r) => setTimeout(r, RETRY_DELAY));
    }

    // Dernier essai ou fallback
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const port: number = await invoke('get_backend_port');
      API_BASE = `http://127.0.0.1:${port}`;
      console.log(`[API] Port backend final : ${port}`);
    } catch {
      console.log('[API] Fallback port 8000 (mode dev)');
    }
  })();
  return _initPromise;
}

/** Retourne l'URL de base courante */
export function getApiBase(): string {
  return API_BASE;
}

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
