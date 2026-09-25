/**
 * Groupe de boutons exclusifs de la DA « Application affinée ».
 *
 * Pas de tablist : sans onglets, sans roving, sans flèches, un tablist
 * mentirait au lecteur d'écran. Motif déjà lu par les tests de l'établi :
 * role="group" nommé + aria-pressed.
 */
import { cn } from '../../lib/utils';
import { CLASSES_SEGMENTS, classeSegment } from './segments.classes';

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
  /** B-1370 : le segment choisi reçoit le focus initial du dialogue qui le contient. */
  focusInitial?: boolean;
}

export function Segments({ label, options, valeur, onChange, className, focusInitial = false }: SegmentsProps) {
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
            data-dialog-autofocus={focusInitial && presse ? true : undefined}
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
