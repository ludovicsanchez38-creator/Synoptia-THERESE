/**
 * Barre de chargement de la DA « Application affinée ».
 *
 * Décorative (`aria-hidden`) : Spinner reste l'attente qu'on annonce.
 * L'animation `glisse` est déclarée ici, pas dans globals.css. Elle s'arrête
 * sous les filets déjà posés : prefers-reduced-motion (globals.css l.479)
 * et html[data-reduce-motion="true"] (globals.css l.491).
 */
import { cn } from '../../lib/utils';

export interface SqueletteProps {
  largeur?: string;
  lignes?: number;
  className?: string;
}

const STYLE_GLISSE = `@keyframes glisse { to { background-position: -200% 0; } }`;

export function Squelette({ largeur = 'w-full', lignes = 1, className }: SqueletteProps) {
  const barres = Array.from({ length: Math.max(1, lignes) }, (_, i) => (
    <div
      key={i}
      className={cn(
        'h-3 rounded-full animate-[glisse_1.2s_linear_infinite]',
        'bg-[linear-gradient(90deg,var(--color-surface-2),var(--color-border),var(--color-surface-2))]',
        '[background-size:200%_100%]',
        largeur,
      )}
    />
  ));

  return (
    <div aria-hidden="true" className={cn('flex flex-col gap-2', className)}>
      <style>{STYLE_GLISSE}</style>
      {barres}
    </div>
  );
}
