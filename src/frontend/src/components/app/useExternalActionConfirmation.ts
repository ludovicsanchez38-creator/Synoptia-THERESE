import { createContext, useCallback, useContext } from 'react';

export interface ExternalActionPreview {
  title: string;
  description: string;
  confirmLabel: string;
  details: Array<{ label: string; value: string }>;
}

export type ExternalAction = () => Promise<void> | void;

export type RequestExternalAction = (
  preview: ExternalActionPreview,
  action: ExternalAction,
) => void;

export const ExternalActionConfirmationContext = createContext<RequestExternalAction | null>(null);

/**
 * Demande une confirmation dans la coque 0.40 lorsqu'un provider est présent.
 * Sans provider, l'action part immédiatement afin de préserver le mode classique.
 */
export function useExternalActionConfirmation(): RequestExternalAction {
  const requestFromPrototype = useContext(ExternalActionConfirmationContext);

  return useCallback<RequestExternalAction>((preview, action) => {
    if (requestFromPrototype) {
      requestFromPrototype(preview, action);
      return;
    }

    void action();
  }, [requestFromPrototype]);
}
