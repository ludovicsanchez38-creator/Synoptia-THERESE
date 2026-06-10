import { useRef, type ReactNode } from 'react';
import { Z_LAYER } from '../../styles/z-layers';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';

interface DialogShellProps {
  open: boolean;
  onClose: () => void;
  ariaLabel: string;
  children: ReactNode;
  className?: string;
}

export function DialogShell({ open, onClose, ariaLabel, children, className }: DialogShellProps) {
  const dialogRef = useRef<HTMLDivElement>(null);

  // US-013 : focus initial + piège Tab + Escape + restauration du focus,
  // mutualisés dans useDialogFocusTrap (même comportement que les modales
  // artisanales migrées).
  useDialogFocusTrap(dialogRef, { active: open, onEscape: onClose });

  if (!open) return null;

  return (
    <div
      className={`fixed inset-0 ${Z_LAYER.MODAL} flex items-center justify-center`}
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
