import { useState } from 'react';
import { RefreshCw } from 'lucide-react';

import {
  INTERFACE_MODE_STORAGE_KEY,
  type InterfaceMode,
} from '../../lib/interfaceMode';
import { Button } from '../ui/Button';

interface InterfaceBetaToggleProps {
  onReload?: () => void;
}

function isConversationCanvasStored(): boolean {
  try {
    return window.localStorage.getItem(INTERFACE_MODE_STORAGE_KEY) === 'conversation-canvas';
  } catch {
    return false;
  }
}

export function InterfaceBetaToggle({
  onReload = () => window.location.reload(),
}: InterfaceBetaToggleProps) {
  const [enabled, setEnabled] = useState(isConversationCanvasStored);
  const [reloadSuggested, setReloadSuggested] = useState(false);
  const [storageError, setStorageError] = useState(false);

  function handleToggle(nextEnabled: boolean) {
    const nextMode: InterfaceMode = nextEnabled ? 'conversation-canvas' : 'classic';

    try {
      window.localStorage.setItem(INTERFACE_MODE_STORAGE_KEY, nextMode);
      setEnabled(nextEnabled);
      setReloadSuggested(true);
      setStorageError(false);
    } catch {
      setStorageError(true);
    }
  }

  return (
    <div className="bg-surface/50 rounded-lg p-5 border border-border/30">
      <div className="flex items-center justify-between gap-4">
        <div>
          <label htmlFor="interface-beta-toggle" className="text-sm font-medium text-text cursor-pointer">
            Essayer la nouvelle interface (bêta)
          </label>
          <p className="text-xs text-text-muted mt-1">
            Le mode classique reste sélectionné par défaut.
          </p>
        </div>
        <button
          id="interface-beta-toggle"
          type="button"
          role="switch"
          aria-checked={enabled}
          onClick={() => handleToggle(!enabled)}
          className={`relative w-11 h-6 shrink-0 rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan focus-visible:ring-offset-2 focus-visible:ring-offset-background ${
            enabled ? 'bg-accent-cyan' : 'bg-border'
          }`}
          data-testid="interface-beta-toggle"
        >
          <span
            className={`absolute top-1 left-0 h-4 w-4 rounded-full bg-white shadow-sm transition-transform ${
              enabled ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </div>

      {reloadSuggested && (
        <div className="mt-4 flex items-center justify-between gap-3 rounded-md border border-accent-cyan/30 bg-accent-cyan/10 px-3 py-2">
          <p className="text-xs text-text-muted">
            Recharge THÉRÈSE pour appliquer ce choix.
          </p>
          <Button variant="secondary" size="sm" onClick={onReload} className="shrink-0">
            <RefreshCw className="w-3.5 h-3.5 mr-2" />
            Recharger maintenant
          </Button>
        </div>
      )}

      {storageError && (
        <p role="alert" className="mt-3 text-xs text-red-400">
          Impossible d'enregistrer ce choix sur cet appareil.
        </p>
      )}
    </div>
  );
}
