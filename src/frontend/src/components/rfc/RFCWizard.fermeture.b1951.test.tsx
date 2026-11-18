import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
vi.mock('../../stores/commandsStore', () => ({
  useCommandsStore: () => ({ createCommand: vi.fn(), updateCommand: vi.fn() }),
}));
vi.mock('../../services/api/commands-v3', () => ({ generateTemplate: vi.fn() }));
vi.mock('./RFCChat', () => ({ RFCChat: () => null }));
import { RFCWizard } from './RFCWizard';

describe('B-1951 : fermeture accessible de l’assistant', () => {
  it('permet de trouver la fermeture par son nom puis de fermer', () => {
    const fermer = vi.fn();
    render(<RFCWizard onClose={fermer} />);
    fireEvent.click(screen.getByRole('button', { name: 'Fermer l’assistant de commande' }));
    expect(fermer).toHaveBeenCalledTimes(1);
  });
});
