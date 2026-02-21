import { useEffect, useState, useCallback, useRef } from 'react';
import { initApiBase, getApiBase } from '../services/api/core';

type UnlistenFn = () => void;

interface SplashScreenProps {
  onReady: () => void;
}

/**
 * F-09 : Met à jour la barre de progression dans le dock macOS.
 * Utilise setProgressBar (Tauri v2) activé via macOSPrivateApi.
 * No-op silencieux sur Windows et en mode dev.
 */
async function setDockProgress(progress: number): Promise<void> {
  try {
    const { getCurrentWindow, ProgressBarStatus } = await import('@tauri-apps/api/window');
    const win = getCurrentWindow();
    if (progress >= 100) {
      await win.setProgressBar({ status: ProgressBarStatus.None });
    } else {
      await win.setProgressBar({
        status: ProgressBarStatus.Normal,
        progress: Math.round(progress),
      });
    }
  } catch {
    // Pas en contexte Tauri ou macOSPrivateApi non activé : on ignore silencieusement
  }
}

const POLL_INTERVAL = 2_000; // 2s entre chaque health check (réduit la charge réseau)
const TIMEOUT_MS = 600_000; // 10 min : premier lancement Windows avec Defender peut prendre 3+ min

const MESSAGES = [
  { after: 0, text: 'Démarrage du moteur...' },
  { after: 5_000, text: 'Chargement des modèles...' },
  { after: 15_000, text: 'Préparation de la mémoire...' },
  { after: 30_000, text: 'Initialisation des services...' },
  { after: 60_000, text: 'Premier lancement, ça peut prendre un moment...' },
  { after: 120_000, text: 'Encore un peu de patience...' },
  { after: 180_000, text: 'Chargement en cours, Windows analyse les fichiers...' },
  { after: 300_000, text: 'Presque prêt...' },
];

/**
 * Crée un AbortSignal qui expire après `ms` millisecondes.
 * Polyfill pour Safari <17.4 où AbortSignal.timeout() n'existe pas.
 */
function createTimeoutSignal(ms: number): AbortSignal {
  if (typeof AbortSignal.timeout === 'function') {
    return AbortSignal.timeout(ms);
  }
  const controller = new AbortController();
  setTimeout(() => controller.abort(), ms);
  return controller.signal;
}

/** Teste si un backend THÉRÈSE répond sur une URL donnée */
async function probeHealth(baseUrl: string): Promise<boolean> {
  const url = `${baseUrl}/health`;
  try {
    console.log(`[probeHealth] GET ${url}`);
    const res = await fetch(url, { signal: createTimeoutSignal(5000) });
    console.log(`[probeHealth] status=${res.status} ok=${res.ok}`);
    if (!res.ok) return false;
    const text = await res.text();
    console.log(`[probeHealth] body=${text.slice(0, 200)}`);
    const data = JSON.parse(text);
    // Vérifier status + version pour s'assurer que c'est bien THÉRÈSE
    // Accepter "degraded" : le backend tourne mais un service non-critique
    // n'est pas prêt (ex: embeddings en cours de chargement sur Windows)
    const valid = (data.status === 'healthy' || data.status === 'degraded')
      && typeof data.version === 'string';
    console.log(`[probeHealth] status=${data.status} version=${data.version} valid=${valid}`);
    return valid;
  } catch (err) {
    console.error(`[probeHealth] ERREUR sur ${url}:`, String(err));
    return false;
  }
}

export function SplashScreen({ onReady }: SplashScreenProps) {
  const [message, setMessage] = useState(MESSAGES[0].text);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [appVersion, setAppVersion] = useState<string | null>(null);
  const apiBaseReady = useRef(false);

  // Charger la version de l'app (tauri.conf.json)
  useEffect(() => {
    import('@tauri-apps/api/app')
      .then(({ getVersion }) => getVersion())
      .then(setAppVersion)
      .catch(() => {});
  }, []);

  const checkHealth = useCallback(async (): Promise<boolean> => {
    return probeHealth(getApiBase());
  }, []);

  // Écouter les erreurs sidecar émises par le Rust
  useEffect(() => {
    let unlisten: UnlistenFn | null = null;

    import('@tauri-apps/api/event')
      .then(({ listen }) => {
        listen<string>('sidecar-error', (event) => {
          setError(
            `Le moteur n'a pas pu démarrer :\n${event.payload}\n\nDans le Terminal :\nxattr -cr /Applications/THÉRÈSE.app\npuis relancez l'app.`
          );
        }).then((fn) => {
          unlisten = fn;
        });
      })
      .catch(() => {
        // Pas en contexte Tauri (mode dev)
      });

    return () => {
      if (unlisten) unlisten();
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    const startTime = Date.now();

    async function poll() {
      // Résoudre le port backend avant de commencer le polling
      if (!apiBaseReady.current) {
        await initApiBase();
        apiBaseReady.current = true;
      }

      while (!cancelled) {
        const elapsed = Date.now() - startTime;

        // Timeout
        if (elapsed > TIMEOUT_MS) {
          setError(
            'Le backend ne répond pas. Relancez THÉRÈSE.'
          );
          return;
        }

        // NOTE (BUG-008) : Le fallback port 8000 a été supprimé.
        // En production, le port est toujours dynamique (IPC Tauri).
        // Le fallback pouvait connecter le frontend à un backend zombie
        // d'une session précédente, causant des erreurs d'auth silencieuses.
        // En dev, API_BASE est déjà 8000 par défaut (initApiBase fallback).

        // Progression (logarithmique pour rester informatif sans stresser)
        // Monte vite au début, ralentit ensuite
        const pct = Math.min(95, Math.log1p(elapsed / 1000) / Math.log1p(TIMEOUT_MS / 1000) * 100);
        setProgress(pct);

        // F-09 : mise à jour de la barre de progression dans le dock macOS
        void setDockProgress(pct);

        // Message adapté au temps écoulé
        let currentMsg = MESSAGES[0].text;
        for (const m of MESSAGES) {
          if (elapsed >= m.after) currentMsg = m.text;
        }
        setMessage(currentMsg);

        // Check
        const healthy = await checkHealth();
        if (healthy && !cancelled) {
          setProgress(100);
          setMessage('Prêt !');
          // F-09 : effacer la progression du dock macOS
          void setDockProgress(100);
          // Petit délai pour l'animation
          await new Promise((r) => setTimeout(r, 300));
          if (!cancelled) onReady();
          return;
        }

        // Attendre avant le prochain poll
        await new Promise((r) => setTimeout(r, POLL_INTERVAL));
      }
    }

    poll();
    return () => { cancelled = true; };
  }, [checkHealth, onReady]);

  if (error) {
    return (
      <div className="h-screen w-screen bg-bg flex items-center justify-center" data-tauri-drag-region>
        <div className="text-center max-w-md px-6">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-accent-cyan to-accent-magenta bg-clip-text text-transparent mb-2">
            THÉRÈSE
          </h1>
          {appVersion && (
            <p className="text-text-muted text-xs mb-4">v{appVersion}-alpha</p>
          )}
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen bg-bg flex items-center justify-center" data-tauri-drag-region>
      <div className="text-center">
        {/* Logo animé */}
        <h1
          className="text-5xl font-bold bg-gradient-to-r from-accent-cyan to-accent-magenta bg-clip-text text-transparent mb-2"
          style={{
            animation: 'pulse 2s ease-in-out infinite',
          }}
        >
          THÉRÈSE
        </h1>
        {appVersion && (
          <p className="text-text-muted text-xs mb-6">v{appVersion}-alpha</p>
        )}

        {/*
          F-09 : Spinner de chargement macOS-style
          Affiché pendant tout le démarrage, avant et après que le backend soit prêt.
          Remplace l'absence de retour visuel sur macOS entre le clic sur l'icône
          et l'apparition de la fenêtre pleinement opérationnelle.
        */}
        <div
          className="mx-auto mb-5"
          style={{
            width: '28px',
            height: '28px',
            border: '2.5px solid rgba(255,255,255,0.12)',
            borderTopColor: 'var(--color-accent-cyan, #00d4ff)',
            borderRightColor: 'var(--color-accent-magenta, #ff00aa)',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
          }}
          role="status"
          aria-label="Chargement en cours"
        />

        {/* Barre de progression */}
        <div className="w-64 mx-auto mb-4">
          <div className="h-1 bg-white/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-accent-cyan to-accent-magenta rounded-full transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Message */}
        <p className="text-text-muted text-sm">{message}</p>
      </div>
    </div>
  );
}
