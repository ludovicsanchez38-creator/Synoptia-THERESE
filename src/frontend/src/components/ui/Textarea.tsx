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
          // Auto resize
          autoResize ? 'resize-none overflow-hidden' : 'resize-y',
          className
        )}
        {...props}
      />
    );
  }
);

Textarea.displayName = 'Textarea';
