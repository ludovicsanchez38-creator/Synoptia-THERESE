import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'icon';
}

// DA « Équilibre » : primary/secondary/danger portent .btn-da (globals.css),
// une classe NON-layered qui pose l'ombre douce et le soulèvement au survol.
// Conséquence inchangée : un shadow-* passé en className sera ignoré sur ces
// variants (twMerge ne déduplique que les utilities Tailwind). Pour une ombre
// custom, utiliser ghost.

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', disabled, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled}
        className={cn(
          'inline-flex items-center justify-center font-semibold',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          // DA « Équilibre » : l'accent d'action est le remplissage cyan,
          // le secondaire est une surface bordée.
          variant === 'primary' && 'btn-da bg-accent-fill text-accent-ink',
          variant === 'secondary' && 'btn-da border border-border bg-surface text-text',
          variant === 'ghost' &&
            'bg-transparent font-medium text-text-muted transition-colors hover:text-text hover:bg-surface-elevated/50 active:translate-y-px',
          variant === 'danger' && 'btn-da border border-error bg-error/10 text-error',
          // Rayons : petit bouton, petit rayon. Le lot 3 du 30/08/2026 les
          // avait inversés en gonflant --radius-md de 8 à 14 px sans toucher
          // aux classes, ce qui donnait une pilule de 32 px de haut à côté
          // d'un bouton d'action de 44 px presque carré.
          // Sizes
          size === 'sm' && 'h-8 px-3 text-sm rounded-sm',
          size === 'md' && 'h-11 px-4 text-sm rounded-md',
          size === 'lg' && 'h-12 px-6 text-base rounded-md',
          size === 'icon' && 'h-11 w-11 rounded-md',
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
