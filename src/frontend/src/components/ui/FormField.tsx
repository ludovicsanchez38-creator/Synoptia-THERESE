/**
 * THERESE v2 - FormField Component
 *
 * Wrapper pour champs de formulaire avec label, description et erreur.
 * US-011 : Composants formulaire standardises
 */

import { type ReactNode } from 'react';
import { cn } from '../../lib/utils';

export interface FormFieldProps {
  label: string;
  description?: string;
  error?: string;
  required?: boolean;
  htmlFor?: string;
  className?: string;
  children: ReactNode;
}

export function FormField({
  label,
  description,
  error,
  required,
  htmlFor,
  className,
  children,
}: FormFieldProps) {
  const errorId = htmlFor ? `${htmlFor}-error` : undefined;
  const descId = htmlFor ? `${htmlFor}-desc` : undefined;

  return (
    <div className={cn('space-y-1.5', className)}>
      <label
        htmlFor={htmlFor}
        className={cn(
          'block text-sm font-medium transition-colors',
          error ? 'text-red-400' : 'text-text'
        )}
      >
        {label}
        {required && <span className="text-red-400 ml-0.5" aria-hidden="true">*</span>}
      </label>

      {description && (
        <p id={descId} className="text-xs text-text-muted">
          {description}
        </p>
      )}

      {children}

      {error && (
        <p
          id={errorId}
          role="alert"
          className="text-xs text-red-400 mt-1"
        >
          {error}
        </p>
      )}
    </div>
  );
}
