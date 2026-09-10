/**
 * Pilule sémantique ou de domaine de la DA « Application affinée ».
 *
 * Fonds = teintes opaques (`--color-*-tint`, `--color-domaine-*-tint`),
 * encre = jeton sémantique. Pas de color-mix translucide.
 *
 * `data-etiquette` est le crochet du contraste élevé : la règle
 * `[data-high-contrast="true"] [data-etiquette] { background: transparent;
 * border: 1px solid currentColor }` est posée dans globals.css par un
 * autre lot.
 */
import { type ReactNode } from 'react';

import { cn } from '../../lib/utils';

export type TonEtiquette = 'erreur' | 'attention' | 'succes' | 'info' | 'neutre';
export type DomaineEtiquette = 'agenda' | 'taches' | 'factures' | 'prospects';

const TONS: Record<TonEtiquette, string> = {
  erreur: 'bg-[var(--color-error-tint)] text-error',
  attention: 'bg-[var(--color-warning-tint)] text-warning',
  succes: 'bg-[var(--color-success-tint)] text-success',
  info: 'bg-[var(--color-info-tint)] text-info',
  neutre: 'bg-surface-2 text-text-muted',
};

const DOMAINES: Record<DomaineEtiquette, string> = {
  agenda: 'bg-domaine-agenda-tint text-domaine-agenda',
  taches: 'bg-domaine-taches-tint text-domaine-taches',
  factures: 'bg-domaine-factures-tint text-domaine-factures',
  prospects: 'bg-domaine-prospects-tint text-domaine-prospects',
};

export interface EtiquetteProps {
  ton?: TonEtiquette;
  domaine?: DomaineEtiquette;
  children: ReactNode;
  className?: string;
}

export function Etiquette({ ton = 'neutre', domaine, children, className }: EtiquetteProps) {
  return (
    <span
      data-etiquette=""
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-sm font-semibold whitespace-nowrap',
        domaine ? DOMAINES[domaine] : TONS[ton],
        className,
      )}
    >
      {children}
    </span>
  );
}
