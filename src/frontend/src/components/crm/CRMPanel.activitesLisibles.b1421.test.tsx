/**
 * B-1421 (tri de la couverture écran P-145, 25/09) : l'onglet « Activités »
 * du Pipeline avait son propre rendu, resté hors de B-1353 et B-1385 : il
 * affichait le type brut (« score_change »), « Raison: update_email » et
 * « Changement de stage ». Il passe par la présentation commune.
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
        type: 'score_change',
        title: 'Score: 50 -> 85',
        description: 'Raison: update_email',
        extra_data: '{"old_score": 50, "new_score": 85, "reason": "update_email"}',
        created_at: '2026-09-01T11:00:00',
      },
      {
        id: 'a-2',
        contact_id: 'c-pipeline',
        type: 'stage_change',
        title: 'Stage: contact -> discovery',
        description: 'Stage changed from contact to discovery',
        extra_data: '{"old_stage": "contact", "new_stage": "discovery"}',
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

describe('B-1421 : le fil des activités parle français', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useCRMStore.setState({ projects: [], activeTab: 'activities' });
    useContactsStore.setState({ contacts: [], selectedContactId: null, truncated: false });
  });

  it('un recalcul de score se lit comme dans la fiche', async () => {
    render(<CRMPanel standalone />);
    await waitFor(() => expect(screen.getByText('Score recalculé : 50 → 85')).toBeInTheDocument());
    expect(screen.getByText('Motif : fiche modifiée')).toBeInTheDocument();
    expect(screen.queryByText(/score_change/i)).toBeNull();
    expect(screen.queryByText(/Raison:/)).toBeNull();
  });

  it("un changement d'étape nomme les étapes, jamais le stage", async () => {
    render(<CRMPanel standalone />);
    await waitFor(() => expect(screen.getByText('Étape : Contact → Découverte')).toBeInTheDocument());
    expect(screen.queryByText(/stage/i)).toBeNull();
  });
});
