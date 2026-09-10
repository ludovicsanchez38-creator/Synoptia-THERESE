/**
 * Cycle 6, lecteur D69 (CRMPanel.tsx) : quand des contacts étaient déjà en
 * cache, un rechargement en panne n'appelait pas `setError`. L'écran gardait
 * une liste peut-être périmée sans dire que la lecture avait échoué.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useCRMStore } from '../../stores/crmStore';
import { useContactsStore } from '../../stores/contactsStore';
import type { Contact } from '../../services/api';

const api = vi.hoisted(() => ({ listProjects: vi.fn(), listContacts: vi.fn() }));
vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...reel, listProjects: (...a: unknown[]) => api.listProjects(...a), listActivities: vi.fn().mockResolvedValue([]) };
});
vi.mock('../../services/api/memory', async () => {
  const reel = await vi.importActual<typeof import('../../services/api/memory')>('../../services/api/memory');
  return { ...reel, listContacts: (...a: unknown[]) => api.listContacts(...a) };
});

import { CRMPanel } from './CRMPanel';

const marie = {
  id: 'ct-1', first_name: 'Marie', last_name: 'Lefevre', company: 'Lefevre Conseil', email: null, phone: null,
  notes: null, tags: null, scope: 'global', stage: 'prospect', created_at: '2026-08-01T00:00:00Z', updated_at: '2026-08-01T00:00:00Z',
} as unknown as Contact;

describe('D69 : un rechargement en panne est dit même avec des contacts en cache', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useCRMStore.setState({ projects: [], activeTab: 'pipeline' });
    useContactsStore.setState({ contacts: [marie], loaded: true, loading: false, error: null, selectedContactId: null, truncated: false });
  });

  it('projets en panne : alerte visible, contacts toujours affichés', async () => {
    api.listContacts.mockResolvedValue([marie]);
    api.listProjects.mockRejectedValue(new Error('Le serveur ne répond pas'));
    render(<CRMPanel standalone />);
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(/Le serveur ne répond pas/));
    expect(screen.getByText(/1 contact/)).toBeInTheDocument();
  });

  it('contacts en panne : alerte visible, ancienne liste conservée', async () => {
    api.listContacts.mockRejectedValue(new Error('boom'));
    api.listProjects.mockResolvedValue([]);
    render(<CRMPanel standalone />);
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(/Impossible de charger les contacts/));
    expect(screen.getByText(/1 contact/)).toBeInTheDocument();
  });
});
