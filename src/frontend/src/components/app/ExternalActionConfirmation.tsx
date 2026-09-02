import {
  useCallback,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { ShieldCheck } from 'lucide-react';
import { Z_LAYER } from '../../styles/z-layers';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import {
  ExternalActionConfirmationContext,
  type ExternalActionPreview,
  type ExternalAction,
  type RequestExternalAction,
} from './useExternalActionConfirmation';
import { Spinner } from '../ui/Spinner';

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

  // B-251 : la carte annonçait `role="dialog" aria-modal="true"` sans rien
  // tenir de ce que `useDialogFocusTrap` déclare être la « source unique de
  // vérité du comportement modal clavier » — focus initial, Tab bouclé, Échap,
  // retour du focus au déclencheur. Un utilisateur au clavier s'entendait
  // annoncer une boîte de dialogue tout en tabulant dans la page qui la porte.
  const dialogRef = useRef<HTMLDivElement | null>(null);
  // Échap ABANDONNE l'action, comme le bouton « Annuler » — et comme lui, il
  // se tait pendant que l'effet externe est en vol : offrir une sortie que
  // l'écran refuse escamoterait la carte au-dessus d'une action déjà partie.
  // Le rappel reste STABLE : le hook lit `onEscape` par un ref, mais une
  // identité qui change à chaque rendu réarmerait quand même le piège.
  const abandonnerSiPossible = useCallback(() => {
    if (busyRef.current) return;
    clearPending();
  }, [clearPending]);

  useDialogFocusTrap(dialogRef, { active: pending !== null, onEscape: abandonnerSiPossible });

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
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="external-action-confirmation-title"
            className="relative w-full max-w-lg rounded-md border border-accent-cyan/30 bg-surface p-5 shadow-2xl"
            data-testid="external-action-confirmation"
          >
            <div className="flex items-start gap-3">
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-md bg-accent-tint text-accent">
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

            <dl className="mt-4 space-y-2 rounded-md border border-border bg-bg p-3 text-sm">
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
                className="rounded-sm border border-border bg-surface px-3 py-2 text-sm font-semibold text-text disabled:opacity-50"
              >
                Annuler
              </button>
              <button
                type="button"
                onClick={() => void confirm()}
                disabled={busy}
                className="inline-flex items-center gap-2 rounded-sm bg-accent-fill px-3 py-2 text-sm font-semibold text-accent-ink disabled:opacity-50"
              >
                {busy && <Spinner taille="bouton" />}
                {pending.confirmLabel}
              </button>
            </div>
          </div>
        </div>
      )}
    </ExternalActionConfirmationContext.Provider>
  );
}
