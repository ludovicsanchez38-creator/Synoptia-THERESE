/**
 * Bandeau d'erreur de la DA « Application affinée ».
 *
 * Deux tons depuis le lot 9 : « erreur » (défaut) et « attention ». Une
 * lecture partielle des réglages n'est pas une panne, l'écran fonctionne avec
 * des valeurs par défaut : la teinter en rouge dirait autre chose que ce qui
 * s'est passé. Fond = teinte opaque (`--color-*-tint`), pas un color-mix.
 * L'icône est décorative, et `role="alert"` vaut pour les deux tons.
 */
import { type HTMLAttributes, type ReactNode } from 'react';

import { cn } from '../../lib/utils';

export type TonAlerte = 'erreur' | 'attention';

const TONS: Record<TonAlerte, { fond: string; titre: string }> = {
  erreur: { fond: 'bg-[var(--color-error-tint)] border-error/30', titre: 'text-error' },
  attention: { fond: 'bg-[var(--color-warning-tint)] border-warning/30', titre: 'text-warning' },
};

export interface AlerteProps extends HTMLAttributes<HTMLDivElement> {
  ton?: TonAlerte;
  titre?: string;
  icone?: ReactNode;
  children?: ReactNode;
  /** Lot 2 : un geste sous le texte (« Réessayer »), hors du paragraphe. */
  action?: ReactNode;
  className?: string;
}

export function Alerte({ ton = 'erreur', titre, icone, children, action, className, ...props }: AlerteProps) {
  const teinte = TONS[ton];
  return (
    <div
      {...props}
      role="alert"
      className={cn(
        'flex gap-3 items-start px-4 py-3 rounded-sm border text-text',
        teinte.fond,
        className,
      )}
    >
      {icone != null ? (
        <span aria-hidden="true" className="shrink-0">
          {icone}
        </span>
      ) : null}
      <div>
        {titre ? <b className={teinte.titre}>{titre}</b> : null}
        {children ? <p>{children}</p> : null}
        {action ? <div className="mt-2">{action}</div> : null}
      </div>
    </div>
  );
}
