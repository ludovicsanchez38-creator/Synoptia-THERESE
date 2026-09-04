/** B-314 : l'étape, pas la source facultative, détermine le Pipeline. */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useCRMStore } from '../../stores/crmStore';
import { useContactsStore } from '../../stores/contactsStore';
import type { ContactResponse } from '../../services/api';

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    listProjects: vi.fn().mockResolvedValue([]),
    listActivities: vi.fn().mockResolvedValue([]),
    listContacts: vi.fn().mockRejectedValue(new Error('hors réseau')),
  };
});

import { CRMPanel } from './CRMPanel';

function contact(patch: Partial<ContactResponse>): ContactResponse {
  return {
    id: 'ct-1',
    first_name: 'Marie',
    last_name: 'Lefèvre',
    company: null,
    email: null,
    phone: null,
    address: null,
    notes: null,
    tags: null,
    stage: 'contact',
    score: 0,
    source: null,
    last_interaction: null,
    created_at: '2026-09-01T10:00:00Z',
    updated_at: '2026-09-01T10:00:00Z',
    ...patch,
  } as ContactResponse;
}

describe("B-314 : le Pipeline montre chaque contact", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useCRMStore.setState({ projects: [], activeTab: 'pipeline' });
    useContactsStore.setState({ contacts: [], selectedContactId: null, truncated: false });
  });

  it('inclut un contact sans source et annonce le total réel', async () => {
    useContactsStore.setState({
      contacts: [
        contact({ id: 'ct-1', source: null }),
        contact({ id: 'ct-2', first_name: 'Paul', last_name: 'Girard', source: 'site-web' }),
      ],
    });

    render(<CRMPanel standalone />);

    expect(await screen.findByText(/2 contacts/)).toBeInTheDocument();
    expect(screen.getByText('Marie Lefèvre')).toBeInTheDocument();
    expect(screen.getByText('Paul Girard')).toBeInTheDocument();
  });

  it("n'affiche plus l'ancienne explication par la source", async () => {
    useContactsStore.setState({ contacts: [contact({ source: 'site-web' })] });

    render(<CRMPanel standalone />);

    await screen.findByRole('tablist');
    expect(screen.queryByText(/seuls les contacts ayant une source/i)).toBeNull();
  });
});
