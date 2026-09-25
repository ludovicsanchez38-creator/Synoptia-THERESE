/**
 * B-1419 : en démonstration, l'Accueil, « Cette semaine » et la palette
 * montraient les vrais noms tant qu'aucun panneau (Contacts, CRM, Tâches)
 * n'avait rempli la table de remplacement : `maskText` est l'identité sans
 * table. La coque remplit désormais la table dès que la démonstration est
 * active, et un panneau qui la remplit l'enrichit au lieu de l'écraser.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useContactsStore } from '../../stores/contactsStore';
import { useDemoStore } from '../../stores/demoStore';
import { useNavigationStore } from '../../stores/navigationStore';
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

const julien = {
  id: 'c-julien', first_name: 'Julien', last_name: 'Garnier', company: null, email: 'julien@garnier.test',
  phone: null, address: null, notes: null, tags: [], stage: 'contact', score: 0, source: null,
  last_interaction: null, created_at: '2026-09-01T00:00:00Z', updated_at: '2026-09-01T00:00:00Z',
};

describe('B-1419 : la démonstration masque aussi l’Accueil et la palette', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    window.history.replaceState({}, '', '/?interface=conversation-canvas');
    useNavigationStore.setState({ activeView: null, history: [] } as never);
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false } as never);
    useContactsStore.setState({ contacts: [julien] as never, loaded: true, loading: false, error: null, fetchContacts: vi.fn().mockResolvedValue(undefined) } as never);
    useDemoStore.setState({ enabled: true, replacementMap: new Map() });
    apiMocks.listProjects.mockResolvedValue([]);
    apiMocks.fetchSemaineDashboard.mockResolvedValue({
      date: '2026-09-25', mois: '2026-09', encaisse_du_mois: {}, prospects_par_etape: {}, indisponibles: [],
      a_venir: [{ kind: 'relance', id: 'c-julien', contact_id: 'c-julien', titre: 'Relancer Julien Garnier', date: '2026-10-01T09:00:00' }],
    });
  });
  afterEach(() => {
    useDemoStore.setState({ enabled: false, replacementMap: new Map() });
  });

  it('« Cette semaine » et la palette ne montrent pas le vrai nom', async () => {
    render(<ConversationCanvasPrototype />);
    const semaine = await screen.findByRole('region', { name: 'Cette semaine' });
    await act(async () => { await Promise.resolve(); });
    expect(semaine.textContent).not.toMatch(/Julien|Garnier/);

    fireEvent.click(screen.getByRole('button', { name: /^Rechercher(Ctrl\+K|⌘K)$/ }));
    fireEvent.change(screen.getByRole('combobox', { name: /Rechercher une commande/ }), { target: { value: 'julien' } });
    const resultats = screen.getByRole('listbox', { name: 'Résultats' });
    expect(resultats.textContent).not.toMatch(/Julien|Garnier/);
  });

  it('un panneau qui remplit la table l’enrichit sans l’écraser', async () => {
    const { buildReplacementMap } = await import('../../lib/demoMask');
    const { useDemoMask } = await import('../../hooks/useDemoMask');
    useDemoStore.setState({ replacementMap: buildReplacementMap([], [{ name: 'Refonte Orion' }]) });
    let remplir: ReturnType<typeof useDemoMask>['populateMap'] = () => undefined;
    function Sonde() { remplir = useDemoMask().populateMap; return null; }
    render(<Sonde />);
    act(() => remplir([julien], []));
    const carte = useDemoStore.getState().replacementMap;
    expect([...carte.keys()].some((cle) => /orion/i.test(cle))).toBe(true);
    expect([...carte.keys()].some((cle) => /garnier/i.test(cle))).toBe(true);
  });
});
