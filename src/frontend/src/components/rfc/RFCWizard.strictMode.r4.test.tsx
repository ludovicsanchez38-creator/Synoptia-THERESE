import { StrictMode } from 'react';
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

function attente() {
  let terminer!: () => void;
  const promesse = new Promise<void>((resolve) => { terminer = resolve; });
  return { promesse, terminer };
}

describe('R4-2 : la requête courante garde la capture et son contrôleur sous StrictMode', () => {
  beforeEach(() => {
    vi.mocked(streamMessage).mockReset();
    vi.mocked(generateTemplate).mockReset().mockResolvedValue(commande);
  });

  it.each(['retour', 'annulation', 'erreur'].flatMap((ancienne) =>
    ['complète', 'arrêt', 'démontage'].map((courante) => [ancienne, courante]),
  ))('ancienne requête : %s ; requête courante : %s', async (ancienne, courante) => {
    const premiere = attente();
    const seconde = attente();
    vi.mocked(streamMessage).mockImplementationOnce(async function* () {
      // La première requête se termine après le remontage de StrictMode,
      // même si son signal a déjà été annulé.
      await premiere.promesse;
      if (ancienne === 'annulation') throw new DOMException('Ancienne interruption', 'AbortError');
      if (ancienne === 'erreur') throw new Error('Ancienne erreur');
      yield { type: 'done', content: '', message_id: 'source-obsolete' };
    }).mockImplementationOnce(async function* (_demande, signal) {
      yield { type: 'text', content: 'Proposition courante en cours' };
      await Promise.race([
        seconde.promesse,
        new Promise<void>((resolve) => signal?.addEventListener('abort', () => resolve(), { once: true })),
      ]);
      if (signal?.aborted) throw new DOMException('Interrompu', 'AbortError');
      yield { type: 'done', content: '', message_id: 'source-courante' };
    });

    const vue = render(<StrictMode><RFCWizard onClose={vi.fn()} editCommand={commande} /></StrictMode>);
    try {
      await screen.findByText('Proposition courante en cours');
      expect(streamMessage).toHaveBeenCalledTimes(2);
      const signalCourant = vi.mocked(streamMessage).mock.calls[1][1];
      expect(vi.mocked(streamMessage).mock.calls[0][1]?.aborted).toBe(true);
      expect(signalCourant?.aborted).toBe(false);

      await act(async () => premiere.terminer());
      const capturer = screen.getByRole('button', { name: 'Capturer' });
      expect(capturer).toBeDisabled();
      expect(capturer).toHaveAccessibleDescription(/Attends la fin de la réponse/);
      expect(screen.getByText('Proposition courante en cours')).toBeInTheDocument();
      fireEvent.click(capturer);
      expect(generateTemplate).not.toHaveBeenCalled();
      expect(screen.queryByLabelText('Nom (slug)')).not.toBeInTheDocument();

      if (courante === 'démontage') {
        vue.unmount();
        expect(signalCourant?.aborted).toBe(true);
        return;
      }
      if (courante === 'arrêt') {
        fireEvent.click(screen.getByRole('button', { name: 'Arrêter la réponse' }));
        expect(signalCourant?.aborted).toBe(true);
        await screen.findByText(/Réponse non conservée/);
      } else {
        await act(async () => seconde.terminer());
      }
      await waitFor(() => expect(screen.getByRole('button', { name: 'Capturer' })).toBeEnabled());
      expect(screen.getByText('Proposition courante en cours')).toBeInTheDocument();
      fireEvent.click(screen.getByRole('button', { name: 'Capturer' }));
      await screen.findByLabelText('Nom (slug)');
      if (courante === 'complète') {
        expect(generateTemplate).toHaveBeenCalledExactlyOnceWith({
          brief: 'Crée une commande à partir de ces échanges.',
          rfc_source_ids: ['source-courante'],
        });
      } else {
        expect(generateTemplate).not.toHaveBeenCalled();
      }
    } finally {
      vue.unmount();
      await act(async () => { premiere.terminer(); seconde.terminer(); });
    }
  });
});
