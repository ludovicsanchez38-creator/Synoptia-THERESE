import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../stores/commandsStore', () => ({
  useCommandsStore: () => ({ createCommand: vi.fn(), updateCommand: vi.fn() }),
}));
vi.mock('../../services/api/commands-v3', () => ({ generateTemplate: vi.fn() }));
vi.mock('../../services/api', () => ({ streamMessage: vi.fn() }));
import { streamMessage } from '../../services/api';
import { generateTemplate } from '../../services/api/commands-v3';
import { RFCWizard } from './RFCWizard';

Element.prototype.scrollTo = vi.fn();
const commande = { id: 'relance', name: 'relance', description: '', icon: '', category: 'production', prompt_template: 'Relance {{client}}.' };

describe('R1-4 : capturer attend chaque réponse du vrai mini-chat', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(streamMessage).mockReset();
    vi.mocked(generateTemplate).mockResolvedValue(commande);
    vi.mocked(streamMessage).mockImplementationOnce(async function* () {
      yield { type: 'text', content: 'Première proposition' };
      yield { type: 'done', content: '', message_id: 'source-1' };
    });
  });

  it.each(['complète', 'interrompue'])('deuxième réponse %s : attend sa fin puis reprend seulement les sources vérifiées', async (fin) => {
    let terminer!: () => void;
    const attente = new Promise<void>((resolve) => { terminer = resolve; });
    vi.mocked(streamMessage).mockImplementationOnce(async function* (_demande, signal) {
      yield { type: 'text', content: 'Deuxième proposition en cours' };
      await Promise.race([attente, new Promise<void>((resolve) => signal?.addEventListener('abort', () => resolve(), { once: true }))]);
      if (signal?.aborted) throw new DOMException('Interrompu', 'AbortError');
      yield { type: 'done', content: '', message_id: 'source-2' };
    });
    render(<RFCWizard onClose={vi.fn()} editCommand={commande} />);
    await waitFor(() => expect(screen.getByRole('button', { name: 'Capturer' })).toBeEnabled());
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'Ajoute la date' } });
    fireEvent.click(screen.getByRole('button', { name: 'Envoyer' }));
    await screen.findByText('Deuxième proposition en cours');
    try {
      const capturer = screen.getByRole('button', { name: 'Capturer' });
      expect(capturer).toBeDisabled();
      expect(capturer).toHaveAccessibleDescription(/Attends la fin de la réponse/);
      fireEvent.click(capturer);
      expect(generateTemplate).not.toHaveBeenCalled();
      if (fin === 'interrompue') {
        fireEvent.click(screen.getByRole('button', { name: 'Arrêter la réponse' }));
        await screen.findByText(/Réponse non conservée/);
      }
    } finally {
      await act(async () => terminer());
    }
    await waitFor(() => expect(screen.getByRole('button', { name: 'Capturer' })).toBeEnabled());
    fireEvent.click(screen.getByRole('button', { name: 'Capturer' }));
    await screen.findByLabelText('Nom (slug)');
    expect(generateTemplate).toHaveBeenCalledExactlyOnceWith({
      brief: 'Crée une commande à partir de ces échanges.',
      rfc_source_ids: fin === 'complète' ? ['source-1', 'source-2'] : ['source-1'],
    });
  });

  it.each(['complète', 'interrompue'])('R2-2 : deuxième réponse de Réfléchir %s : attend avant de passer les sources à Faire', async (fin) => {
    let terminer!: () => void;
    let signalEnCours: AbortSignal | undefined;
    const attente = new Promise<void>((resolve) => { terminer = resolve; });
    vi.mocked(streamMessage).mockImplementationOnce(async function* (_demande, signal) {
      signalEnCours = signal;
      yield { type: 'text', content: 'Deuxième réflexion en cours' };
      await Promise.race([attente, new Promise<void>((resolve) => signal?.addEventListener('abort', () => resolve(), { once: true }))]);
      if (signal?.aborted) throw new DOMException('Interrompu', 'AbortError');
      yield { type: 'done', content: '', message_id: 'source-2' };
    }).mockImplementationOnce(async function* () {
      yield { type: 'text', content: 'Ébauche de commande' };
      yield { type: 'done', content: '', message_id: 'source-faire' };
    });
    render(<RFCWizard onClose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'Prépare une relance' } });
    fireEvent.click(screen.getByRole('button', { name: 'Envoyer' }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Passer à Faire' })).toBeEnabled());
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'Ajoute la date' } });
    fireEvent.click(screen.getByRole('button', { name: 'Envoyer' }));
    await screen.findByText('Deuxième réflexion en cours');
    try {
      const suite = screen.getByRole('button', { name: 'Passer à Faire' });
      expect(suite).toBeDisabled();
      expect(suite).toHaveAccessibleDescription(/^THÉRÈSE répond.*réponse complète/);
      fireEvent.click(suite);
      expect(signalEnCours?.aborted).toBe(false);
      expect(streamMessage).toHaveBeenCalledTimes(2);
      expect(screen.getByPlaceholderText('Décris ta commande idéale...')).toBeInTheDocument();
      if (fin === 'interrompue') {
        fireEvent.click(screen.getByRole('button', { name: 'Arrêter la réponse' }));
        await screen.findByText(/Réponse non conservée/);
      }
    } finally {
      await act(async () => terminer());
    }
    await waitFor(() => expect(screen.getByRole('button', { name: 'Passer à Faire' })).toBeEnabled());
    fireEvent.click(screen.getByRole('button', { name: 'Passer à Faire' }));
    await screen.findByText('Ébauche de commande');
    expect(streamMessage).toHaveBeenCalledTimes(3);
    expect(vi.mocked(streamMessage).mock.calls[1][0].rfc_source_ids).toEqual(['source-1']);
    expect(vi.mocked(streamMessage).mock.calls[2][0].rfc_source_ids)
      .toEqual(fin === 'complète' ? ['source-1', 'source-2'] : ['source-1']);
  });
});
