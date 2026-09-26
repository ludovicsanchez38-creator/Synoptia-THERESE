/**
 * Revue P-148, passe 2, constat 1, côté coque : chaque demande explicite de
 * fiche émet un jeton qui vide la recherche du panneau Contacts, resté monté.
 * Ici la palette et la carte Contacts de l'accueil ; la fenêtre d'un projet
 * est couverte dans ConversationCanvasPrototype.projetMene.p148.test.tsx.
 *
 * « Cette semaine » et les points d'attention émettent aussi le jeton, mais
 * aucun test ne peut l'observer : ils ne sont visibles que sur l'accueil
 * « aujourd'hui », où le panneau de contexte est démonté (sa recherche avec).
 */
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useContactsStore } from '../../stores/contactsStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { useStatusStore } from '../../stores/statusStore';
import { _clearEscapeHandlers } from '../../lib/escapeStack';

const apiMocks = vi.hoisted(() => ({ fetchSemaineDashboard: vi.fn(), listProjects: vi.fn() }));
vi.mock('../../services/api/dashboard', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api/dashboard')>()),
  fetchSemaineDashboard: apiMocks.fetchSemaineDashboard,
}));
vi.mock('../../services/api/memory', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api/memory')>()),
  listProjects: apiMocks.listProjects,
}));

import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

function contact(id: string, prenom: string, nom: string) {
  return {
    id, first_name: prenom, last_name: nom, company: null, email: null, phone: null, address: null, notes: null,
    tags: [], stage: 'contact', score: 0, source: null, last_interaction: null,
    created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-01T00:00:00Z',
  };
}
const MARIE = contact('c-marie', 'Marie', 'Durand');
const ALEX = contact('c-alex', 'Alex', 'Martin');

const titreDeLaFiche = () => screen.queryAllByRole('heading', { level: 3, name: /Durand|Martin/ })[0]?.textContent ?? null;

/** Une recherche tapée dans le panneau Contacts, qui écarte Marie. */
async function chercherAlexDansLePanneau() {
  const champ = await screen.findByLabelText('Rechercher un contact');
  fireEvent.change(champ, { target: { value: 'Alex' } });
  await waitFor(() => expect(titreDeLaFiche()).toBe('Alex Martin'));
  return champ;
}

describe('Revue P-148, passe 2, constat 1 : la coque émet un jeton à chaque demande de fiche', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    window.history.replaceState({}, '', '/?interface=conversation-canvas');
    useNavigationStore.setState({ activeView: null, history: [] } as never);
    usePanelStore.setState({ showProjectModal: false, editingProject: null } as never);
    useStatusStore.setState({ notifications: [] } as never);
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false } as never);
    useContactsStore.setState({ contacts: [MARIE, ALEX] as never, loaded: true, loading: false, error: null, fetchContacts: vi.fn().mockResolvedValue(undefined) } as never);
    apiMocks.listProjects.mockResolvedValue([]);
    apiMocks.fetchSemaineDashboard.mockResolvedValue({
      date: '2026-09-25', mois: '2026-09', encaisse_du_mois: {}, prospects_par_etape: {}, indisponibles: [],
      a_venir: [{ kind: 'relance', id: 'c-marie', contact_id: 'c-marie', titre: 'Relancer Marie Durand', date: '2026-10-01T09:00:00' }],
    });
  });

  it('palette : la fiche choisie l’emporte sur la recherche du panneau, qui est vidée', async () => {
    render(<ConversationCanvasPrototype />);
    await act(async () => { await Promise.resolve(); });
    const choisirMarie = async () => {
      fireEvent.click(screen.getByRole('button', { name: /^Rechercher(Ctrl\+K|⌘K)$/ }));
      fireEvent.change(screen.getByRole('combobox', { name: /Rechercher une commande/ }), { target: { value: 'durand' } });
      await act(async () => { await Promise.resolve(); });
      fireEvent.click(within(screen.getByRole('listbox', { name: 'Résultats' })).getByRole('option', { name: /Marie Durand/ }));
      await act(async () => { await Promise.resolve(); });
    };
    await choisirMarie();
    await waitFor(() => expect(titreDeLaFiche()).toBe('Marie Durand'));
    const champ = await chercherAlexDansLePanneau();

    await choisirMarie();

    await waitFor(() => expect(titreDeLaFiche()).toBe('Marie Durand'));
    expect(champ).toHaveValue('');
  });

  it('carte Contacts de l’accueil : la fiche choisie l’emporte sur la recherche du panneau, qui est vidée', async () => {
    render(<ConversationCanvasPrototype />);
    await act(async () => { await Promise.resolve(); });
    // La palette ouvre Marie : l'accueil passe à la carte Contacts, le panneau est ouvert.
    fireEvent.click(screen.getByRole('button', { name: /^Rechercher(Ctrl\+K|⌘K)$/ }));
    fireEvent.change(screen.getByRole('combobox', { name: /Rechercher une commande/ }), { target: { value: 'durand' } });
    await act(async () => { await Promise.resolve(); });
    fireEvent.click(within(screen.getByRole('listbox', { name: 'Résultats' })).getByRole('option', { name: /Marie Durand/ }));
    await waitFor(() => expect(titreDeLaFiche()).toBe('Marie Durand'));
    const champ = await chercherAlexDansLePanneau();

    // Sous la largeur xl, le panneau couvre l'accueil (usePanneauCouvrant) ;
    // au-delà, la carte reste à côté et cliquable. jsdom n'a pas de largeur.
    const carte = screen.getByTestId('contacts-memory-card');
    fireEvent.click(within(carte).getByRole('button', { name: /Marie Durand/, hidden: true }));

    await waitFor(() => expect(titreDeLaFiche()).toBe('Marie Durand'));
    expect(champ).toHaveValue('');
  });
});
