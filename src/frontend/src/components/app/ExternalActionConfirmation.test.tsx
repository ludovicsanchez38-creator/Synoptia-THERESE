import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import {
  PrototypeExternalActionConfirmationProvider,
} from './ExternalActionConfirmation';
import { useExternalActionConfirmation } from './useExternalActionConfirmation';

const preview = {
  title: 'Confirmer l’action externe',
  description: 'Vérifie cet aperçu avant de continuer.',
  confirmLabel: 'Confirmer maintenant',
  details: [{ label: 'Destination', value: 'service@example.fr' }],
};

function Trigger({ action }: { action: () => Promise<void> | void }) {
  const request = useExternalActionConfirmation();
  return <button type="button" onClick={() => request(preview, action)}>Préparer</button>;
}

describe('PrototypeExternalActionConfirmationProvider', () => {
  it('préserve l’exécution directe hors de la coque prototype', () => {
    const action = vi.fn();
    render(<Trigger action={action} />);

    fireEvent.click(screen.getByRole('button', { name: 'Préparer' }));

    expect(action).toHaveBeenCalledTimes(1);
    expect(screen.queryByTestId('external-action-confirmation')).not.toBeInTheDocument();
  });

  it('affiche l’aperçu, permet d’annuler et bloque tout effet avant confirmation', () => {
    const action = vi.fn();
    render(
      <PrototypeExternalActionConfirmationProvider>
        <Trigger action={action} />
      </PrototypeExternalActionConfirmationProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Préparer' }));

    expect(screen.getByTestId('external-action-confirmation')).toHaveTextContent('Aperçu avant action');
    expect(screen.getByText('service@example.fr')).toBeInTheDocument();
    expect(action).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));

    expect(screen.queryByTestId('external-action-confirmation')).not.toBeInTheDocument();
    expect(action).not.toHaveBeenCalled();
  });

  it('n’exécute qu’une fois après confirmation, même en cas de double clic', async () => {
    let resolveAction: (() => void) | undefined;
    const action = vi.fn(() => new Promise<void>((resolve) => {
      resolveAction = resolve;
    }));
    render(
      <PrototypeExternalActionConfirmationProvider>
        <Trigger action={action} />
      </PrototypeExternalActionConfirmationProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Préparer' }));
    const confirm = screen.getByRole('button', { name: 'Confirmer maintenant' });
    fireEvent.click(confirm);
    fireEvent.click(confirm);

    expect(action).toHaveBeenCalledTimes(1);
    resolveAction?.();
    await waitFor(() => {
      expect(screen.queryByTestId('external-action-confirmation')).not.toBeInTheDocument();
    });
  });
});
