import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { installLocalStorageStub } from '../../test/localStorage-stub';

const moteur = vi.hoisted(() => ({ mission: vi.fn() }));

vi.mock('../../services/api/agents', async (original) => ({
  ...await original<typeof import('../../services/api/agents')>(),
  getAgentProfiles: async () => [{ id: 'researcher', name: 'Chercheur', tools: [], default_model: 'openai::test' }],
  streamAgentSpawn: async function* (...args: unknown[]) { moteur.mission(...args); yield { type: 'done' }; },
}));

import { AgentSession } from './AgentSession';

beforeEach(() => {
  installLocalStorageStub();
  localStorage.setItem('therese:data-profile', '/profil-fictif');
  moteur.mission.mockReset();
  vi.mocked(globalThis.fetch).mockReset();
});

it.each(['confirmation', 'autorisation'])('affiche le refus HTTP réel pendant %s', async (etape) => {
  const message = 'Ce profil d’agent est introuvable. Reviens au catalogue.';
  let lectures = 0;
  const routes: string[] = [];
  vi.mocked(globalThis.fetch).mockImplementation(async (entree) => {
    const route = new URL(String(entree)).pathname;
    routes.push(route);
    if (route === '/api/consents') return new Response('{}', { status: 200 });
    if (route !== '/api/agents/profiles/researcher/consent') throw new Error('Route inattendue');
    lectures++;
    if (etape === 'autorisation' && lectures === 1) {
      return new Response(JSON.stringify({
        model: 'openai::test', provider: 'openai', label: 'OpenAI', purposes: ['llm'], granted_purposes: [],
      }), { status: 200 });
    }
    return new Response(JSON.stringify({ detail: message }), { status: 404 });
  });

  render(<AgentSession model="openai::test" profileId="researcher" onBack={vi.fn()} />);
  fireEvent.change(screen.getByLabelText(/Message à l/), { target: { value: 'Analyse fictive' } });
  fireEvent.click(screen.getByTitle('Envoyer'));
  fireEvent.click(await screen.findByRole('button', { name: "Confirmer l'appel" }));
  if (etape === 'autorisation') {
    fireEvent.click(await screen.findByRole('button', { name: 'Autoriser et envoyer' }));
  }

  expect(await screen.findByRole('alert')).toHaveTextContent(message);
  expect(screen.getByRole('alert')).not.toHaveTextContent('Vérifie la connexion au moteur');
  expect(moteur.mission).not.toHaveBeenCalled();
  expect(lectures).toBe(etape === 'autorisation' ? 2 : 1);
  expect(routes.includes('/api/consents')).toBe(etape === 'autorisation');
});

it.each(['confirmation', 'autorisation'])('signale une coupure de destination pendant %s', async (etape) => {
  let lectures = 0;
  vi.mocked(globalThis.fetch).mockImplementation(async (entree) => {
    const route = new URL(String(entree)).pathname;
    if (route === '/api/consents') return new Response('{}', { status: 200 });
    if (route !== '/api/agents/profiles/researcher/consent') throw new Error('Route inattendue');
    lectures++;
    if (etape === 'autorisation' && lectures === 1) {
      return new Response(JSON.stringify({
        model: 'openai::test', provider: 'openai', label: 'OpenAI', purposes: ['llm'], granted_purposes: [],
      }), { status: 200 });
    }
    throw new TypeError('Coupure simulée');
  });

  render(<AgentSession model="openai::test" profileId="researcher" onBack={vi.fn()} />);
  fireEvent.change(screen.getByLabelText(/Message à l/), { target: { value: 'Analyse fictive' } });
  fireEvent.click(screen.getByTitle('Envoyer'));
  fireEvent.click(await screen.findByRole('button', { name: "Confirmer l'appel" }));
  if (etape === 'autorisation') {
    fireEvent.click(await screen.findByRole('button', { name: 'Autoriser et envoyer' }));
  }

  expect(await screen.findByRole('alert')).toHaveTextContent('Vérifie la connexion au moteur');
  expect(moteur.mission).not.toHaveBeenCalled();
  expect(lectures).toBe(etape === 'autorisation' ? 2 : 1);
});
