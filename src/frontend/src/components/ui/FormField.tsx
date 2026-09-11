/**
 * THERESE v2 - FormField Component
 *
 * Wrapper pour champs de formulaire avec label, description et erreur.
 * US-011 : Composants formulaire standardises
 */

import { Children, cloneElement, isValidElement, type ReactElement, type ReactNode } from 'react';
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

  /* Ces deux identifiants étaient calculés… et jamais posés. Un lecteur
     d'écran annonçait le champ et son label, mais ni l'explication ni le
     message d'erreur : le rouge sous le champ n'existait que pour l'œil.
     On rattache donc ici, à l'endroit qui connaît les deux. */
  const rattachements = [description && descId, error && errorId]
    .filter(Boolean)
    .join(' ');

  const champDecrit = Children.map(children, (enfant) => {
    if (!isValidElement(enfant)) return enfant;
    const existant = (enfant.props as { 'aria-describedby'?: string })['aria-describedby'];
    const decrit = [existant, rattachements].filter(Boolean).join(' ');
    return cloneElement(enfant as ReactElement<Record<string, unknown>>, {
      ...(decrit ? { 'aria-describedby': decrit } : {}),
      ...(error ? { 'aria-invalid': true } : {}),
    });
  });

  return (
    <div className={cn('space-y-1.5', className)}>
      <label
        htmlFor={htmlFor}
        className={cn(
          'block text-sm font-semibold transition-colors',
          error ? 'text-error' : 'text-text'
        )}
      >
        {label}
        {required && <span className="text-error ml-0.5" aria-hidden="true">*</span>}
      </label>

      {/* Lot 9 : ces deux textes passent en 14 px. Ils sont rattachés au champ
          par aria-describedby, donc liés à un interactif, et la règle du lot y
          bannit 12 px. */}
      {description && (
        <p id={descId} className="text-sm text-text-muted">
          {description}
        </p>
      )}

      {champDecrit}

      {error && (
        <p
          id={errorId}
          role="alert"
          className="text-sm text-error mt-1"
        >
          {error}
        </p>
      )}
    </div>
  );
}
