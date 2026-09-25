/**
 * P-116 (persona Claire, cycle 13) : la fiche d'Hélène ne montrait aucune de
 * ses séances. La fiche de Retrouver liste ses prochaines séances (rapprochées
 * par son adresse) ; une séance ouvre Préparer sur elle.
 */
import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Contact } from '../../services/api/memory';

const apiMocks = vi.hoisted(() => ({ listActivities: vi.fn(), listerLesSeancesDuContact: vi.fn() }));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  listActivities: apiMocks.listActivities,
  listerLesSeancesDuContact: apiMocks.listerLesSeancesDuContact,
}));

import { ContactsMemoryCanvas } from './ContactsMemoryCard';

const fiche = (email: string | null): Contact => ({
  id: 'c-helene', first_name: 'Hélène', last_name: 'Ménard', company: null, email,
  phone: null, address: null, notes: null, tags: [], stage: 'client', score: 0, source: 'local',
  last_interaction: null, created_at: '2026-09-20T09:00:00Z', updated_at: '2026-09-20T09:00:00Z',
});

const seance = {
  id: 'ev-3', calendar_id: 'cal-1', summary: 'Séance 3', description: null, location: null,
  start_datetime: '2026-09-26T14:00:00', end_datetime: '2026-09-26T15:00:00', start_date: null, end_date: null,
  all_day: false, attendees: ['helene@example.test'], recurrence: null, status: 'confirmed', synced_at: '2026-09-25T09:00:00',
};

function ouvrir(email: string | null) {
  render(
    <ContactsMemoryCanvas
      resource={{ status: 'ready', error: null, data: [fiche(email)] }}
      selectedContactId="c-helene" onSelectContact={vi.fn()} onRetry={vi.fn()} onOpenClassic={vi.fn()}
    />,
  );
}

describe('P-116 : les séances sur la fiche', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.listActivities.mockResolvedValue([]);
    apiMocks.listerLesSeancesDuContact.mockResolvedValue([seance]);
  });

  it('les prochaines séances s’affichent et ouvrent Préparer', async () => {
    const ecoute = vi.fn();
    window.addEventListener('therese:preparer-seance', ecoute);
    ouvrir('helene@example.test');
    const region = await screen.findByRole('region', { name: 'Prochaines séances' });
    const bouton = await within(region).findByRole('button', { name: /Séance 3/ });
    fireEvent.click(bouton);
    window.removeEventListener('therese:preparer-seance', ecoute);
    expect(apiMocks.listerLesSeancesDuContact).toHaveBeenCalledWith('c-helene');
    expect((ecoute.mock.calls[0][0] as CustomEvent).detail).toEqual({ evenement: seance });
  });

  it('sans adresse, la fiche dit comment relier ses séances', async () => {
    apiMocks.listerLesSeancesDuContact.mockResolvedValue([]);
    ouvrir(null);
    const region = await screen.findByRole('region', { name: 'Prochaines séances' });
    expect(region).toHaveTextContent('Ajoute son adresse e-mail');
    expect(apiMocks.listerLesSeancesDuContact).not.toHaveBeenCalled();
  });

  it('avec une adresse et rien à venir, elle le dit', async () => {
    apiMocks.listerLesSeancesDuContact.mockResolvedValue([]);
    ouvrir('helene@example.test');
    const region = await screen.findByRole('region', { name: 'Prochaines séances' });
    expect(await within(region).findByText(/Aucune séance à venir/)).toBeInTheDocument();
  });
});
