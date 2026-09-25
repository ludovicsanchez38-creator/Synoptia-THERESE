/**
 * B-1430 (recette P-146, lot 1) : « Cette semaine » ignorait les rendez-vous.
 * Un rendez-vous se lit à son jour, ouvre l'Agenda, et un rendez-vous sur la
 * journée (« 2026-09-26 ») garde son jour quel que soit le fuseau.
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({ fetchSemaineDashboard: vi.fn() }));
vi.mock('../../services/api/dashboard', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api/dashboard')>()),
  fetchSemaineDashboard: apiMocks.fetchSemaineDashboard,
}));

import { CetteSemaine } from './CetteSemaine';

describe('B-1430 : les rendez-vous de la semaine', () => {
  it('un rendez-vous ouvre l’Agenda et garde son jour', async () => {
    apiMocks.fetchSemaineDashboard.mockResolvedValue({
      date: '2026-09-24', mois: '2026-09',
      a_venir: [
        { kind: 'rdv', id: 'ev-journee', contact_id: null, titre: 'Salon des artisans', date: '2026-09-26' },
        { kind: 'rdv', id: 'ev-lundi', contact_id: null, titre: 'Point fournisseur bois', date: '2026-09-28T14:00:00' },
      ],
      encaisse_du_mois: {}, prospects_par_etape: {}, indisponibles: [],
    });
    const onOpenAgenda = vi.fn();
    render(<CetteSemaine onOpenContact={vi.fn()} onOpenTasks={vi.fn()} onOpenAgenda={onOpenAgenda} />);
    const section = await screen.findByRole('region', { name: 'Cette semaine' });
    const salon = await within(section).findByRole('button', { name: /Salon des artisans/ });
    expect(salon).toHaveTextContent('samedi 26 sept.');
    fireEvent.click(within(section).getByRole('button', { name: /Point fournisseur bois/ }));
    expect(onOpenAgenda).toHaveBeenCalled();
  });
});
