/**
 * Cycle 6, lecteur D58 (ExternalActionConfirmation.tsx) : `confirm()` faisait
 * try/finally sans catch et le bouton appelait `void confirm()` : si l'effet
 * externe échouait, la carte se fermait quand même et le rejet partait en
 * promesse non gérée, sans message.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { PrototypeExternalActionConfirmationProvider } from './ExternalActionConfirmation';
import { useExternalActionConfirmation } from './useExternalActionConfirmation';

const preview = {
  title: 'Envoyer le devis', description: 'Vérifie.', confirmLabel: 'Envoyer maintenant',
  details: [{ label: 'Destination', value: 'client@example.fr' }],
};
function Trigger({ action }: { action: () => Promise<void> }) {
  const request = useExternalActionConfirmation();
  return <button type="button" onClick={() => request(preview, action)}>Préparer</button>;
}

describe('D58 : un effet externe qui échoue reste à l’écran', () => {
  it('la carte reste ouverte avec la cause, et Annuler la ferme', async () => {
    const action = vi.fn().mockRejectedValue(new Error('Le serveur SMTP refuse la connexion'));
    render(
      <PrototypeExternalActionConfirmationProvider>
        <Trigger action={action} />
      </PrototypeExternalActionConfirmationProvider>,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Préparer' }));
    fireEvent.click(screen.getByRole('button', { name: 'Envoyer maintenant' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/SMTP refuse/);
    expect(screen.getByTestId('external-action-confirmation')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Envoyer maintenant' })).toBeEnabled();

    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));
    expect(screen.queryByTestId('external-action-confirmation')).not.toBeInTheDocument();
  });
});
