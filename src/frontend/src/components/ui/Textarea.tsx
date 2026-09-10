/**
 * THERESE v2 - Textarea Component
 *
 * Textarea stylise avec auto-resize optionnel et gestion d'erreur.
 * US-011 : Composants formulaire standardises
 */

import { forwardRef, useCallback, useEffect, useRef, type TextareaHTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
  autoResize?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, autoResize, onChange, ...props }, ref) => {
    const internalRef = useRef<HTMLTextAreaElement | null>(null);

    const setRefs = useCallback(
      (node: HTMLTextAreaElement | null) => {
        internalRef.current = node;
        if (typeof ref === 'function') {
          ref(node);
        } else if (ref) {
          (ref as React.MutableRefObject<HTMLTextAreaElement | null>).current = node;
        }
      },
      [ref]
    );

    const adjustHeight = useCallback(() => {
      const textarea = internalRef.current;
      if (!textarea || !autoResize) return;
      textarea.style.height = 'auto';
      textarea.style.height = `${textarea.scrollHeight}px`;
    }, [autoResize]);

    useEffect(() => {
      adjustHeight();
    }, [adjustHeight, props.value]);

    const handleChange = useCallback(
      (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        onChange?.(e);
        if (autoResize) {
          adjustHeight();
        }
      },
      [onChange, autoResize, adjustHeight]
    );

    return (
      <textarea
        ref={setRefs}
        aria-invalid={error || undefined}
        onChange={handleChange}
        className={cn(
          'w-full rounded-sm px-3 py-2 text-sm min-h-9',
          'bg-surface border text-text placeholder:text-text-muted',
          'focus:outline-none focus:ring-[3px]',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          'forced-colors:border-[ButtonText] forced-colors:focus:border-[Highlight]',
          !error && 'border-border focus:border-accent focus:ring-ring/30',
          error && 'border-error focus:border-error focus:ring-error/30',
          autoResize ? 'resize-none overflow-hidden' : 'resize-y',
          className
        )}
        {...props}
      />
    );
  }
);

Textarea.displayName = 'Textarea';
