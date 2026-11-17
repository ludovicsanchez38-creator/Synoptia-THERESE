import { installLocalStorageStub } from '../../test/localStorage-stub';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { TOOL_READ_DATA_CATEGORY } from '../../lib/consent';

const moteur = vi.hoisted(() => ({
  stream: vi.fn(), request: vi.fn(), documents: true, refuser: false, destinationChangee: false,
  acquitter: undefined as undefined | (() => void),
  decisions: [] as Array<{ purpose: string; provider: string; granted: boolean }>,
}));
// Correctifs 0.83 : AgentSession vide la file par `viderLesAccords` (core) ; seul `request` est doublé.
vi.mock('../../services/api/core', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api/core')>()),
  request: (...args: unknown[]) => moteur.request(...args),
}));
vi.mock('../../services/api/agents', () => ({
  getAgentProfiles: async () => [{ id: 'researcher', name: 'Chercheur', tools: ['read_file'], default_model: 'openai::modele-test' }],
  getAgentConsent: async () => ({ model: 'openai::modele-test', provider: moteur.destinationChangee ? 'anthropic' : 'openai', label: 'OpenAI',
    purposes: moteur.documents ? ['llm', 'documents'] : ['llm'],
    granted_purposes: moteur.decisions.filter(d => d.granted).map(d => d.purpose) }),
  streamAgentSpawn: async function* (...args: unknown[]) {
    moteur.stream(...args);
    yield { type: 'done', content: 'Terminé' };
  },
}));
import { AgentSession } from './AgentSession';

beforeEach(() => {
  installLocalStorageStub();
  localStorage.setItem('therese:data-profile', 'profil-fictif');
  moteur.stream.mockClear();
  moteur.documents = true;
  moteur.refuser = false;
  moteur.destinationChangee = false;
  moteur.decisions = [];
  moteur.acquitter = undefined;
  moteur.request.mockImplementation(async (url: string, options: { body: string }) => {
    expect(url).toBe('/api/consents');
    if (moteur.refuser) throw new Error('Moteur indisponible');
    await new Promise<void>(resolve => { moteur.acquitter = resolve; });
    moteur.decisions.push(JSON.parse(options.body));
  });
});

async function proposer() {
  fireEvent.change(screen.getByLabelText(/Message à l/), { target: { value: 'Analyse fictive' } });
  fireEvent.click(screen.getByTitle('Envoyer'));
  await waitFor(() => expect(screen.getByRole('button', { name: "Confirmer l'appel" })).toBeEnabled());
  fireEvent.click(screen.getByRole('button', { name: "Confirmer l'appel" }));
  return screen.findByTestId('agent-cloud-consent');
}

async function acquitter() {
  await waitFor(() => expect(moteur.acquitter).toBeDefined());
  await act(async () => { const resolve = moteur.acquitter!; moteur.acquitter = undefined; resolve(); });
}

describe('Atelier : accord explicite acquitté avant la mission', () => {
  it.each([false, true])('depuis stockage vierge, puis LLM seul : %s', async (llmSeul) => {
    moteur.documents = !llmSeul;
    const vue = render(<AgentSession model="openai::modele-test" profileId="researcher" onBack={vi.fn()} />);
    if (llmSeul) {
      await proposer();
      fireEvent.click(screen.getByText('Autoriser et envoyer'));
      await acquitter();
      await waitFor(() => expect(moteur.stream).toHaveBeenCalledTimes(1));
      expect(moteur.decisions.map(d => d.purpose)).toEqual(['llm']);
      vue.unmount();
      moteur.documents = true;
      moteur.stream.mockClear();
      render(<AgentSession model="openai::modele-test" profileId="researcher" onBack={vi.fn()} />);
    }
    const dialogue = await proposer();
    expect(dialogue.textContent).toContain('OpenAI');
    expect(dialogue.textContent).toContain('documents');
    expect(dialogue.textContent).toContain(TOOL_READ_DATA_CATEGORY);
    expect(moteur.stream).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText('Autoriser et envoyer'));
    await waitFor(() => expect(moteur.acquitter).toBeDefined());
    expect(moteur.stream).not.toHaveBeenCalled();
    await acquitter();
    if (!llmSeul) {
      expect(moteur.stream).not.toHaveBeenCalled();
      await acquitter();
    }
    await waitFor(() => expect(moteur.stream).toHaveBeenCalledTimes(1));
    expect(moteur.decisions.map(d => [d.purpose, d.provider, d.granted])).toEqual([
      ['llm', 'openai', true], ['documents', 'openai', true],
    ]);
  });

  it('annuler ou ne pas obtenir l’acquittement bloque et explique le refus', async () => {
    render(<AgentSession model="openai::modele-test" profileId="researcher" onBack={vi.fn()} />);
    await proposer();
    fireEvent.click(screen.getByText('Annuler'));
    expect(await screen.findByRole('alert')).toHaveTextContent(/mission.*pas.*démarr/i);
    expect(moteur.stream).not.toHaveBeenCalled();
    await proposer();
    moteur.refuser = true;
    fireEvent.click(screen.getByText('Autoriser et envoyer'));
    expect(await screen.findByRole('alert')).toHaveTextContent(/accord.*enregistr/i);
    expect(moteur.stream).not.toHaveBeenCalled();
  });

  it.each(['annulation', 'profil', 'destination'])('ne démarre pas après %s pendant l’acquittement', async (changement) => {
    moteur.documents = false;
    render(<AgentSession model="openai::modele-test" profileId="researcher" onBack={vi.fn()} />);
    await proposer();
    fireEvent.click(screen.getByText('Autoriser et envoyer'));
    await waitFor(() => expect(moteur.acquitter).toBeDefined());
    if (changement === 'annulation') fireEvent.click(screen.getByText('Annuler'));
    if (changement === 'profil') localStorage.setItem('therese:data-profile', 'autre-profil');
    if (changement === 'destination') moteur.destinationChangee = true;
    await acquitter();
    expect(await screen.findByRole('alert')).toHaveTextContent(/mission.*pas.*démarr/i);
    expect(moteur.stream).not.toHaveBeenCalled();
  });
});
