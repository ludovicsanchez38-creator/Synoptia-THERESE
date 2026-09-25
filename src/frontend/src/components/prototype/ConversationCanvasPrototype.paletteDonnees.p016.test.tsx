/**
 * P-016 (persona consultant, puis Claire claire-20) : « un consultant retrouve
 * son client par son nom, quelque part ». La palette (⌘K) ne cherchait que
 * les commandes et les capacités ; « Durand » ne rendait rien. Elle cherche
 * désormais aussi dans les contacts, les projets et les conversations, en tête
 * des résultats, et chaque résultat ouvre son objet.
 */
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useContactsStore } from '../../stores/contactsStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';

const apiMocks = vi.hoisted(() => ({ listProjects: vi.fn() }));
vi.mock('../../services/api/memory', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api/memory')>()),
  listProjects: apiMocks.listProjects,
}));

import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

const marie = {
  id: 'c-marie', first_name: 'Marie', last_name: 'Durand', company: 'Société Durand', email: 'marie@durand.test',
  phone: null, address: null, notes: null, tags: [], stage: 'proposition', score: 0, source: null,
  last_interaction: null, created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-01T00:00:00Z',
};

async function chercher(terme: string) {
  render(<ConversationCanvasPrototype />);
  await act(async () => { await Promise.resolve(); });
  fireEvent.click(screen.getByRole('button', { name: /^Rechercher(Ctrl\+K|⌘K)$/ }));
  const champ = screen.getByRole('combobox', { name: /Rechercher une commande/ });
  fireEvent.change(champ, { target: { value: terme } });
  await act(async () => { await Promise.resolve(); });
  return screen.getByRole('listbox', { name: 'Résultats' });
}

describe('P-016 : la palette retrouve un client par son nom', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    window.history.replaceState({}, '', '/?interface=conversation-canvas');
    useNavigationStore.setState({ activeView: null, history: [] } as never);
    apiMocks.listProjects.mockResolvedValue([{ id: 'p-durand', name: 'Refonte du site Durand', description: null, tags: ['web'] }]);
    useContactsStore.setState({ contacts: [marie] as never, loaded: true, loading: false, error: null, fetchContacts: vi.fn().mockResolvedValue(undefined) } as never);
    useChatStore.setState({
      conversations: [{
        id: 'conv-relance', title: 'Rédige la relance pour le client Du',
        messages: [{ id: 'm1', role: 'user', content: 'Rédige la relance pour le client Durand, sur la proposition.', timestamp: new Date() }],
        createdAt: new Date(), updatedAt: new Date(), synced: true,
      }],
      currentConversationId: null, isStreaming: false,
    } as never);
  });

  it('« Durand » trouve le contact, le projet et la conversation', async () => {
    const resultats = await chercher('durand');
    expect(within(resultats).getByRole('option', { name: /Marie Durand/ })).toBeInTheDocument();
    expect(await within(resultats).findByRole('option', { name: /Refonte du site Durand/ })).toBeInTheDocument();
    expect(within(resultats).getByRole('option', { name: /Rédige la relance pour le client Du/ })).toBeInTheDocument();
    const entetes = Array.from(resultats.querySelectorAll('[role="presentation"]')).map((n) => n.textContent?.trim());
    expect(entetes.slice(0, 3)).toEqual(['Contacts', 'Projets', 'Conversations']);
  });

  it('le contact choisi ouvre sa fiche', async () => {
    const resultats = await chercher('durand');
    fireEvent.click(within(resultats).getByRole('option', { name: /Marie Durand/ }));
    await act(async () => { await Promise.resolve(); });
    expect(screen.getAllByRole('heading', { name: 'Marie Durand' }).length).toBeGreaterThan(0);
  });

  it('la conversation choisie s’ouvre', async () => {
    const resultats = await chercher('durand');
    fireEvent.click(within(resultats).getByRole('option', { name: /Rédige la relance pour le client Du/ }));
    await act(async () => { await Promise.resolve(); });
    expect(useChatStore.getState().currentConversationId).toBe('conv-relance');
  });

  it('une section sans résultat ne garde pas son en-tête', async () => {
    const resultats = await chercher('julien-introuvable-mais-contact');
    const entetes = Array.from(resultats.querySelectorAll('[role="presentation"]')).map((n) => n.textContent?.trim());
    expect(entetes).not.toContain('Capacités');
  });
});
