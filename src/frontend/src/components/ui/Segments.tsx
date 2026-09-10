/**
 * Groupe de boutons exclusifs de la DA « Application affinée ».
 *
 * Pas de tablist : sans onglets, sans roving, sans flèches, un tablist
 * mentirait au lecteur d'écran. Motif déjà lu par les tests de l'établi :
 * role="group" nommé + aria-pressed.
 */
import { cn } from '../../lib/utils';

export interface OptionSegment {
  id: string;
  label: string;
}

export interface SegmentsProps {
  label: string;
  options: OptionSegment[];
  valeur: string;
  onChange: (id: string) => void;
  className?: string;
}

/** Lot 2 : classes partagées avec le variateur du brief (radiogroup) : une seule source. */
export const CLASSES_SEGMENTS = 'inline-flex gap-1 p-1 rounded-full bg-surface-2';

export function classeSegment(actif: boolean): string {
  return cn(
    'rounded-full px-3 py-1 text-sm font-medium',
    actif ? 'bg-surface text-text shadow-sm' : 'text-text-muted hover:text-text',
  );
}

export function Segments({ label, options, valeur, onChange, className }: SegmentsProps) {
  return (
    <div
      role="group"
      aria-label={label}
      className={cn(CLASSES_SEGMENTS, className)}
    >
      {options.map((option) => {
        const presse = option.id === valeur;
        return (
          <button
            key={option.id}
            type="button"
            aria-pressed={presse}
            onClick={() => onChange(option.id)}
            className={classeSegment(presse)}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
