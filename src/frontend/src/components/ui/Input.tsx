/**
 * THERESE v2 - Input Component
 *
 * Input stylise avec variantes, icone et gestion d'erreur.
 * US-011 : Composants formulaire standardises
 */

import { forwardRef, type InputHTMLAttributes, type ReactNode } from 'react';
import { cn } from '../../lib/utils';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
  icon?: ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, error, icon, ...props }, ref) => {
    return (
      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none">
            {icon}
          </div>
        )}
        <input
          ref={ref}
          aria-invalid={error || undefined}
          className={cn(
            'w-full rounded-lg px-3 py-2 text-sm transition-all duration-150',
            'bg-white/5 border text-text placeholder:text-text-muted/50',
            'focus:outline-none focus:ring-2 focus:ring-offset-0',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            // High contrast support
            'forced-colors:border-[ButtonText] forced-colors:focus:border-[Highlight]',
            // Normal state
            !error && 'border-white/10 focus:ring-cyan-400 focus:border-cyan-400/50',
            // Error state
            error && 'border-red-500/50 focus:ring-red-400 focus:border-red-400/50',
            // Icon padding
            icon && 'pl-10',
            className
          )}
          {...props}
        />
      </div>
    );
  }
);

Input.displayName = 'Input';
