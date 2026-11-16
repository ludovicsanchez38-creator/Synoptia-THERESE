import { act, fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
vi.mock('../../stores/commandsStore', () => ({
  useCommandsStore: () => ({ createCommand: vi.fn(), updateCommand: vi.fn() }),
}));
vi.mock('../../services/api/commands-v3', () => ({ generateTemplate: vi.fn() }));
vi.mock('./RFCChat', () => ({
  RFCChat: ({ onConversationUpdate }: { onConversationUpdate: (m: unknown[]) => void }) => (
    <button onClick={() => onConversationUpdate([
      { id: 'reponse', role: 'assistant', content: 'Une commande', sourceId: 'source' },
    ])}>Terminer la réponse</button>
  ),
}));
import { generateTemplate } from '../../services/api/commands-v3';
import { RFCWizard } from './RFCWizard';

const commande = { id: 'relance', name: 'relance', description: '', icon: '', category: 'production', prompt_template: 'Relance {{client}}.' };

describe('B-1953 : la capture désactivée est expliquée', () => {
  it('indique qu’il faut attendre la réponse avant de capturer', () => {
    render(<RFCWizard onClose={vi.fn()} editCommand={commande} />);
    const capturer = screen.getByRole('button', { name: 'Capturer' });
    expect(capturer).toBeDisabled();
    expect(capturer).toHaveAccessibleDescription(/Attends la fin de la réponse/);
  });

  it('annonce la préparation de la commande pendant la génération', async () => {
    let terminer!: (v: typeof commande) => void;
    vi.mocked(generateTemplate).mockImplementation(() => new Promise((resolve) => { terminer = resolve; }));
    render(<RFCWizard onClose={vi.fn()} editCommand={commande} />);
    fireEvent.click(screen.getByRole('button', { name: 'Terminer la réponse' }));
    const capturer = screen.getByRole('button', { name: 'Capturer' });
    expect(capturer).toBeEnabled();
    expect(capturer).not.toHaveAttribute('aria-describedby');
    fireEvent.click(capturer);
    try {
      expect(screen.getByRole('button', { name: 'Génération...' })).toBeDisabled();
      expect(screen.getByRole('button', { name: 'Génération...' })).toHaveAccessibleDescription(/THÉRÈSE prépare ta commande/);
      expect(screen.getByRole('status')).toHaveTextContent('THÉRÈSE prépare ta commande');
    } finally {
      await act(async () => terminer(commande));
    }
    expect(await screen.findByLabelText('Nom (slug)')).toHaveValue('relance');
  });
});
