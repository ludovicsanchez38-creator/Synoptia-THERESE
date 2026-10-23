/**
 * B-205 : le fil d'activités du Pipeline affichait « Contact inconnu ».
 *
 * Le fil charge les activités de TOUS les contacts (`listActivities` sans
 * filtre). Le magasin complet permet de les nommer, y compris lorsque la
 * source facultative du contact n'est pas renseignée.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useCRMStore } from '../../stores/crmStore';
import { useContactsStore } from '../../stores/contactsStore';

const { CONTACTS, ACTIVITES } = vi.hoisted(() => {
  const base = {
    company: null,
    email: null,
    phone: null,
    address: null,
    notes: null,
    tags: null,
    stage: 'contact',
    score: 50,
    last_interaction: null,
    created_at: '2026-09-01T10:00:00',
    updated_at: '2026-09-01T10:00:00',
  };
  return {
    CONTACTS: [
      // Chemin Contacts : aucune source, mais une étape de pipeline valide.
      { ...base, id: 'c-memoire', first_name: 'Jean', last_name: 'Dupont', source: null },
      // Contact dont la source est renseignée.
      { ...base, id: 'c-pipeline', first_name: 'Alice', last_name: 'Martin', source: 'prospect' },
    ] as never[],
    ACTIVITES: [
      {
        id: 'a-1',
        contact_id: 'c-memoire',
        type: 'note',
        title: 'Note prise en conversation',
        description: null,
        extra_data: null,
        created_at: '2026-09-01T11:00:00',
      },
      {
        id: 'a-2',
        contact_id: 'c-pipeline',
        type: 'note',
        title: 'Relance envoyée',
        description: null,
        extra_data: null,
        created_at: '2026-09-01T12:00:00',
      },
    ] as never[],
  };
});

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    listProjects: vi.fn().mockResolvedValue([]),
    listActivities: vi.fn().mockResolvedValue(ACTIVITES),
  };
});

vi.mock('../../services/api/memory', async () => {
  const reel = await vi.importActual<typeof import('../../services/api/memory')>(
    '../../services/api/memory',
  );
  return { ...reel, listContacts: vi.fn().mockResolvedValue(CONTACTS) };
});

import { CRMPanel } from './CRMPanel';

describe('B-205 : une activité affichée nomme toujours son contact', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useCRMStore.setState({ projects: [], activeTab: 'activities' });
    useContactsStore.setState({ contacts: [], selectedContactId: null, truncated: false });
  });

  it("le fil global nomme aussi le contact venu du chemin Contacts", async () => {
    render(<CRMPanel standalone />);

    // Les deux activités sont bien rendues : sans cette attente, l'absence de
    // « Contact inconnu » ne prouverait rien (un fil vide la garantit aussi).
    await waitFor(() => expect(screen.getByText('Note prise en conversation')).toBeInTheDocument());
    expect(screen.getByText('Relance envoyée')).toBeInTheDocument();

    expect(screen.getByText('Alice Martin')).toBeInTheDocument();
    expect(screen.getByText('Jean Dupont')).toBeInTheDocument();
    expect(screen.queryByText('Contact inconnu')).toBeNull();
  });

  it('distingue une activité sans contact d’une référence à un contact inconnu', async () => {
    const api = await import('../../services/api');
    vi.mocked(api.listActivities).mockResolvedValueOnce([
      { ...(ACTIVITES[0] as Record<string, unknown>), id: 'sans-contact', contact_id: null, title: 'Note sans contact' },
      { ...(ACTIVITES[1] as Record<string, unknown>), id: 'contact-absent', contact_id: 'absent', title: 'Note liée' },
    ] as never);
    render(<CRMPanel standalone />);

    await waitFor(() => expect(screen.getByText('Note sans contact')).toBeInTheDocument());
    expect(screen.getByText('Note liée')).toBeInTheDocument();
    expect(screen.getByText('Sans contact')).toBeInTheDocument();
    expect(screen.getAllByText('Contact inconnu')).toHaveLength(1);
  });

  it('le pipeline utilise le même magasin complet', async () => {
    useCRMStore.setState({ activeTab: 'pipeline' });
    render(<CRMPanel standalone />);

    await waitFor(() => expect(screen.getByText(/2 contacts/)).toBeInTheDocument());
  });
});

it('B-1062 : le nouveau contact nomme sa fermeture', async () => {
  const { fireEvent } = await import('@testing-library/react');
  render(<CRMPanel standalone />);
  fireEvent.click(screen.getByRole('button', { name: 'Nouveau contact' }));
  expect(screen.getByRole('button', { name: 'Fermer le nouveau contact' })).toBeInTheDocument();
});
it('B-1063 : le filtre expose son état', async () => {
  const { fireEvent } = await import('@testing-library/react');
  useCRMStore.setState({ activeTab: 'activities' });
  render(<CRMPanel standalone />);
  const tous = screen.getByRole('button', { name: 'Tous' });
  expect(tous).toHaveAttribute('aria-pressed', 'true');
  fireEvent.click(screen.getByRole('button', { name: 'Appel' }));
  expect(tous).toHaveAttribute('aria-pressed', 'false');
  expect(screen.getByRole('button', { name: 'Appel' })).toHaveAttribute('aria-pressed', 'true');
});
