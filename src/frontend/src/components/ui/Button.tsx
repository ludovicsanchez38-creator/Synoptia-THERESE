import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'icon';
}

// DA « Application affinée » (lot 1, 10/09/2026) : `.btn` de base.css.
// 36 px, sans ombre ni soulèvement ; le primaire est le remplissage cyan,
// le secondaire une surface bordée, le discret (ghost) est écrit en accent,
// le danger repose sur la teinte d'erreur. Le grand geste d'un écran garde
// 44 px (`lg`). L'API ne change pas : les 254 usages compilent tels quels.

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
          'transition-colors',
          variant === 'primary' && 'bg-accent-fill text-accent-ink hover:brightness-[.96]',
          variant === 'secondary' && 'border border-border bg-surface text-text hover:bg-surface-2',
          variant === 'ghost' && 'bg-transparent text-accent hover:bg-accent-tint',
          variant === 'danger' && 'bg-[var(--color-error-tint)] text-error hover:brightness-95',
          size === 'sm' && 'h-8 px-3 text-sm rounded-sm',
          size === 'md' && 'h-9 px-4 text-sm rounded-md',
          size === 'lg' && 'h-11 px-6 text-base rounded-md',
          size === 'icon' && 'h-9 w-9 rounded-md',
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
