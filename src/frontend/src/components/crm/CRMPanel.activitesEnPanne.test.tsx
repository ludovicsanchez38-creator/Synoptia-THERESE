/**
 * B-527 : un échec de chargement des activités s'affichait en « Aucune
 * activité enregistrée ». Une panne n'est pas un fil vide.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useCRMStore } from '../../stores/crmStore';
import { useContactsStore } from '../../stores/contactsStore';

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    listProjects: vi.fn().mockResolvedValue([]),
    listActivities: vi.fn().mockRejectedValue(new Error('boom')),
  };
});

vi.mock('../../services/api/memory', async () => {
  const reel = await vi.importActual<typeof import('../../services/api/memory')>(
    '../../services/api/memory',
  );
  return { ...reel, listContacts: vi.fn().mockResolvedValue([]) };
});

import { CRMPanel } from './CRMPanel';

describe('B-527 : une panne du fil des activités se distingue d’un fil vide', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useCRMStore.setState({ projects: [], activeTab: 'activities' });
    useContactsStore.setState({ contacts: [], selectedContactId: null, truncated: false });
  });

  it('affiche une alerte avec reprise, pas « Aucune activité enregistrée »', async () => {
    render(<CRMPanel standalone />);

    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(/n’ont pas pu être lues/),
    );
    expect(screen.queryByText('Aucune activité enregistrée')).toBeNull();
    expect(screen.getByRole('button', { name: 'Réessayer' })).toBeInTheDocument();
  });
});
