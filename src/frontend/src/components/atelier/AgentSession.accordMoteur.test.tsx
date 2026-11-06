import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { installLocalStorageStub } from '../../test/localStorage-stub';
import { flushConsentDecisions, queueConsentDecision } from '../../lib/consentSync';
import { AccordNonEnregistre } from '../../services/api/core';

const moteur = vi.hoisted(() => ({
  consent: vi.fn(),
  mission: vi.fn(),
}));

vi.mock('../../services/api/agents', () => ({
  getAgentProfiles: async () => [{ id: 'researcher', name: 'Chercheur', tools: [],
    default_model: 'openai::modele-test' }],
  getAgentConsent: (...args: unknown[]) => moteur.consent(...args),
  streamAgentSpawn: async function* (...args: unknown[]) {
    moteur.mission(...args);
    yield { type: 'done', content: 'Terminé' };
  },
}));

import { AgentSession } from './AgentSession';

const MESSAGE = 'Le profil a changé. Reviens au profil concerné avant de réessayer.';

beforeEach(() => {
  installLocalStorageStub();
  localStorage.setItem('therese:data-profile', '/profils/test');
  vi.mocked(globalThis.fetch).mockReset();
  moteur.mission.mockReset();
  moteur.consent.mockReset().mockResolvedValue({
    model: 'openai::modele-test', provider: 'openai', label: 'OpenAI',
    purposes: ['llm'], granted_purposes: [],
  });
});

async function confirmer(): Promise<void> {
  fireEvent.change(screen.getByLabelText(/Message à l/), { target: { value: 'Analyse fictive' } });
  fireEvent.click(screen.getByTitle('Envoyer'));
  fireEvent.click(await screen.findByRole('button', { name: "Confirmer l'appel" }));
}

async function laisserUnAccordEnAttente(): Promise<void> {
  vi.mocked(globalThis.fetch).mockRejectedValueOnce(new TypeError('Failed to fetch'));
  queueConsentDecision('llm', 'openai', true, ['consigne']);
  await flushConsentDecisions().catch(() => {});
  vi.mocked(globalThis.fetch).mockReset();
}

function doublerLeMoteur(refus: boolean): string[] {
  const routes: string[] = [];
  vi.mocked(globalThis.fetch).mockImplementation(async entree => {
    const route = new URL(String(entree)).pathname;
    routes.push(route);
    if (route !== '/api/consents') throw new Error(`Route inattendue : ${route}`);
    if (refus) return new Response(JSON.stringify({ detail: MESSAGE }), { status: 409 });
    throw new TypeError('Failed to fetch');
  });
  return routes;
}

describe('AgentSession : accord du moteur avant la mission', () => {
  it('confirmSend affiche le refus du moteur et ne démarre aucune mission', async () => {
    await laisserUnAccordEnAttente();
    const routes = doublerLeMoteur(true);
    render(<AgentSession model="openai::modele-test" profileId="researcher" onBack={vi.fn()} />);

    await confirmer();

    expect(await screen.findByRole('alert')).toHaveTextContent(`La mission n’a pas démarré : ton accord n’a pas été enregistré par le moteur. ${MESSAGE}`);
    expect(moteur.mission).not.toHaveBeenCalled();
    expect(moteur.consent).not.toHaveBeenCalled();
    expect(routes).toEqual(['/api/consents']);
  });

  it('confirmSend garde le message de connexion lors d’une coupure', async () => {
    await laisserUnAccordEnAttente();
    const routes = doublerLeMoteur(false);
    render(<AgentSession model="openai::modele-test" profileId="researcher" onBack={vi.fn()} />);

    await confirmer();

    expect(await screen.findByRole('alert')).toHaveTextContent('Vérifie la connexion au moteur');
    expect(moteur.mission).not.toHaveBeenCalled();
    expect(routes).toEqual(['/api/consents']);
  });

  it('garde le message actuel si la vérification de destination échoue', async () => {
    moteur.consent.mockRejectedValueOnce(new AccordNonEnregistre(MESSAGE, new Error(MESSAGE)));
    render(<AgentSession model="openai::modele-test" profileId="researcher" onBack={vi.fn()} />);

    await confirmer();

    expect(await screen.findByRole('alert')).toHaveTextContent('Vérifie la connexion au moteur');
    expect(screen.getByRole('alert')).not.toHaveTextContent(MESSAGE);
    expect(moteur.mission).not.toHaveBeenCalled();
  });

  it('autoriserAgent affiche le refus du moteur et ne démarre aucune mission', async () => {
    const routes = doublerLeMoteur(true);
    render(<AgentSession model="openai::modele-test" profileId="researcher" onBack={vi.fn()} />);
    await confirmer();
    await screen.findByTestId('agent-cloud-consent');

    fireEvent.click(screen.getByText('Autoriser et envoyer'));

    expect(await screen.findByRole('alert')).toHaveTextContent(`La mission n’a pas démarré : ton accord n’a pas été enregistré par le moteur. ${MESSAGE}`);
    expect(moteur.mission).not.toHaveBeenCalled();
    expect(moteur.consent).toHaveBeenCalledTimes(1);
    expect(routes).toEqual(['/api/consents']);
  });

  it('autoriserAgent garde le message de connexion lors d’une coupure', async () => {
    const routes = doublerLeMoteur(false);
    render(<AgentSession model="openai::modele-test" profileId="researcher" onBack={vi.fn()} />);
    await confirmer();
    await screen.findByTestId('agent-cloud-consent');

    fireEvent.click(screen.getByText('Autoriser et envoyer'));

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Vérifie la connexion au moteur'));
    expect(moteur.mission).not.toHaveBeenCalled();
    expect(routes).toEqual(['/api/consents']);
  });
});
