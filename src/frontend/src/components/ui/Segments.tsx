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

export function Segments({ label, options, valeur, onChange, className }: SegmentsProps) {
  return (
    <div
      role="group"
      aria-label={label}
      className={cn('inline-flex gap-1 p-1 rounded-full bg-surface-2', className)}
    >
      {options.map((option) => {
        const presse = option.id === valeur;
        return (
          <button
            key={option.id}
            type="button"
            aria-pressed={presse}
            onClick={() => onChange(option.id)}
            className={cn(
              'rounded-full px-3 py-1 text-sm font-medium',
              presse ? 'bg-surface text-text shadow-sm' : 'text-text-muted',
            )}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
