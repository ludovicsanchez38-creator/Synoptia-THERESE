/**
 * Tour 7 (relecture 6, constat 2) : une réponse refusée ou interrompue ne
 * bloque plus le mini-chat RFC et n'est jamais reprise. Vrais composants
 * RFCWizard et RFCChat, API simulée.
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

describe('Tour 7 : reprise après un premier échange raté', () => {
  it.each([
    ['refus du moteur', async function* () { yield {type: 'error', content: 'Ton accord « llm » pour openai est nécessaire.'}; }],
    ['réponse interrompue', async function* () { yield {type: 'text', content: 'Réponse coupée'}; }],
    ['accord des fiches demandé', async function* () { yield {type: 'memory_consent_required', content: 'Une fiche mémoire ancienne sert à cet échange.'}; }],
  ])('%s puis renvoi réussi : on passe à Faire sans reprendre l’échange raté', async (_cas, premier) => {
    vi.mocked(streamMessage).mockImplementationOnce(premier as never);
    render(<RFCWizard onClose={vi.fn()} />);
    envoyer('Je veux une commande de relance client.');
    await waitFor(() => expect(streamMessage).toHaveBeenCalledTimes(1));
    expect(await screen.findByText(/Réponse non conservée/)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('button', {name: 'Envoyer'})).toBeInTheDocument());
    envoyer('Je veux une commande de relance client.');
    await screen.findByText('Réponse ordinaire 1');
    // Aucune référence vide : sans réponse vérifiée, le message part seul.
    expect(vi.mocked(streamMessage).mock.calls[1][0].rfc_source_ids).toBeUndefined();
    envoyer('Ajoute une variable pour le nom du client.');
    await screen.findByText('Réponse ordinaire 2');
    expect(vi.mocked(streamMessage).mock.calls[2][0].rfc_source_ids).toEqual(['message-1']);
    fireEvent.click(screen.getByRole('button', {name: /Passer à Faire/}));
    await waitFor(() => expect(screen.queryByPlaceholderText('Décris ta commande idéale...')).toBeNull());
    await waitFor(() => expect(streamMessage).toHaveBeenCalledTimes(4));
    expect(vi.mocked(streamMessage).mock.calls[3][0].rfc_source_ids).toEqual(['message-1', 'message-2']);
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('une réponse interrompue en « Faire » n’empêche pas la capture et n’est pas reprise', async () => {
    render(<RFCWizard onClose={vi.fn()} />);
    envoyer('Je veux une commande de relance client.');
    await screen.findByText('Réponse ordinaire 1');
    fireEvent.click(screen.getByRole('button', {name: /Passer à Faire/}));
    await screen.findByText('Réponse ordinaire 2');
    vi.mocked(streamMessage).mockImplementationOnce(async function* () { yield {type: 'text', content: 'Réponse coupée'}; } as never);
    envoyer('Ajoute le ton.', 'Itère sur le template...');
    expect(await screen.findByText(/Réponse non conservée/)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('button', {name: 'Capturer'})).toBeEnabled());
    fireEvent.click(screen.getByRole('button', {name: 'Capturer'}));
    await waitFor(() => expect(generateTemplate).toHaveBeenCalledTimes(1));
    expect(vi.mocked(generateTemplate).mock.calls[0][0].rfc_source_ids).toEqual(['message-1', 'message-2']);
    expect(await screen.findByLabelText('Nom (slug)')).toHaveValue('relance');
  });

  it('sans aucune réponse vérifiée, « Capturer » ouvre le formulaire à remplir à la main', async () => {
    vi.mocked(streamMessage).mockImplementation(async function* () { yield {type: 'text', content: 'Réponse coupée'}; } as never);
    render(<RFCWizard onClose={vi.fn()} editCommand={{id: 'user-relance', name: 'relance', description: '', icon: '', category: 'production', prompt_template: 'Relance {{client}}.'}} />);
    await waitFor(() => expect(streamMessage).toHaveBeenCalledTimes(1));
    // Le mode modification ne pose aucune référence vide.
    expect(vi.mocked(streamMessage).mock.calls[0][0].rfc_source_ids).toBeUndefined();
    await waitFor(() => expect(screen.getByRole('button', {name: 'Capturer'})).toBeEnabled());
    fireEvent.click(screen.getByRole('button', {name: 'Capturer'}));
    expect(await screen.findByRole('alert')).toHaveTextContent('remplis la commande à la main');
    expect(await screen.findByLabelText('Nom (slug)')).toBeInTheDocument();
    expect(generateTemplate).not.toHaveBeenCalled();
  });
});
