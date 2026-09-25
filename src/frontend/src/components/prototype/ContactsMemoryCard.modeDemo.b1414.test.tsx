/**
 * B-1414 (relecture de P-120, cycle 13) : en mode démo, la liste et la fiche
 * de « Retrouver » montraient les vrais noms (aucun masque), et la frise
 * d'activités (Pipeline, puis la fiche par P-120) rendait titres et
 * descriptions en clair. Famille B-1080 : une démonstration ne montre
 * aucun vrai nom.
 */
import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Contact } from '../../services/api/memory';
import { useDemoStore } from '../../stores/demoStore';

const apiMocks = vi.hoisted(() => ({ listActivities: vi.fn() }));
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  listActivities: apiMocks.listActivities,
}));

import { ContactsMemoryCanvas, ContactsMemoryCard } from './ContactsMemoryCard';

const helene: Contact = {
  id: 'c-helene', first_name: 'Hélène', last_name: 'Ménard', company: 'Ménard Conseil', email: 'helene@menard.test',
  phone: '06 12 34 56 78', address: null, notes: 'Hélène prépare une prise de parole.', tags: [], stage: 'client', score: 0,
  source: 'local', last_interaction: null, created_at: '2026-09-20T09:00:00Z', updated_at: '2026-09-20T09:00:00Z',
};

const PRIVE = /Hélène|Ménard|helene@menard|06 12 34 56 78/;

describe('B-1414 : Retrouver ne montre aucun vrai nom en démonstration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useDemoStore.setState({ enabled: true });
    apiMocks.listActivities.mockResolvedValue([{
      id: 'a1', contact_id: 'c-helene', type: 'note', title: 'Note rendez-vous : Séance Hélène Ménard',
      description: 'Hélène veut reprendre confiance.', extra_data: null, created_at: '2026-09-24T10:00:00Z',
    }]);
  });
  afterEach(() => {
    useDemoStore.setState({ enabled: false, replacementMap: new Map() });
  });

  it('la fiche, ses notes et son historique sont masqués', async () => {
    const { container } = render(
      <ContactsMemoryCanvas
        resource={{ status: 'ready', error: null, data: [helene] }}
        selectedContactId="c-helene"
        onSelectContact={vi.fn()}
        onRetry={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );
    await screen.findByText(/Note rendez-vous/);
    expect(container.textContent).not.toMatch(PRIVE);
  });

  it('la carte de l’accueil est masquée', () => {
    const { container } = render(
      <ContactsMemoryCard
        resource={{ status: 'ready', error: null, data: [helene] }}
        onRetry={vi.fn()}
        onOpenContact={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );
    expect(container.textContent).not.toMatch(PRIVE);
  });
});
