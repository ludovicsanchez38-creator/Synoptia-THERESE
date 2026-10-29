import { MEMORY_CARDS_CATEGORY } from '../../lib/consent';

interface Props {
  title: string;
  dataCategories: string[];
  onCancel: () => void;
  onConfirm: () => void;
  busy?: boolean;
  testId: string;
}

/** Même demande explicite et même présentation des données dans le chat et l’Atelier. */
export function CloudConsentDialog({ title, dataCategories, onCancel, onConfirm, busy = false, testId }: Props) {
  return (
    <div role="alertdialog" aria-label={title} className="mb-3 rounded-md border border-warning/40 bg-[var(--color-warning-tint)] p-4 text-sm text-warning" data-testid={testId}>
      <p className="font-semibold">{title}</p>
      <p className="mt-1">Données transmises : {dataCategories.filter(c => c !== MEMORY_CARDS_CATEGORY).join(', ')}.</p>
      <div className="mt-3 flex justify-end gap-2">
        <button type="button" onClick={onCancel} className="rounded-sm border border-border bg-surface px-3 py-2 text-sm font-semibold text-text">Annuler</button>
        <button type="button" onClick={onConfirm} disabled={busy} className="rounded-sm bg-accent-fill px-3 py-2 text-sm font-semibold text-accent-ink">{busy ? 'Enregistrement de ton accord…' : 'Autoriser et envoyer'}</button>
      </div>
    </div>
  );
}
