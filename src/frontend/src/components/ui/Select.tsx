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
          'w-full rounded-md px-3 py-2 text-sm transition-all duration-150 appearance-none',
          'bg-surface-2 border text-text',
          'focus:outline-none focus:ring-2 focus:ring-offset-0',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          // High contrast support
          'forced-colors:border-[ButtonText] forced-colors:focus:border-[Highlight]',
          // Normal state
          !error && 'border-border focus:ring-agent-cyan focus:border-agent-cyan/50',
          // Error state
          error && 'border-error/50 focus:ring-error focus:border-error/50',
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
