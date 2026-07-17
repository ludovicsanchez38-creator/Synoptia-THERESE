import { useEffect, useState } from 'react';
import { RefreshCw, TriangleAlert } from 'lucide-react';

type SidecarStatus = { state: 'restarting' | 'failed' | 'running'; attempt: number };

/**
 * Bandeau d'état du moteur local (sidecar backend) - revue 0.40.
 *
 * Rust émet `sidecar-status` à chaque relance automatique (3 tentatives à
 * délai progressif) puis en cas d'abandon. Avant, une panne du sidecar était
 * silencieuse et imposait de relancer toute l'application.
 */
export function SidecarStatusBanner() {
  const [status, setStatus] = useState<SidecarStatus | null>(null);

  useEffect(() => {
    if (!('__TAURI__' in window)) return;
    let disposed = false;
    let unlisten: (() => void) | undefined;
    void import('@tauri-apps/api/event').then(({ listen }) =>
      listen<SidecarStatus>('sidecar-status', (event) => setStatus(event.payload)).then((un) => {
        if (disposed) un();
        else unlisten = un;
      }),
    );
    return () => {
      disposed = true;
      unlisten?.();
    };
  }, []);

  if (!status || status.state === 'running') return null;

  if (status.state === 'restarting') {
    return (
      <div
        role="status"
        aria-live="polite"
        className="flex items-center justify-center gap-2 border-b border-border bg-surface-2 px-4 py-1.5 text-xs font-semibold text-text"
      >
        <RefreshCw className="h-3.5 w-3.5 animate-spin text-accent" />
        Le moteur local redémarre{status.attempt > 0 ? ` (tentative ${status.attempt}/3)` : ''}…
      </div>
    );
  }

  return (
    <div
      role="alert"
      className="flex flex-wrap items-center justify-center gap-3 border-b border-error/40 bg-[var(--color-error-tint)] px-4 py-1.5 text-xs font-semibold text-error"
    >
      <span className="inline-flex items-center gap-2">
        <TriangleAlert className="h-3.5 w-3.5" />
        Le moteur local ne répond plus après 3 relances.
      </span>
      <button
        type="button"
        className="rounded-[6px] border border-error px-2 py-1 font-semibold text-error transition-colors hover:bg-error-fill/10"
        onClick={() => {
          setStatus({ state: 'restarting', attempt: 0 });
          void import('@tauri-apps/api/core').then(({ invoke }) =>
            invoke('restart_backend').catch(() => {
              setStatus({ state: 'failed', attempt: 3 });
            }),
          );
        }}
      >
        Relancer le moteur local
      </button>
    </div>
  );
}
