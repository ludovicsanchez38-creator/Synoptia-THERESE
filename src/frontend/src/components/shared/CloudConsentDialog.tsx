import { useRef } from 'react';
import { createPortal } from 'react-dom';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { MEMORY_CARDS_CATEGORY } from '../../lib/consent';
import { Z_LAYER } from '../../styles/z-layers';

interface Props {
  title: string;
  dataCategories: string[];
  onCancel: () => void;
  onConfirm: () => void;
  busy?: boolean;
  error?: string | null;
  testId: string;
}

/** Même demande explicite et même présentation des données dans le chat et l’Atelier. */
export function CloudConsentDialog({ title, dataCategories, onCancel, onConfirm, busy = false, error, testId }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  useDialogFocusTrap(ref, { active: true, onEscape: onCancel, isolateBackground: true });
  return createPortal(
    <div className={`fixed inset-0 ${Z_LAYER.MODAL} grid place-items-center bg-surface/90 p-4`}>
      <div ref={ref} role="alertdialog" aria-modal="true" aria-label={title} className="max-h-full w-full max-w-lg overflow-y-auto rounded-md border border-warning/40 bg-[var(--color-warning-tint)] p-4 text-sm text-warning" data-testid={testId}>
        <p className="font-semibold">{title}</p>
        <p className="mt-1">Données transmises : {dataCategories.filter(c => c !== MEMORY_CARDS_CATEGORY).join(', ')}.</p>
        {error && <p role="alert" className="mt-2 text-error">{error}</p>}
        <div className="mt-3 flex justify-end gap-2">
          <button type="button" data-dialog-autofocus onClick={onCancel} className="rounded-sm border border-border bg-surface px-3 py-2 text-sm font-semibold text-text">Annuler</button>
          <button type="button" onClick={onConfirm} disabled={busy} className="rounded-sm bg-accent-fill px-3 py-2 text-sm font-semibold text-accent-ink">{busy ? 'Enregistrement de ton accord…' : 'Autoriser et envoyer'}</button>
        </div>
      </div>
    </div>, document.body
  );
}
