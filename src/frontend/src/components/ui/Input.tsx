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
            'w-full rounded-sm px-3 py-2 text-sm min-h-9',
            'bg-surface border text-text placeholder:text-text-muted',
            'focus:outline-none focus:ring-[3px]',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'forced-colors:border-[ButtonText] forced-colors:focus:border-[Highlight]',
            !error && 'border-border focus:border-accent focus:ring-ring/30',
            error && 'border-error focus:border-error focus:ring-error/30',
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
