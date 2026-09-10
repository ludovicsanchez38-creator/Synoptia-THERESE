/**
 * Bandeau d'erreur de la DA « Application affinée ».
 *
 * Ton limité à « erreur » dans ce lot. Fond = teinte opaque
 * `--color-error-tint`, pas un color-mix. L'icône est décorative.
 */
import { type ReactNode } from 'react';

import { cn } from '../../lib/utils';

export interface AlerteProps {
  ton?: 'erreur';
  titre?: string;
  icone?: ReactNode;
  children?: ReactNode;
  className?: string;
}

export function Alerte({ ton: _ton = 'erreur', titre, icone, children, className }: AlerteProps) {
  return (
    <div
      role="alert"
      className={cn(
        'flex gap-3 items-start px-4 py-3 rounded-sm bg-[var(--color-error-tint)] border border-error/30 text-text',
        className,
      )}
    >
      {icone != null ? (
        <span aria-hidden="true" className="shrink-0">
          {icone}
        </span>
      ) : null}
      <div>
        {titre ? <b className="text-error">{titre}</b> : null}
        {children ? <p>{children}</p> : null}
      </div>
    </div>
  );
}
