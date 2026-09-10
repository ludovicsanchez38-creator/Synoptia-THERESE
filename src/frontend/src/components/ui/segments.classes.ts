/**
 * Classes des segments de la DA « Application affinée », partagées entre
 * `Segments` (groupe + aria-pressed) et le variateur du brief (radiogroup) :
 * une seule source. Module sans composant (fast refresh).
 */
import { cn } from '../../lib/utils';

export const CLASSES_SEGMENTS = 'inline-flex gap-1 p-1 rounded-full bg-surface-2';

export function classeSegment(actif: boolean): string {
  return cn(
    'rounded-full px-3 py-1 text-sm font-medium',
    actif ? 'bg-surface text-text shadow-sm' : 'text-text-muted hover:text-text',
  );
}
