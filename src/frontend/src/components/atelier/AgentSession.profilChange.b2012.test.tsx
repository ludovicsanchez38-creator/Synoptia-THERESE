import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { installLocalStorageStub } from '../../test/localStorage-stub';

const moteur = vi.hoisted(() => ({ consent: vi.fn(), mission: vi.fn() }));

vi.mock('../../services/api/agents', () => ({
  getAgentProfiles: async () => [{ id: 'researcher', name: 'Chercheur', tools: [], default_model: 'openai::test' }],
  getAgentConsent: (...args: unknown[]) => moteur.consent(...args),
  streamAgentSpawn: async function* (...args: unknown[]) { moteur.mission(...args); yield { type: 'done' }; },
}));

import { AgentSession } from './AgentSession';

beforeEach(() => {
  installLocalStorageStub();
  localStorage.setItem('therese:data-profile', '/profil-a');
  moteur.consent.mockReset();
  moteur.mission.mockReset();
});

it('explique un changement de profil pendant la vérification de destination', async () => {
  let terminer!: (destination: unknown) => void;
  moteur.consent.mockReturnValueOnce(new Promise(resolve => { terminer = resolve; }));
  render(<AgentSession model="openai::test" profileId="researcher" onBack={vi.fn()} />);
  fireEvent.change(screen.getByLabelText(/Message à l/), { target: { value: 'Analyse fictive' } });
  fireEvent.click(screen.getByTitle('Envoyer'));
  fireEvent.click(await screen.findByRole('button', { name: "Confirmer l'appel" }));
  await waitFor(() => expect(moteur.consent).toHaveBeenCalled());
  localStorage.setItem('therese:data-profile', '/profil-b');
  terminer({ model: 'openai::test', provider: 'openai', label: 'OpenAI', purposes: [], granted_purposes: [] });

  expect(await screen.findByRole('alert')).toHaveTextContent('Le profil a changé. Reviens au profil concerné avant de réessayer.');
  expect(moteur.mission).not.toHaveBeenCalled();
});
