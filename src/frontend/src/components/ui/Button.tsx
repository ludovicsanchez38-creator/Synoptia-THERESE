import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'icon';
}

// DA « brutaliste éditorial » : primary/secondary/danger portent .btn-brutal
// (globals.css), une classe NON-layered. Conséquence : un border-*/shadow-*
// passé en className sera ignoré sur ces variants (twMerge ne déduplique que
// les utilities Tailwind). Pour un style de bordure custom, utiliser ghost.

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', disabled, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled}
        className={cn(
          'inline-flex items-center justify-center font-semibold',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-bg',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          // DA brutaliste éditorial : bordure encre + ombre dure, le bouton
          // « s'enfonce » au clic (.btn-brutal dans globals.css)
          variant === 'primary' && 'btn-brutal bg-accent-fill text-accent-ink',
          variant === 'secondary' && 'btn-brutal bg-surface text-text',
          variant === 'ghost' &&
            'bg-transparent font-medium text-text-muted transition-colors hover:text-text hover:bg-surface-elevated/50 active:translate-y-px',
          variant === 'danger' && 'btn-brutal btn-brutal-danger bg-error/10 text-error',
          // Sizes
          size === 'sm' && 'h-8 px-3 text-sm rounded-md',
          size === 'md' && 'h-11 px-4 text-sm rounded-[7px]',
          size === 'lg' && 'h-12 px-6 text-base rounded-[7px]',
          size === 'icon' && 'h-11 w-11 rounded-[7px]',
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
