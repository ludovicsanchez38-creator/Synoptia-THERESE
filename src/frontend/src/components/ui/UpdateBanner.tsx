import { useEffect, useState, useCallback } from 'react';
import { Download, RefreshCw, X } from 'lucide-react';
import { API_BASE } from '../../services/api/core';
import { sanitizeErrorMessage } from '../../lib/sanitizeError';

/** Intervalle entre les checks auto (6 heures en ms) */
const CHECK_INTERVAL_MS = 6 * 60 * 60 * 1000;

/** Delai au demarrage avant le premier check (5 secondes) */
const STARTUP_DELAY_MS = 5_000;

type UpdateState =
  | { phase: 'idle' }
  | { phase: 'available'; version: string; body: string }
  | { phase: 'downloading'; version: string; progress: number }
  | { phase: 'ready'; version: string }
  | { phase: 'restart-required'; version: string }
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

      // BUG-099 : Arrêter le backend sidecar AVANT l'installation
      // pour éviter le verrou backend.exe sur Windows
      try {
        // Revue 0.40.1 (F8) : marquer l'arrêt comme volontaire côté Rust,
        // sinon le watcher relance le backend pendant l'installation.
        try {
          const { invoke } = await import('@tauri-apps/api/core');
          await invoke('prepare_backend_shutdown');
        } catch {
          // Hors Tauri (dev navigateur) : rien à préparer.
        }
        await fetch(`${API_BASE}/api/shutdown`, { method: 'POST' });
        // Health check poll : attendre que le backend soit vraiment mort
        const MAX_WAIT = 10_000;
        const POLL_INTERVAL = 500;
        let waited = 0;
        while (waited < MAX_WAIT) {
          try {
            await fetch(`${API_BASE}/health`);
            // Backend répond encore, on attend
            await new Promise(r => setTimeout(r, POLL_INTERVAL));
            waited += POLL_INTERVAL;
          } catch {
            // Connexion refusée = backend mort, on peut continuer
            break;
          }
        }
      } catch {
        // Backend peut déjà être arrêté ou indisponible - on continue
      }

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
      
      // Gestion spécifique des erreurs d'installation Windows
      let errorMessage = 'Erreur inconnue';
      
      if (err instanceof Error) {
        errorMessage = err.message;
        
        // Messages d'erreur spécifiques pour diagnostiquer BUG-110
        if (errorMessage.includes('path') || errorMessage.includes('directory')) {
          errorMessage = `Erreur d'installation (répertoire): ${errorMessage}. Essayez d'installer THÉRÈSE dans C:\\Program Files\\ ou redémarrez en mode administrateur.`;
        } else if (errorMessage.includes('permission') || errorMessage.includes('access denied')) {
          errorMessage = `Permissions insuffisantes: ${errorMessage}. Redémarrez THÉRÈSE en mode administrateur pour installer la mise à jour.`;
        } else if (errorMessage.includes('signature') || errorMessage.includes('invalid')) {
          errorMessage = `Erreur de signature: ${errorMessage}. La mise à jour n'est pas authentique.`;
        }
      }
      
      setState({
        phase: 'error',
        message: errorMessage,
      });
    }
  }, []);

  const handleRestart = useCallback(async (version: string) => {
    try {
      // Attendre un peu avant le redémarrage pour laisser le temps aux processus de finir
      await new Promise(resolve => setTimeout(resolve, 1000));

      const { relaunch } = await import('@tauri-apps/plugin-process');
      await relaunch();

    } catch (relaunchError) {
      console.error('[UpdateBanner] Erreur relaunch:', relaunchError);

      // BUG-128 : à ce stade la mise à jour EST déjà téléchargée/installée
      // (on venait de la phase « ready ») ; seul le redémarrage automatique n'a
      // pas pu se déclencher. Sous Windows l'installeur NSIS passif (« /P /R »)
      // gère lui-même le restart et le process est en cours d'arrêt quand
      // relaunch() est appelé, ce qui fait légitimement échouer l'appel. Ce
      // n'est donc pas une erreur de mise à jour : on informe calmement et on
      // propose un redémarrage manuel plutôt qu'une alerte magenta trompeuse.
      setState({ phase: 'restart-required', version });
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
      data-testid="update-banner"
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
            data-testid="update-install-btn"
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
            Téléchargement de la v{state.version}...
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
            Mise à jour <strong className="text-accent-cyan">v{state.version}</strong> prête
          </span>
          <button
            onClick={() => handleRestart(state.version)}
            data-testid="update-restart-btn"
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
            Redémarrer pour installer
          </button>
        </>
      )}

      {state.phase === 'restart-required' && (
        <>
          <RefreshCw size={16} className="text-accent-cyan shrink-0" />
          <span className="text-text">
            Mise à jour <strong className="text-accent-cyan">v{state.version}</strong> installée.
            {' '}Ferme et rouvre THÉRÈSE pour l'appliquer.
          </span>
          <button
            onClick={() => handleRestart(state.version)}
            data-testid="update-restart-retry-btn"
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
            Réessayer
          </button>
        </>
      )}

      {state.phase === 'error' && (
        <>
          <span className="text-accent-magenta">{sanitizeErrorMessage(state.message)}</span>
        </>
      )}

      {/* Bouton fermer (sauf pendant le telechargement) */}
      {state.phase !== 'downloading' && (
        <button
          onClick={() => setDismissed(true)}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded text-text-muted hover:text-text transition-colors"
          aria-label="Fermer le bandeau de mise à jour"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}
