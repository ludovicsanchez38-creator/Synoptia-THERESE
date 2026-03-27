/**
 * THERESE v2 - Select Component
 *
 * Select stylise avec options, placeholder et gestion d'erreur.
 * US-011 : Composants formulaire standardises
 */

import { forwardRef, type SelectHTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  error?: boolean;
  options: SelectOption[];
  placeholder?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, error, options, placeholder, ...props }, ref) => {
    return (
      <select
        ref={ref}
        aria-invalid={error || undefined}
        className={cn(
          'w-full rounded-lg px-3 py-2 text-sm transition-all duration-150 appearance-none',
          'bg-white/5 border text-text',
          'focus:outline-none focus:ring-2 focus:ring-offset-0',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          // High contrast support
          'forced-colors:border-[ButtonText] forced-colors:focus:border-[Highlight]',
          // Normal state
          !error && 'border-white/10 focus:ring-cyan-400 focus:border-cyan-400/50',
          // Error state
          error && 'border-red-500/50 focus:ring-red-400 focus:border-red-400/50',
          // Custom arrow
          'bg-[length:16px_16px] bg-[position:right_12px_center] bg-no-repeat',
          "bg-[url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23888' stroke-width='2'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E\")]",
          'pr-10',
          className
        )}
        {...props}
      >
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    );
  }
);

Select.displayName = 'Select';
