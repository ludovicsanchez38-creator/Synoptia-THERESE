/**
 * Rangée de liste de la DA « Application affinée ».
 *
 * Cliquable : le titre est un bouton étiré (`before:absolute before:inset-0`
 * sur une rangée `relative`). Les actions de `droite` passent au-dessus
 * (`relative z-10`) mais seuls les vrais interactifs y reçoivent le pointeur
 * (bouton, lien, champ) : une heure ou un chevron restent transparents au
 * bouton étiré. Un seul interactif pour la rangée, Entrée et Espace natifs. Non cliquable : aucun rôle, aucun tabIndex.
 *
 * Le détail est en `text-sm` : la ligne se clique, `text-xs` est interdit
 * sur un interactif (plancher typographique).
 */
import { type MouseEventHandler, type ReactNode } from 'react';

import { cn } from '../../lib/utils';

export type DomaineLigne = 'agenda' | 'taches' | 'factures' | 'prospects';

const FOND_DOMAINE: Record<DomaineLigne, string> = {
  agenda: 'bg-domaine-agenda-tint text-domaine-agenda',
  taches: 'bg-domaine-taches-tint text-domaine-taches',
  factures: 'bg-domaine-factures-tint text-domaine-factures',
  prospects: 'bg-domaine-prospects-tint text-domaine-prospects',
};

export interface LigneProps {
  puce?: ReactNode;
  domaine?: DomaineLigne;
  titre: string;
  detail?: string;
  droite?: ReactNode;
  dense?: boolean;
  /**
   * Lot 7 : coupe le libellé ET le détail à une ligne, pour une liste dont
   * les rangées doivent garder la même hauteur (l'historique de Décision).
   * `block w-full` est nécessaire : un bouton inline-block à largeur
   * automatique déborde la cellule `1fr` au lieu d'être coupé. Jamais
   * `relative` dessus : le `before:absolute before:inset-0` se cale sur la
   * rangée, le positionner rabattrait le pseudo-élément sur le texte et
   * tuerait le clic étiré (P1 de la revue du lot 1).
   */
  coupe?: boolean;
  onClick?: MouseEventHandler<HTMLButtonElement>;
  className?: string;
}

export function Ligne({
  puce,
  domaine,
  titre,
  detail,
  droite,
  dense = false,
  coupe = false,
  onClick,
  className,
}: LigneProps) {
  const cliquable = onClick != null;
  const coupeDuLibelle = coupe ? 'block w-full truncate' : undefined;
  const libelle = cliquable ? (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "font-semibold text-left text-text before:absolute before:inset-0 before:content-['']",
        coupeDuLibelle,
      )}
    >
      {titre}
    </button>
  ) : (
    <span className={cn('font-semibold text-text', coupeDuLibelle)}>{titre}</span>
  );

  return (
    <div
      className={cn(
        'grid grid-cols-[2rem_1fr_auto] gap-3 items-center px-4 border-t border-border hover:bg-surface-2',
        dense ? 'py-2' : 'py-3',
        cliquable && 'relative',
        className,
      )}
    >
      <span
        aria-hidden={puce == null ? true : undefined}
        className={cn(
          'grid h-8 w-8 place-items-center rounded-sm',
          domaine ? FOND_DOMAINE[domaine] : 'bg-surface-2 text-text-muted',
        )}
      >
        {puce}
      </span>
      <div className="min-w-0">
        {libelle}
        {detail ? (
          <p className={cn('text-sm text-text-muted', coupe && 'truncate')}>{detail}</p>
        ) : null}
      </div>
      {droite != null ? (
        <div className={cn('flex items-center gap-2 text-text-muted', cliquable &&
            'relative z-10 pointer-events-none [&_button]:pointer-events-auto [&_a]:pointer-events-auto [&_input]:pointer-events-auto [&_select]:pointer-events-auto [&_textarea]:pointer-events-auto [&_[role=button]]:pointer-events-auto')}>
          {droite}
        </div>
      ) : (
        <span />
      )}
    </div>
  );
}
