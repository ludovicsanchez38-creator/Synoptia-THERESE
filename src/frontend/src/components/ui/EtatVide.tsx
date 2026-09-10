/**
 * État vide de la DA « Application affinée ».
 *
 * Titre en h3 (couleur texte), corps muted, geste optionnel sous le texte.
 * Pas de live region : le titre suffit au parcours.
 */
import { type ReactNode } from 'react';

import { cn } from '../../lib/utils';

export interface EtatVideProps {
  titre: string;
  children?: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function EtatVide({ titre, children, action, className }: EtatVideProps) {
  return (
    <div className={cn('px-4 py-8 text-center text-text-muted', className)}>
      <h3 className="text-text mb-1">{titre}</h3>
      {children ? <p>{children}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}
