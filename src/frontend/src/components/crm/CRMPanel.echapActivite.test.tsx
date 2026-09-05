/**
 * B-336 (05/09/2026) : la modale « Nouvelle activité » se déclarait dialog
 * et aria-modal sans s'inscrire dans la pile Échap. La cascade de la coque
 * ne trouvait aucun preneur et éjectait la vue CRM entière, saisie comprise.
 * Même correctif que B-262 pour la modale de création de contact.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useCRMStore } from '../../stores/crmStore';
import { useContactsStore } from '../../stores/contactsStore';
import { _clearEscapeHandlers, runTopEscapeHandler } from '../../lib/escapeStack';

const { CONTACTS } = vi.hoisted(() => ({
  CONTACTS: [
    {
      id: 'c-marie', first_name: 'Marie', last_name: 'Curie', company: null, email: null,
      phone: null, address: null, notes: null, tags: null, source: null, stage: 'contact',
      score: 50, last_interaction: null, created_at: '2026-09-01T10:00:00',
      updated_at: '2026-09-01T10:00:00',
    },
  ] as never[],
}));

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...reel, listProjects: vi.fn().mockResolvedValue([]), listActivities: vi.fn().mockResolvedValue([]) };
});

import { CRMPanel } from './CRMPanel';

describe('CRMPanel : Échap sur la modale Nouvelle activité (B-336)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    useCRMStore.setState({ projects: [], activeTab: 'activities' });
    useContactsStore.setState({ contacts: CONTACTS, selectedContactId: 'c-marie', truncated: false });
  });
  afterEach(() => _clearEscapeHandlers());

  it('Échap ferme la modale seule, sans retomber sur la cascade de la coque', async () => {
    render(<CRMPanel standalone />);
    fireEvent.click(await screen.findByRole('button', { name: /Ajouter une activité/i }));
    await screen.findByRole('dialog', { name: 'Nouvelle activité CRM' });

    expect(runTopEscapeHandler()).toBe(true);
    await waitFor(() =>
      expect(screen.queryByRole('dialog', { name: 'Nouvelle activité CRM' })).not.toBeInTheDocument(),
    );
  });
});
