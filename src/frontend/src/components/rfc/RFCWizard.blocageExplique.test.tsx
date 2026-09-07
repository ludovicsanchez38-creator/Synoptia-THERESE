/**
 * B-636 (persona Sophie, c4) : « Passer à Faire » restait désactivé sans
 * dire qu'il faut d'abord envoyer le brief à THÉRÈSE.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../stores/commandsStore', () => ({
  useCommandsStore: () => ({ createCommand: vi.fn(), updateCommand: vi.fn() }),
}));
vi.mock('../../services/api/commands-v3', () => ({ generateTemplate: vi.fn() }));
vi.mock('./RFCChat', () => ({
  RFCChat: ({ onConversationUpdate }: { onConversationUpdate: (m: unknown[]) => void }) => (
    <button
      type="button"
      onClick={() => onConversationUpdate([{ id: 'm1', role: 'user', content: 'Un brief' }])}
    >
      Envoyer un brief factice
    </button>
  ),
}));

import { RFCWizard } from './RFCWizard';

describe('B-636 : le blocage de « Passer à Faire » est expliqué', () => {
  it('sans brief envoyé, le bouton est désactivé et une aide visible dit pourquoi', () => {
    render(<RFCWizard onClose={vi.fn()} />);
    const bouton = screen.getByRole('button', { name: /Passer à Faire/ });
    expect(bouton).toBeDisabled();

    const idAide = bouton.getAttribute('aria-describedby');
    expect(idAide).toBeTruthy();
    const aide = document.getElementById(idAide as string);
    expect(aide).not.toBeNull();
    expect(aide).toHaveTextContent(/Envoie d’abord|Envoie d'abord/);
    // framer-motion pose opacity:0 au montage dans jsdom : on vérifie que rien ne le masque volontairement.
    expect(aide).not.toHaveAttribute('hidden');
    expect(aide).not.toHaveAttribute('aria-hidden');
  });

  it('une fois le brief envoyé, le bouton s’active et l’aide disparaît', () => {
    render(<RFCWizard onClose={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /Envoyer un brief factice/ }));

    const bouton = screen.getByRole('button', { name: /Passer à Faire/ });
    expect(bouton).toBeEnabled();
    expect(screen.queryByText(/Envoie d’abord|Envoie d'abord/)).toBeNull();
  });
});
