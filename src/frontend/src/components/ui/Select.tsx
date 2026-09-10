/**
 * THERESE v2 - Select Component
 *
 * Select stylise avec options, placeholder et gestion d'erreur.
 * US-011 : Composants formulaire standardises
 */

import { forwardRef, type SelectHTMLAttributes } from 'react';
import { ChevronDown } from 'lucide-react';
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
      <div className="relative">
      <select
        ref={ref}
        aria-invalid={error || undefined}
        className={cn(
          'w-full rounded-sm px-3 py-2 text-sm min-h-9 appearance-none',
          'bg-surface border text-text',
          'focus:outline-none focus:ring-[3px]',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          'forced-colors:border-[ButtonText] forced-colors:focus:border-[Highlight]',
          !error && 'border-border focus:border-accent focus:ring-ring/30',
          error && 'border-error focus:border-error focus:ring-error/30',
          // B-292 / B-405 : la flèche est une icône peinte par un jeton du thème
          // (plus de SVG en data-URI au trait figé en #888), voir ci-dessous.
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
      <ChevronDown
        aria-hidden="true"
        className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted"
      />
      </div>
    );
  }
);

Select.displayName = 'Select';
