import { useRef, useState } from 'react';

import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import {
  hasExplicitInterfaceModeChoice,
  INTERFACE_MODE_STORAGE_KEY,
} from '../../lib/interfaceMode';
import { Z_LAYER } from '../../styles/z-layers';
import { Button } from '../ui/Button';

export const NEW_INTERFACE_INTRO_STORAGE_KEY = 'therese-040-intro-seen';

function shouldShowIntro(): boolean {
  try {
    const introSeen = window.localStorage.getItem(NEW_INTERFACE_INTRO_STORAGE_KEY) === 'true';
    const storedMode = window.localStorage.getItem(INTERFACE_MODE_STORAGE_KEY);
    return !introSeen && !hasExplicitInterfaceModeChoice(storedMode);
  } catch {
    // Sans stockage persistant, la promesse « une seule fois » ne peut pas être
    // tenue. On évite donc de présenter le dialogue à chaque lancement.
    return false;
  }
}

export function NewInterfaceIntro() {
  const [isOpen, setIsOpen] = useState(shouldShowIntro);
  const dialogRef = useRef<HTMLDivElement>(null);

  function dismiss() {
    try {
      window.localStorage.setItem(NEW_INTERFACE_INTRO_STORAGE_KEY, 'true');
    } catch {
      // Le dialogue reste fermable même si le stockage devient indisponible.
    }
    setIsOpen(false);
  }

  useDialogFocusTrap(dialogRef, {
    active: isOpen,
    onEscape: dismiss,
    isolateBackground: true,
  });

  if (!isOpen) return null;

  return (
    <div className={`fixed inset-0 ${Z_LAYER.WIZARD} flex items-center justify-center p-4`}>
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        data-dialog-backdrop
        aria-hidden="true"
      />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="new-interface-intro-title"
        className="relative w-full max-w-md rounded-xl border border-border bg-surface p-6 text-text shadow-2xl"
      >
        <h2
          id="new-interface-intro-title"
          tabIndex={-1}
          data-dialog-autofocus
          className="text-xl font-semibold"
        >
          La nouvelle interface est active
        </h2>
        <p className="mt-3 text-sm leading-6 text-text-muted">
          Tu peux revenir à l’ancienne à tout moment dans Paramètres → À propos,
          avec l’interrupteur « Essayer la nouvelle interface ».
        </p>
        <div className="mt-6 flex justify-end">
          <Button type="button" onClick={dismiss}>
            J’ai compris
          </Button>
        </div>
      </div>
    </div>
  );
}
