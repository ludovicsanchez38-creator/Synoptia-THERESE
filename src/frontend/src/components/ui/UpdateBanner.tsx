import { useEffect, useState, useCallback } from 'react';
import { Download, RefreshCw, X } from 'lucide-react';

/** Intervalle entre les checks auto (6 heures en ms) */
const CHECK_INTERVAL_MS = 6 * 60 * 60 * 1000;

/** Delai au demarrage avant le premier check (5 secondes) */
const STARTUP_DELAY_MS = 5_000;

type UpdateState =
  | { phase: 'idle' }
  | { phase: 'available'; version: string; body: string }
  | { phase: 'downloading'; version: string; progress: number }
  | { phase: 'ready'; version: string }
  | { phase: 'error'; message: string };

/**
 * Bandeau discret en haut de l'app pour les mises a jour automatiques.
 * Utilise le plugin Tauri updater (@tauri-apps/plugin-updater).
 *
 * Comportement :
 * - Check silencieux au lancement (apres 5s) puis toutes les 6h
 * - Pas de popup bloquante (dialog: false dans tauri.conf.json)
 * - Telechargement en arriere-plan au clic
 * - Redemarrage a la demande de l'utilisateur
 */
export function UpdateBanner() {
  const [state, setState] = useState<UpdateState>({ phase: 'idle' });
  const [dismissed, setDismissed] = useState(false);

  const checkForUpdate = useCallback(async () => {
    // Ne pas checker si on n'est pas dans Tauri
    if (!('__TAURI__' in window)) return;

    try {
      const { check } = await import('@tauri-apps/plugin-updater');
      const update = await check();

      if (update?.available) {
        setState({
          phase: 'available',
          version: update.version,
          body: update.body ?? '',
        });
        setDismissed(false);
      }
    } catch (err) {
      // Silencieux - pas d'erreur affichee pour un check auto
      console.warn('[UpdateBanner] Check echoue:', err);
    }
  }, []);

  // Check au montage (apres delai) + intervalle periodique
  useEffect(() => {
    const startupTimer = setTimeout(checkForUpdate, STARTUP_DELAY_MS);

    const intervalId = setInterval(checkForUpdate, CHECK_INTERVAL_MS);

    return () => {
      clearTimeout(startupTimer);
      clearInterval(intervalId);
    };
  }, [checkForUpdate]);

  const handleDownloadAndInstall = useCallback(async () => {
    if (!('__TAURI__' in window)) return;

    try {
      const { check } = await import('@tauri-apps/plugin-updater');
      const update = await check();

      if (!update?.available) return;

      const version = update.version;
      setState({ phase: 'downloading', version, progress: 0 });

      let contentLength = 0;
      let downloaded = 0;

      await update.downloadAndInstall((event) => {
        if (event.event === 'Started' && event.data.contentLength) {
          contentLength = event.data.contentLength;
        } else if (event.event === 'Progress') {
          downloaded += event.data.chunkLength;
          const progress = contentLength > 0
            ? Math.round((downloaded / contentLength) * 100)
            : 0;
          setState({ phase: 'downloading', version, progress });
        } else if (event.event === 'Finished') {
          setState({ phase: 'ready', version });
        }
      });

      // Si on arrive ici sans event Finished (fallback)
      setState((prev) =>
        prev.phase === 'downloading' ? { phase: 'ready', version } : prev
      );
    } catch (err) {
      console.error('[UpdateBanner] Erreur installation:', err);
      setState({
        phase: 'error',
        message: err instanceof Error ? err.message : 'Erreur inconnue',
      });
    }
  }, []);

  const handleRestart = useCallback(async () => {
    try {
      const { relaunch } = await import('@tauri-apps/plugin-process');
      await relaunch();
    } catch {
      // Fallback : demander un redemarrage manuel
      setState({
        phase: 'error',
        message: 'Veuillez redemarrer THERESE manuellement pour appliquer la mise a jour.',
      });
    }
  }, []);

  // Rien a afficher
  if (state.phase === 'idle' || dismissed) {
    return null;
  }

  return (
    <div
      role="status"
      aria-live="polite"
      className="relative flex items-center justify-center gap-3 px-4 py-2 text-sm"
      style={{
        background: state.phase === 'error'
          ? 'rgba(225, 29, 141, 0.15)'
          : 'rgba(34, 211, 238, 0.1)',
        borderBottom: '1px solid',
        borderColor: state.phase === 'error'
          ? 'rgba(225, 29, 141, 0.3)'
          : 'rgba(34, 211, 238, 0.2)',
      }}
    >
      {/* Contenu selon la phase */}
      {state.phase === 'available' && (
        <>
          <Download size={16} className="text-accent-cyan shrink-0" />
          <span className="text-text">
            Nouvelle version <strong className="text-accent-cyan">{state.version}</strong> disponible
          </span>
          <button
            onClick={handleDownloadAndInstall}
            className="ml-2 px-3 py-1 rounded-md text-xs font-medium transition-colors"
            style={{
              background: 'rgba(34, 211, 238, 0.2)',
              color: '#22D3EE',
              border: '1px solid rgba(34, 211, 238, 0.3)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(34, 211, 238, 0.3)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(34, 211, 238, 0.2)';
            }}
          >
            Installer maintenant
          </button>
        </>
      )}

      {state.phase === 'downloading' && (
        <>
          <RefreshCw size={16} className="text-accent-cyan shrink-0 animate-spin" />
          <span className="text-text">
            Telechargement de la v{state.version}...
            {state.progress > 0 && (
              <span className="text-text-muted ml-1">({state.progress}%)</span>
            )}
          </span>
        </>
      )}

      {state.phase === 'ready' && (
        <>
          <RefreshCw size={16} className="text-accent-cyan shrink-0" />
          <span className="text-text">
            Mise a jour <strong className="text-accent-cyan">v{state.version}</strong> prete
          </span>
          <button
            onClick={handleRestart}
            className="ml-2 px-3 py-1 rounded-md text-xs font-medium transition-colors"
            style={{
              background: 'rgba(34, 211, 238, 0.2)',
              color: '#22D3EE',
              border: '1px solid rgba(34, 211, 238, 0.3)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(34, 211, 238, 0.3)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'rgba(34, 211, 238, 0.2)';
            }}
          >
            Redemarrer pour installer
          </button>
        </>
      )}

      {state.phase === 'error' && (
        <>
          <span className="text-accent-magenta">{state.message}</span>
        </>
      )}

      {/* Bouton fermer (sauf pendant le telechargement) */}
      {state.phase !== 'downloading' && (
        <button
          onClick={() => setDismissed(true)}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded text-text-muted hover:text-text transition-colors"
          aria-label="Fermer le bandeau de mise a jour"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}
