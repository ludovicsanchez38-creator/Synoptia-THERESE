import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
vi.mock('../../stores/commandsStore', () => ({ useCommandsStore: () => ({createCommand: vi.fn(), updateCommand: vi.fn()}) }));
vi.mock('../../services/api/commands-v3', () => ({generateTemplate: vi.fn().mockResolvedValue({name:'devis',prompt_template:'Prépare un devis.'})}));
vi.mock('../../services/api', () => ({streamMessage: vi.fn(async function* () {
  yield {type:'text',content:'Citation du contrat : REFERENCE_CONTRAT_AMBRE'};
  yield {type:'done',message_id:'message-documentaire-en-base',conversation_id:'conversation-rfc'};
})}));
import { streamMessage } from '../../services/api';
import { generateTemplate } from '../../services/api/commands-v3';
import { RFCWizard } from './RFCWizard';
Element.prototype.scrollTo = vi.fn();
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(generateTemplate).mockResolvedValue({name: 'devis', description: '', icon: '', category: 'production', prompt_template: 'Prépare un devis.'});
});
async function reflechir() {
  render(<RFCWizard onClose={vi.fn()} />);
  fireEvent.change(screen.getByPlaceholderText('Décris ta commande idéale...'), {target: {value: 'Utilise mon contrat.'}});
  fireEvent.click(screen.getByRole('button', {name: 'Envoyer'}));
  await waitFor(() => expect(screen.getByRole('button', {name: /Passer à Faire/})).toBeEnabled());
}
describe('Tour 6 : provenance du mini-chat RFC', () => {
  it('les deux transitions gardent les références serveur et ne recopient pas le texte', async () => {
    render(<RFCWizard onClose={vi.fn()} />);
    fireEvent.change(screen.getByPlaceholderText('Décris ta commande idéale...'), {target:{value:'Utilise mon contrat pour créer une commande.'}});
    fireEvent.click(screen.getByRole('button',{name:'Envoyer'}));
    await waitFor(() => expect(screen.getByRole('button',{name:/Passer à Faire/})).toBeEnabled());
    fireEvent.click(screen.getByRole('button',{name:/Passer à Faire/}));
    await waitFor(() => expect(streamMessage).toHaveBeenCalledTimes(2));
    const reprise=vi.mocked(streamMessage).mock.calls[1][0];
    expect(reprise.message).not.toContain('REFERENCE_CONTRAT_AMBRE');
    expect(reprise.rfc_source_ids).toEqual(['message-documentaire-en-base']);
    await waitFor(() => expect(screen.getByRole('button',{name:'Capturer'})).toBeEnabled());
    fireEvent.click(screen.getByRole('button',{name:'Capturer'}));
    await waitFor(() => expect(generateTemplate).toHaveBeenCalledTimes(1));
    const demande=vi.mocked(generateTemplate).mock.calls[0][0];
    expect(demande.brief).not.toContain('REFERENCE_CONTRAT_AMBRE');
    expect(demande.context).toBeUndefined();
    expect(demande.rfc_source_ids).toEqual(['message-documentaire-en-base']);
  });
});

it('explique une réponse incomplète et bloque la transition', async () => {
  vi.mocked(streamMessage).mockImplementationOnce(async function* () {
    yield {type: 'text', content: 'Réponse documentaire interrompue'};
  });
  await reflechir();
  fireEvent.click(screen.getByRole('button', {name: /Passer à Faire/}));
  expect(await screen.findByRole('alert')).toHaveTextContent('Renvoie ton message');
  expect(streamMessage).toHaveBeenCalledTimes(1);
});

it('affiche le refus français de la capture et garde la conversation', async () => {
  vi.mocked(generateTemplate).mockRejectedValueOnce(new Error('Ton accord documents pour Mistral est nécessaire.'));
  await reflechir();
  fireEvent.click(screen.getByRole('button', {name: /Passer à Faire/}));
  await waitFor(() => expect(screen.getByRole('button', {name: 'Capturer'})).toBeEnabled());
  fireEvent.click(screen.getByRole('button', {name: 'Capturer'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('Ton accord documents pour Mistral');
  expect(screen.getByPlaceholderText('Itère sur le template...')).toBeInTheDocument();
});

it('affiche le refus du moteur dans le mini-chat', async () => {
  vi.mocked(streamMessage).mockImplementationOnce(async function* () {
    yield {type: 'error', content: 'Ton accord documents pour OpenAI est nécessaire.'};
  });
  render(<RFCWizard onClose={vi.fn()} />);
  fireEvent.change(screen.getByPlaceholderText('Décris ta commande idéale...'), {target: {value: 'Fictif'}});
  fireEvent.click(screen.getByRole('button', {name: 'Envoyer'}));
  expect(await screen.findByText('Ton accord documents pour OpenAI est nécessaire.')).toBeInTheDocument();
});
