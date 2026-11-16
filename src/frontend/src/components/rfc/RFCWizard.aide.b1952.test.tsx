import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
vi.mock('../../stores/commandsStore', () => ({
  useCommandsStore: () => ({ createCommand: vi.fn(), updateCommand: vi.fn() }),
}));
vi.mock('../../services/api/commands-v3', () => ({ generateTemplate: vi.fn() }));
vi.mock('../../services/api', () => ({ streamMessage: vi.fn() }));
import { streamMessage } from '../../services/api';
import { RFCWizard } from './RFCWizard';
Element.prototype.scrollTo = vi.fn();

function envoyer() {
  fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'Crée une commande' } });
  fireEvent.click(screen.getByRole('button', { name: 'Envoyer' }));
}

describe('B-1952 : l’aide décrit la condition réelle du passage à Faire', () => {
  beforeEach(() => vi.clearAllMocks());

  it('explique dès le départ qu’une réponse complète est nécessaire', () => {
    render(<RFCWizard onClose={vi.fn()} />);
    expect(screen.getByRole('button', { name: /Passer à Faire/ })).toHaveAccessibleDescription(/réponse complète/);
  });

  it('garde cette explication pendant la réponse puis permet de continuer', async () => {
    let terminer!: () => void;
    const attente = new Promise<void>((resolve) => { terminer = resolve; });
    vi.mocked(streamMessage).mockImplementation(async function* () {
      await attente;
      yield { type: 'text', content: 'Une commande complète' };
      yield { type: 'done', content: '', message_id: 'reponse-verifiee' };
    });
    render(<RFCWizard onClose={vi.fn()} />);
    envoyer();
    const suite = screen.getByRole('button', { name: /Passer à Faire/ });
    try {
      expect(suite).toBeDisabled();
      expect(suite).toHaveAccessibleDescription(/réponse complète/);
    } finally {
      await act(async () => terminer());
    }
    await waitFor(() => expect(suite).toBeEnabled());
    expect(suite).not.toHaveAttribute('aria-describedby');
  });

  it('explique encore le blocage après une réponse interrompue et invite à renvoyer', async () => {
    vi.mocked(streamMessage).mockImplementation(async function* () {
      yield { type: 'text', content: 'Une réponse interrompue' };
    });
    render(<RFCWizard onClose={vi.fn()} />);
    envoyer();
    await screen.findByText(/Réponse non conservée/);
    const suite = screen.getByRole('button', { name: /Passer à Faire/ });
    expect(suite).toHaveAccessibleDescription(/réponse complète.*Renvoie ton message/);
    fireEvent.click(suite);
    expect(await screen.findByRole('alert')).toHaveTextContent('Aucune réponse complète');
  });

  it.each([false, true])('R1-8 : explique le flux en cours sans redemander le brief (renvoi=%s)', async (renvoi) => {
    vi.mocked(streamMessage).mockReset();
    if (renvoi) {
      vi.mocked(streamMessage).mockImplementationOnce(async function* () {
        yield { type: 'text', content: 'Réponse interrompue' };
      });
    }
    let terminer!: () => void;
    const attente = new Promise<void>((resolve) => { terminer = resolve; });
    vi.mocked(streamMessage).mockImplementationOnce(async function* () {
      await attente;
      yield { type: 'text', content: 'Réponse complète' };
      yield { type: 'done', content: '', message_id: 'source' };
    });
    render(<RFCWizard onClose={vi.fn()} />);
    if (renvoi) {
      envoyer();
      await screen.findByText(/Réponse non conservée/);
      await waitFor(() => expect(screen.getByRole('button', { name: /Passer à Faire/ })).toHaveAccessibleDescription(/Renvoie ton message/));
    }
    envoyer();
    try {
      const suite = screen.getByRole('button', { name: /Passer à Faire/ });
      expect(suite).toHaveAccessibleDescription(/^THÉRÈSE répond/);
      expect(suite).not.toHaveAccessibleDescription(/Envoie|Renvoie/);
      expect(suite).toHaveAccessibleDescription(/réponse complète/);
    } finally {
      await act(async () => terminer());
    }
    expect(screen.getByRole('button', { name: /Passer à Faire/ })).not.toHaveAttribute('aria-describedby');
  });
});
