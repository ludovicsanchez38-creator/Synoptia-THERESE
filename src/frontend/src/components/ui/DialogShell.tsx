import { useEffect, useRef, type ReactNode } from 'react';

interface DialogShellProps {
  open: boolean;
  onClose: () => void;
  ariaLabel: string;
  children: ReactNode;
  className?: string;
}

export function DialogShell({ open, onClose, ariaLabel, children, className }: DialogShellProps) {
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    const dialog = dialogRef.current;
    if (!dialog) return;

    // Focus le dialog a l'ouverture
    const firstFocusable = dialog.querySelector<HTMLElement>(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"]):not([disabled])'
    );
    firstFocusable?.focus();

    // Focus trap
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        onClose();
        return;
      }
      if (e.key !== 'Tab') return;

      const focusables = dialog!.querySelectorAll<HTMLElement>(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"]):not([disabled])'
      );
      if (focusables.length === 0) return;

      const first = focusables[0];
      const last = focusables[focusables.length - 1];

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" aria-hidden="true" />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label={ariaLabel}
        className={`relative z-10 ${className ?? ''}`}
      >
        {children}
      </div>
    </div>
  );
}
