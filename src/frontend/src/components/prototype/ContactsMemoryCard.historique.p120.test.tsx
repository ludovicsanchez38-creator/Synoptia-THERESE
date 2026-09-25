/**
 * P-120 (persona Claire, cycle 13) : la note de séance ajoutée « au CRM du
 * contact » depuis Préparer ne se retrouvait pas depuis la fiche de
 * « Retrouver » : la fiche ne montrait que les notes saisies à la création,
 * l'historique ne vivait que dans la vue Pipeline.
 */
import { render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Contact } from '../../services/api/memory';

const apiMocks = vi.hoisted(() => ({ listActivities: vi.fn() }));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  listActivities: apiMocks.listActivities,
}));

import { ContactsMemoryCanvas } from './ContactsMemoryCard';

const helene: Contact = {
  id: 'c-helene', first_name: 'Hélène', last_name: 'Ménard', company: null, email: 'helene@example.test',
  phone: null, address: null, notes: null, tags: [], stage: 'client', score: 0, source: 'local',
  last_interaction: null, created_at: '2026-09-20T09:00:00Z', updated_at: '2026-09-20T09:00:00Z',
};

describe('P-120 : l’historique sur la fiche de Retrouver', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('la note de séance ajoutée depuis Préparer se lit sur la fiche', async () => {
    apiMocks.listActivities.mockResolvedValue([{
      id: 'a1', contact_id: 'c-helene', type: 'note', title: 'Note rendez-vous : Séance Hélène',
      description: 'Objectif : reprendre confiance à l’oral.', extra_data: null, created_at: '2026-09-24T10:00:00Z',
    }]);
    render(
      <ContactsMemoryCanvas
        resource={{ status: 'ready', error: null, data: [helene] }}
        selectedContactId="c-helene"
        onSelectContact={vi.fn()}
        onRetry={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );
    const historique = await screen.findByRole('region', { name: 'Historique' });
    expect(await within(historique).findByText('Note rendez-vous : Séance Hélène')).toBeInTheDocument();
    expect(within(historique).getByText('Objectif : reprendre confiance à l’oral.')).toBeInTheDocument();
    expect(apiMocks.listActivities).toHaveBeenCalledWith(expect.objectContaining({ contact_id: 'c-helene' }));
  });
});
