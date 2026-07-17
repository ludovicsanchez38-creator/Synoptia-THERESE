/**
 * THÉRÈSE v2 - API Core Module
 *
 * Base types, helpers, and authentication for API communication.
 * Sprint 2 - PERF-2.2: Extracted from monolithic api.ts
 */

/**
 * Port par défaut du backend. Surchargable au build/dev par
 * VITE_THERESE_BACKEND_PORT : les E2E isolés (revue 0.40) pointent ainsi le
 * frontend vers leur backend jetable au lieu de l'instance réelle (17293).
 */
const DEFAULT_BACKEND_PORT = Number(import.meta.env.VITE_THERESE_BACKEND_PORT ?? 17293);
export let API_BASE = `http://127.0.0.1:${DEFAULT_BACKEND_PORT}`;

/**
 * Singleton : une seule promesse d'init partagée entre toutes les fenêtres/appels.
 * Évite la race condition quand SplashScreen et PanelWindow appellent initApiBase()
 * en parallèle (chaque fenêtre Tauri a son propre contexte JS).
 */
let _initPromise: Promise<void> | null = null;

/**
 * Initialise API_BASE avec le port du sidecar.
 *
 * Ordre de résolution :
 * 1. Paramètre URL ?port=XXXX (passé par la fenêtre principale aux panels)
 * 2. Tauri IPC get_backend_port (retry 10x 300ms pour Mac M1 lent)
 * 3. Fallback port 17293 (mode dev)
 */
export function initApiBase(): Promise<void> {
  if (_initPromise) return _initPromise;
  _initPromise = (async () => {
    // 1. Vérifier le paramètre URL (panels ouverts depuis la fenêtre principale)
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const portParam = urlParams.get('port');
      if (portParam && /^\d+$/.test(portParam)) {
        const port = parseInt(portParam, 10);
        if (port > 0 && port <= 65535) {
          API_BASE = `http://127.0.0.1:${port}`;
          console.log(`[API] Port backend via URL : ${port}`);
          return;
        }
      }
    } catch {
      // window.location peut ne pas être disponible dans certains contextes
    }

    // 2. Tauri IPC avec retry (fenêtre principale / SplashScreen)
    const MAX_RETRIES = 10;
    const RETRY_DELAY = 300;

    for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
      try {
        const { invoke } = await import('@tauri-apps/api/core');
        const port: number = await invoke('get_backend_port');
        if (port && port > 0 && port <= 65535) {
          API_BASE = `http://127.0.0.1:${port}`;
          console.log(`[API] Port backend : ${port} (tentative ${attempt + 1})`);
          return;
        }
        console.log(`[API] Port invalide reçu, retry ${attempt + 1}/${MAX_RETRIES}...`);
      } catch {
        console.log(`[API] IPC échoué, retry ${attempt + 1}/${MAX_RETRIES}...`);
      }
      await new Promise((r) => setTimeout(r, RETRY_DELAY));
    }

    // 3. Dernier essai ou fallback
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const port: number = await invoke('get_backend_port');
      if (port && port > 0 && port <= 65535) {
        API_BASE = `http://127.0.0.1:${port}`;
        console.log(`[API] Port backend final : ${port}`);
        return;
      }
    } catch {
      // Fallback : port 17293 déjà défini dans API_BASE
    }
    console.log(`[API] Fallback port ${DEFAULT_BACKEND_PORT} (mode dev)`);
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
    // Borné : un backend muet au démarrage ne doit pas bloquer l'app (F7).
    const response = await apiFetch(`${API_BASE}/api/auth/token`, { timeoutMs: 10_000 });
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

/**
 * Délai maximal commun des appels API (revue 0.40) : une requête bloquée ne
 * doit plus figer un écran sans limite. Le délai couvre l'attente de la
 * RÉPONSE (en-têtes) : une fois la réponse arrivée, le corps (téléchargement,
 * flux SSE) n'est plus soumis au délai.
 */
export const API_TIMEOUT_MS = 30_000;

export type ApiFetchOptions = RequestInit & {
  /**
   * Délai maximal en millisecondes, `null` pour désactiver. À désactiver sur
   * les flux SSE (le premier octet peut attendre un modèle local froid), les
   * appels LLM non-stream et les transferts de fichiers longs.
   */
  timeoutMs?: number | null;
};

export function apiFetch(url: string, options: ApiFetchOptions = {}): Promise<Response> {
  const { timeoutMs = API_TIMEOUT_MS, ...init } = options;
  const headers = new Headers(init.headers);
  if (_sessionToken) {
    headers.set('X-Therese-Token', _sessionToken);
  }
  if (timeoutMs == null) {
    return fetch(url, { ...init, headers });
  }

  const controller = new AbortController();
  const timer = setTimeout(
    () => controller.abort(new DOMException(`Délai de ${timeoutMs} ms dépassé`, 'TimeoutError')),
    timeoutMs,
  );
  const callerSignal = init.signal;
  if (callerSignal) {
    if (callerSignal.aborted) {
      controller.abort(callerSignal.reason);
    } else {
      callerSignal.addEventListener('abort', () => controller.abort(callerSignal.reason), {
        once: true,
      });
    }
  }
  return fetch(url, { ...init, headers, signal: controller.signal }).finally(() =>
    clearTimeout(timer),
  );
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
  options: ApiFetchOptions = {}
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
