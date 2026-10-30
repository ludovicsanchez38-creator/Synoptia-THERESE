/**
 * Tour 8 (relecture 7, réserves 2 et 3) : le mini-chat RFC n'utilise pas les
 * fiches mémoire, et une référence supprimée est retirée au lieu de bloquer.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
vi.mock('../../stores/commandsStore', () => ({ useCommandsStore: () => ({createCommand: vi.fn(), updateCommand: vi.fn()}) }));
vi.mock('../../services/api/commands-v3', () => ({generateTemplate: vi.fn()}));
let compteur = 0;
vi.mock('../../services/api', () => ({streamMessage: vi.fn(async function* () {
  compteur += 1;
  yield {type: 'text', content: `Réponse ordinaire ${compteur}`};
  yield {type: 'done', message_id: `message-${compteur}`, conversation_id: `conversation-${compteur}`};
})}));
import { streamMessage } from '../../services/api';
import { generateTemplate } from '../../services/api/commands-v3';
import { RFCWizard } from './RFCWizard';
Element.prototype.scrollTo = vi.fn();
beforeEach(() => {
  vi.clearAllMocks();
  compteur = 0;
  vi.mocked(generateTemplate).mockResolvedValue({name: 'relance', description: '', icon: '', category: 'production', prompt_template: 'Relance {{client}}.'});
});

function envoyer(texte: string, placeholder = 'Décris ta commande idéale...') {
  fireEvent.change(screen.getByPlaceholderText(placeholder), {target: {value: texte}});
  fireEvent.click(screen.getByRole('button', {name: 'Envoyer'}));
}

describe('Tour 8 : mini-chat RFC', () => {
  it('n’utilise jamais les fiches mémoire', async () => {
    render(<RFCWizard onClose={vi.fn()} />);
    envoyer('Je veux une commande de relance client.');
    await screen.findByText('Réponse ordinaire 1');
    expect(vi.mocked(streamMessage).mock.calls[0][0].include_memory).toBe(false);
  });

  it('retire une référence signalée absente et ne la renvoie plus', async () => {
    render(<RFCWizard onClose={vi.fn()} />);
    envoyer('Je veux une commande de relance client.');
    await screen.findByText('Réponse ordinaire 1');
    envoyer('Ajoute le nom du client.');
    await screen.findByText('Réponse ordinaire 2');
    // Le moteur signale que la première réponse a été supprimée entre-temps.
    vi.mocked(streamMessage).mockImplementationOnce(async function* () {
      compteur += 1;
      yield {type: 'text', content: `Réponse ordinaire ${compteur}`};
      yield {type: 'done', message_id: `message-${compteur}`, conversation_id: 'c', rfc_sources_absentes: ['message-1']};
    } as never);
    envoyer('Ajoute le ton.');
    await screen.findByText('Réponse ordinaire 3');
    expect(vi.mocked(streamMessage).mock.calls[2][0].rfc_source_ids).toEqual(['message-1', 'message-2']);
    envoyer('Ajoute la date.');
    await screen.findByText('Réponse ordinaire 4');
    expect(vi.mocked(streamMessage).mock.calls[3][0].rfc_source_ids).toEqual(['message-2', 'message-3']);
    fireEvent.click(screen.getByRole('button', {name: /Passer à Faire/}));
    await waitFor(() => expect(streamMessage).toHaveBeenCalledTimes(5));
    expect(vi.mocked(streamMessage).mock.calls[4][0].rfc_source_ids).toEqual(['message-2', 'message-3', 'message-4']);
  });

  it('retire aussi une référence que la capture signale absente', async () => {
    vi.mocked(generateTemplate).mockResolvedValueOnce({name: 'relance', description: '', icon: '', category: 'production',
      prompt_template: 'Relance {{client}}.', rfc_sources_absentes: ['message-1']} as never);
    render(<RFCWizard onClose={vi.fn()} />);
    envoyer('Je veux une commande de relance client.');
    await screen.findByText('Réponse ordinaire 1');
    fireEvent.click(screen.getByRole('button', {name: /Passer à Faire/}));
    await screen.findByText('Réponse ordinaire 2');
    await waitFor(() => expect(screen.getByRole('button', {name: 'Capturer'})).toBeEnabled());
    fireEvent.click(screen.getByRole('button', {name: 'Capturer'}));
    await screen.findByLabelText('Nom (slug)');
    // Retour à « Faire » : le message relancé ne reprend plus la réponse supprimée.
    fireEvent.click(screen.getByRole('button', {name: 'Annuler'}));
    await waitFor(() => expect(streamMessage).toHaveBeenCalledTimes(3));
    expect(vi.mocked(streamMessage).mock.calls[2][0].rfc_source_ids ?? []).not.toContain('message-1');
    expect(vi.mocked(streamMessage).mock.calls[1][0].rfc_source_ids).toEqual(['message-1']);
  });
});
