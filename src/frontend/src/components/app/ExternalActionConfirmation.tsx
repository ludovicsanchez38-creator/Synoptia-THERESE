import {
  useCallback,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { Loader2, ShieldCheck } from 'lucide-react';
import { Z_LAYER } from '../../styles/z-layers';
import {
  ExternalActionConfirmationContext,
  type ExternalActionPreview,
  type ExternalAction,
  type RequestExternalAction,
} from './useExternalActionConfirmation';

interface PendingExternalAction extends ExternalActionPreview {
  run: ExternalAction;
}

/** Couche commune aux effets externes déclenchés depuis l'interface 0.40. */
export function PrototypeExternalActionConfirmationProvider({ children }: { children: ReactNode }) {
  const [pending, setPending] = useState<PendingExternalAction | null>(null);
  const [busy, setBusy] = useState(false);
  const pendingRef = useRef<PendingExternalAction | null>(null);
  const busyRef = useRef(false);

  const clearPending = useCallback(() => {
    pendingRef.current = null;
    busyRef.current = false;
    setPending(null);
    setBusy(false);
  }, []);

  const request = useCallback<RequestExternalAction>((preview, action) => {
    // Le verrou synchrone empêche deux clics rapprochés d'empiler la même action.
    if (pendingRef.current) return;

    const next = { ...preview, run: action };
    pendingRef.current = next;
    setPending(next);
  }, []);

  const confirm = useCallback(async () => {
    const action = pendingRef.current;
    if (!action || busyRef.current) return;

    busyRef.current = true;
    setBusy(true);
    try {
      await action.run();
    } finally {
      clearPending();
    }
  }, [clearPending]);

  return (
    <ExternalActionConfirmationContext.Provider value={request}>
      {children}
      {pending && (
        <div
          className={`fixed inset-0 ${Z_LAYER.WIZARD} flex items-center justify-center px-4`}
          data-testid="external-action-confirmation-layer"
        >
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="external-action-confirmation-title"
            className="relative w-full max-w-lg rounded-xl border border-accent-cyan/30 bg-surface p-5 shadow-2xl"
            data-testid="external-action-confirmation"
          >
            <div className="flex items-start gap-3">
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-[9px] bg-accent-tint text-accent">
                <ShieldCheck className="h-4 w-4" />
              </span>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-accent">Aperçu avant action</p>
                <h2 id="external-action-confirmation-title" className="mt-1 text-base font-semibold text-text">
                  {pending.title}
                </h2>
                <p className="mt-1 text-sm leading-5 text-text-muted">{pending.description}</p>
              </div>
            </div>

            <dl className="mt-4 space-y-2 rounded-[10px] border border-border bg-bg p-3 text-sm">
              {pending.details.filter((detail) => detail.value).map((detail) => (
                <div key={detail.label} className="grid gap-1 sm:grid-cols-[8rem_minmax(0,1fr)]">
                  <dt className="font-medium text-text-muted">{detail.label}</dt>
                  <dd className="whitespace-pre-wrap break-words text-text">{detail.value}</dd>
                </div>
              ))}
            </dl>

            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={clearPending}
                disabled={busy}
                className="rounded-[8px] border border-border bg-surface px-3 py-2 text-sm font-semibold text-text disabled:opacity-50"
              >
                Annuler
              </button>
              <button
                type="button"
                onClick={() => void confirm()}
                disabled={busy}
                className="inline-flex items-center gap-2 rounded-[8px] bg-text px-3 py-2 text-sm font-semibold text-white disabled:opacity-50"
              >
                {busy && <Loader2 className="h-4 w-4 animate-spin" />}
                {pending.confirmLabel}
              </button>
            </div>
          </div>
        </div>
      )}
    </ExternalActionConfirmationContext.Provider>
  );
}
