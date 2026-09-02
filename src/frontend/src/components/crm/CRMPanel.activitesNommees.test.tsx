/**
 * B-205 : le fil d'activités du Pipeline affichait « Contact inconnu ».
 *
 * Le fil charge les activités de TOUS les contacts (`listActivities` sans
 * filtre) tandis que l'annuaire qui sert à les nommer, lui, recevait la vue
 * filtrée du pipeline (`allContacts.filter((c) => !!c.source)`). Une activité
 * d'un contact créé par le chemin Contacts (source = null) s'affichait donc
 * sans jamais pouvoir être nommée : la vue montre une ligne qu'elle s'interdit
 * ensuite de nommer.
 *
 * Le filtre du pipeline lui-même est délibéré et documenté : il n'est pas en
 * cause, et le test ne le remet pas en question — il n'exige QUE la cohérence
 * entre ce qui est affiché et ce qui est nommé.
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
      // Chemin Contacts : aucune source, donc absent de la vue pipeline.
      { ...base, id: 'c-memoire', first_name: 'Jean', last_name: 'Dupont', source: null },
      // Chemin pipeline : une source, donc présent dans la vue.
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

  it('le pipeline reste filtré sur les contacts à source', async () => {
    // Contre-épreuve : nommer depuis le magasin complet ne doit PAS élargir la
    // liste du pipeline, filtre délibéré (CRMPanel.tsx:41-42).
    useCRMStore.setState({ activeTab: 'pipeline' });
    render(<CRMPanel standalone />);

    await waitFor(() => expect(screen.getByText(/1 contact/)).toBeInTheDocument());
  });
});
