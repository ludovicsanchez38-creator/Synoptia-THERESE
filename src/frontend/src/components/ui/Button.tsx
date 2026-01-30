import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'icon';
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', disabled, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled}
        className={cn(
          'inline-flex items-center justify-center font-medium transition-all duration-150',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-bg',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          'active:scale-[0.98]',
          // Variants with premium glow effects
          variant === 'primary' &&
            'bg-accent-cyan text-bg hover:bg-accent-cyan/90 hover:shadow-[0_0_20px_rgba(34,211,238,0.3)] hover:-translate-y-0.5',
          variant === 'secondary' &&
            'bg-surface-elevated text-text border border-border hover:bg-surface hover:border-accent-cyan/50 hover:shadow-[0_0_15px_rgba(34,211,238,0.1)]',
          variant === 'ghost' &&
            'bg-transparent text-text-muted hover:text-text hover:bg-surface-elevated/50',
          variant === 'danger' &&
            'bg-error/10 text-error border border-error/20 hover:bg-error/20 hover:shadow-[0_0_15px_rgba(239,68,68,0.2)]',
          // Sizes
          size === 'sm' && 'h-8 px-3 text-sm rounded-md',
          size === 'md' && 'h-10 px-4 text-sm rounded-lg',
          size === 'lg' && 'h-12 px-6 text-base rounded-lg',
          size === 'icon' && 'h-10 w-10 rounded-lg',
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
