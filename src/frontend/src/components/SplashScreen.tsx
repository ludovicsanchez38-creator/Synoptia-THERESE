import { useEffect, useState, useCallback, useRef } from 'react';
import { initApiBase, getApiBase } from '../services/api/core';

interface SplashScreenProps {
  onReady: () => void;
}

const POLL_INTERVAL = 500;
const TIMEOUT_MS = 60_000;

const MESSAGES = [
  'Démarrage du moteur...',
  'Chargement des modèles...',
  'Préparation de la mémoire...',
  'Initialisation des services...',
  'Presque prêt...',
];

export function SplashScreen({ onReady }: SplashScreenProps) {
  const [message, setMessage] = useState(MESSAGES[0]);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const apiBaseReady = useRef(false);

  const checkHealth = useCallback(async (): Promise<boolean> => {
    try {
      const healthUrl = `${getApiBase()}/health`;
      const res = await fetch(healthUrl, { signal: AbortSignal.timeout(2000) });
      if (res.ok) {
        const data = await res.json();
        return data.status === 'healthy';
      }
      return false;
    } catch {
      return false;
    }
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

        // Progression et messages
        const pct = Math.min(95, (elapsed / TIMEOUT_MS) * 100);
        setProgress(pct);
        const msgIndex = Math.min(
          MESSAGES.length - 1,
          Math.floor((elapsed / TIMEOUT_MS) * MESSAGES.length)
        );
        setMessage(MESSAGES[msgIndex]);

        // Check
        const healthy = await checkHealth();
        if (healthy && !cancelled) {
          setProgress(100);
          setMessage('Prêt !');
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
          <h1 className="text-4xl font-bold bg-gradient-to-r from-accent-cyan to-accent-magenta bg-clip-text text-transparent mb-6">
            THÉRÈSE
          </h1>
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
          className="text-5xl font-bold bg-gradient-to-r from-accent-cyan to-accent-magenta bg-clip-text text-transparent mb-8"
          style={{
            animation: 'pulse 2s ease-in-out infinite',
          }}
        >
          THÉRÈSE
        </h1>

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
