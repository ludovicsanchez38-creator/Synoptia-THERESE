/**
 * B-1434 (recette P-146, lot 1, A-4) : la fiche de Retrouver affichait
 * « Notes mémorisées : Aucune note enregistrée pour ce contact » au-dessus
 * d'une note de rendez-vous visible dans l'Historique. Ce bloc ne montre que
 * les notes saisies sur la fiche ; il le dit, et ne nie plus l'historique.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { Contact } from '../../services/api/memory';

const apiMocks = vi.hoisted(() => ({ listActivities: vi.fn() }));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  listActivities: apiMocks.listActivities,
}));

import { ContactsMemoryCanvas } from './ContactsMemoryCard';

const HELENE: Contact = {
  id: 'c-helene', first_name: 'Hélène', last_name: 'Ménard', company: null, email: 'helene@example.test',
  phone: null, address: null, notes: null, tags: [], stage: 'client', score: 0, source: 'local',
  last_interaction: null, created_at: '2026-09-20T09:00:00Z', updated_at: '2026-09-20T09:00:00Z',
};

describe('B-1434 : les notes de la fiche ne nient pas l’historique', () => {
  it('une fiche sans note dit « Aucune note sur la fiche »', async () => {
    apiMocks.listActivities.mockResolvedValue([{
      id: 'a1', contact_id: 'c-helene', type: 'note', title: 'Note rendez-vous : Séance Hélène',
      description: null, extra_data: null, created_at: '2026-09-24T10:00:00Z',
    }]);
    render(
      <ContactsMemoryCanvas
        resource={{ status: 'ready', error: null, data: [HELENE] }}
        selectedContactId="c-helene"
        onSelectContact={vi.fn()}
        onRetry={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );
    await screen.findByText('Note rendez-vous : Séance Hélène');
    expect(screen.getByText('Notes de la fiche')).toBeInTheDocument();
    expect(screen.getByText('Aucune note sur la fiche.')).toBeInTheDocument();
    expect(screen.queryByText(/Aucune note enregistrée pour ce contact/)).toBeNull();
  });
});
