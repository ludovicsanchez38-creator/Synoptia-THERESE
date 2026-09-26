/**
 * P-016 (persona consultant, puis Claire claire-20) : « un consultant retrouve
 * son client par son nom, quelque part ». La palette (⌘K) ne cherchait que
 * les commandes et les capacités ; « Durand » ne rendait rien. Elle cherche
 * désormais aussi dans les contacts, les projets et les conversations, en tête
 * des résultats, et chaque résultat ouvre son objet.
 */
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError } from '../../services/api/core';
import { useChatStore } from '../../stores/chatStore';
import { useContactsStore } from '../../stores/contactsStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { useStatusStore } from '../../stores/statusStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';

const apiMocks = vi.hoisted(() => ({ listProjects: vi.fn(), getProject: vi.fn(), lireLEnsembleDuProjet: vi.fn() }));
vi.mock('../../services/api/memory', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api/memory')>()),
  listProjects: apiMocks.listProjects,
  getProject: apiMocks.getProject,
  lireLEnsembleDuProjet: apiMocks.lireLEnsembleDuProjet,
}));

import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

const marie = {
  id: 'c-marie', first_name: 'Marie', last_name: 'Durand', company: 'Société Durand', email: 'marie@durand.test',
  phone: null, address: null, notes: null, tags: [], stage: 'proposition', score: 0, source: null,
  last_interaction: null, created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-01T00:00:00Z',
};

const DURAND = {
  id: 'p-durand', name: 'Refonte du site Durand', description: null, contact_id: null, status: 'active',
  budget: null, notes: null, tags: ['web'], created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-01T00:00:00Z',
};

async function chercher(terme: string) {
  render(<ConversationCanvasPrototype />);
  await act(async () => { await Promise.resolve(); });
  // Un vrai clic donne le focus au bouton (fireEvent.click ne le fait pas).
  const rechercher = screen.getByRole('button', { name: /^Rechercher(Ctrl\+K|⌘K)$/ });
  rechercher.focus();
  fireEvent.click(rechercher);
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
    apiMocks.lireLEnsembleDuProjet.mockReturnValue(new Promise(() => {}));
    usePanelStore.setState({ showProjectModal: false, editingProject: null } as never);
    useStatusStore.setState({ notifications: [] } as never);
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

  it('P-148 : le projet choisi ouvre sa fenêtre, plus la liste des projets', async () => {
    apiMocks.getProject.mockResolvedValue(DURAND);
    const resultats = await chercher('durand');
    fireEvent.click(await within(resultats).findByRole('option', { name: /Refonte du site Durand/ }));
    expect(await screen.findByRole('dialog', { name: 'Projet Refonte du site Durand' })).toBeInTheDocument();
    expect(apiMocks.getProject).toHaveBeenCalledWith('p-durand');
    expect(usePanelStore.getState().editingProject).toEqual(DURAND);
    expect(screen.getByTestId('conversation-canvas-prototype').getAttribute('data-embedded-view')).not.toBe('projects');
  });

  it('P-148 : un projet supprimé entre-temps donne une notification, jamais une fenêtre vide', async () => {
    apiMocks.getProject.mockRejectedValue(new ApiError(404, 'Not Found', 'Project not found'));
    const resultats = await chercher('durand');
    fireEvent.click(await within(resultats).findByRole('option', { name: /Refonte du site Durand/ }));
    await waitFor(() => expect(useStatusStore.getState().notifications.map((n) => n.title)).toContain('Ce projet n’existe plus'));
    expect(screen.queryByRole('dialog', { name: /^Projet / })).toBeNull();
    expect(usePanelStore.getState().showProjectModal).toBe(false);
  });

  it('P-148 : ouverte depuis la palette, la fenêtre rend le focus au bouton de recherche en se fermant', async () => {
    apiMocks.getProject.mockResolvedValue(DURAND);
    const resultats = await chercher('durand');
    fireEvent.click(await within(resultats).findByRole('option', { name: /Refonte du site Durand/ }));
    await screen.findByRole('dialog', { name: 'Projet Refonte du site Durand' });
    await act(async () => { fireEvent.keyDown(window, { key: 'Escape' }); });
    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Projet Refonte du site Durand' })).toBeNull());
    await waitFor(() => expect(document.activeElement).toBe(screen.getByRole('button', { name: /^Rechercher(Ctrl\+K|⌘K)$/ })));
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
