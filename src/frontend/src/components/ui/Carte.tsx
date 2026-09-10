/**
 * Surface de la DA « Application affinée » : une carte, et sa tête.
 *
 * Ombre sm uniquement (jamais le jeton global --shadow-card : cinq canevas
 * hors lot le consomment encore). L'icône de tête est une pastille ronde
 * accent, 2 rem : c'est le glyphe de domaine, pas un bouton.
 */
import { type HTMLAttributes, type ReactNode } from 'react';

import { cn } from '../../lib/utils';

export interface CarteProps extends HTMLAttributes<HTMLElement> {
  as?: 'article' | 'section';
  children?: ReactNode;
}

export function Carte({ as: Tag = 'article', className, children, ...props }: CarteProps) {
  return (
    <Tag
      className={cn('bg-surface border border-border rounded-md shadow-sm', className)}
      {...props}
    >
      {children}
    </Tag>
  );
}

export interface CarteTeteProps {
  icone?: ReactNode;
  titre: string;
  /** Lot 2 : id du h2, pour qu'une section puisse s'en nommer (`aria-labelledby`). */
  idTitre?: string;
  meta?: string;
  actions?: ReactNode;
  className?: string;
}

export function CarteTete({ icone, titre, idTitre, meta, actions, className }: CarteTeteProps) {
  return (
    // Lot 2 : `flex-wrap`, et sous 840 px les actions prennent une ligne
    // entière sous le titre (`basis-full`) au lieu de le comprimer.
    <div className={cn('flex flex-wrap items-center gap-3 px-4 pt-4 pb-2', className)}>
      {icone != null && (
        <span
          aria-hidden="true"
          className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-accent-tint text-accent"
        >
          {icone}
        </span>
      )}
      <div className="min-w-0 flex-1">
        <h2 id={idTitre}>{titre}</h2>
        {meta ? <p className="text-xs font-medium text-text-muted">{meta}</p> : null}
      </div>
      {actions ? (
        <div className="ml-auto flex flex-wrap gap-2 max-[840px]:basis-full max-[840px]:ml-0">{actions}</div>
      ) : null}
    </div>
  );
}
