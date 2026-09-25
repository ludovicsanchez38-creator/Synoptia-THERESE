/**
 * P-135 (persona Nathalie, cycle 13) : l'Accueil ne regardait qu'aujourd'hui.
 * « Cette semaine » montre ce qui vient sur sept jours (relances, échéances)
 * et deux chiffres, chacun avec ce qu'il compte.
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({ fetchSemaineDashboard: vi.fn() }));
vi.mock('../../services/api/dashboard', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api/dashboard')>()),
  fetchSemaineDashboard: apiMocks.fetchSemaineDashboard,
}));

import { CetteSemaine } from './CetteSemaine';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';
import { useNavigationStore } from '../../stores/navigationStore';

describe('P-135 : Cette semaine', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.fetchSemaineDashboard.mockResolvedValue({
      date: '2026-09-24', mois: '2026-09',
      a_venir: [
        { kind: 'relance', id: 'c-karim', contact_id: 'c-karim', titre: 'Relancer Karim Benali', date: '2026-09-25T09:00:00' },
        { kind: 'tache', id: 't-1', contact_id: null, titre: 'Envoyer le devis', date: '2026-09-28T09:00:00' },
      ],
      encaisse_du_mois: { EUR: 1440 },
      prospects_par_etape: { discovery: 2, proposition: 1 },
      indisponibles: [],
    });
  });

  it('liste ce qui vient et ouvre la personne ou les tâches', async () => {
    const onOpenContact = vi.fn();
    const onOpenTasks = vi.fn();
    render(<CetteSemaine onOpenContact={onOpenContact} onOpenTasks={onOpenTasks} />);
    const section = await screen.findByRole('region', { name: 'Cette semaine' });
    fireEvent.click(await within(section).findByRole('button', { name: /Relancer Karim Benali/ }));
    fireEvent.click(within(section).getByRole('button', { name: /Envoyer le devis/ }));
    expect(onOpenContact).toHaveBeenCalledWith('c-karim');
    expect(onOpenTasks).toHaveBeenCalled();
  });

  it('les deux chiffres disent leur source', async () => {
    render(<CetteSemaine onOpenContact={vi.fn()} onOpenTasks={vi.fn()} />);
    const section = await screen.findByRole('region', { name: 'Cette semaine' });
    expect(await within(section).findByText(/Encaissé en septembre/)).toBeInTheDocument();
    expect(within(section).getByText(/1\s440,00\s€/)).toBeInTheDocument();
    // Le chiffre dit ce qu'il compte : les avoirs ne sont pas déduits.
    expect(within(section).getByText('Source : factures payées ce mois-ci, avoirs non déduits.')).toBeInTheDocument();
    expect(within(section).getByText(/Prospects en cours : 3/)).toBeInTheDocument();
    expect(within(section).getByText(/Découverte 2, Proposition 1/)).toBeInTheDocument();
  });

  it('une semaine vide le dit, une lecture en panne aussi', async () => {
    apiMocks.fetchSemaineDashboard.mockResolvedValue({
      date: '2026-09-24', mois: '2026-09', a_venir: [], encaisse_du_mois: {}, prospects_par_etape: {}, indisponibles: ['encaisse'],
    });
    render(<CetteSemaine onOpenContact={vi.fn()} onOpenTasks={vi.fn()} />);
    const section = await screen.findByRole('region', { name: 'Cette semaine' });
    expect(await within(section).findByText('Rien de daté dans les sept prochains jours.')).toBeInTheDocument();
    expect(within(section).getByText(/L’encaissé n’a pas pu être lu/)).toBeInTheDocument();
  });

  it('l’Accueil porte la section, sous le brief', async () => {
    window.history.replaceState({}, '', '/?interface=conversation-canvas');
    useNavigationStore.setState({ activeView: null, history: [] } as never);
    render(<ConversationCanvasPrototype />);
    expect(await screen.findByRole('region', { name: 'Cette semaine' })).toBeInTheDocument();
  });
});
