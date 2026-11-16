import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { installLocalStorageStub } from '../../test/localStorage-stub';
import { AccordNonEnregistre } from '../../services/api/core';

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

it('affiche le refus du moteur pendant la vérification de destination', async () => {
  const message = 'Le profil a changé. Reviens au profil concerné avant de réessayer.';
  moteur.consent.mockRejectedValueOnce(new AccordNonEnregistre(message, new Error(message)));
  render(<AgentSession model="openai::test" profileId="researcher" onBack={vi.fn()} />);
  fireEvent.change(screen.getByLabelText(/Message à l/), { target: { value: 'Analyse fictive' } });
  fireEvent.click(screen.getByTitle('Envoyer'));
  fireEvent.click(await screen.findByRole('button', { name: "Confirmer l'appel" }));

  expect(await screen.findByRole('alert')).toHaveTextContent(message);
  expect(screen.getByRole('alert')).not.toHaveTextContent('Vérifie la connexion au moteur');
  expect(moteur.mission).not.toHaveBeenCalled();
});
