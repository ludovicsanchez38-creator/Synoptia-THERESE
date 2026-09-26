/**
 * B-1689 (suite de B-1621, décision de Ludo du 26/09) : en démo, déplacer une
 * fiche d'étape dans le pipeline écrivait sur la vraie fiche.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useCRMStore } from '../../stores/crmStore';
import { useContactsStore } from '../../stores/contactsStore';
import { useDemoStore } from '../../stores/demoStore';
import type { Contact } from '../../services/api';

const api = vi.hoisted(() => ({ updateContactStage: vi.fn() }));
vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel, updateContactStage: api.updateContactStage,
    listProjects: vi.fn().mockResolvedValue([]), listActivities: vi.fn().mockResolvedValue([]),
  };
});
vi.mock('../../services/api/memory', async () => {
  const reel = await vi.importActual<typeof import('../../services/api/memory')>('../../services/api/memory');
  return { ...reel, listContacts: vi.fn().mockResolvedValue([]) };
});
// Le glisser-déposer de dnd-kit ne se joue pas dans jsdom : la vue rend un
// bouton qui fait ce que fait le dépôt d'une carte.
vi.mock('./PipelineView', () => ({
  PipelineView: ({ onStageChange }: { onStageChange: (id: string, etape: string) => void }) => (
    <button type="button" onClick={() => onStageChange('ct-1', 'proposition')}>Déposer en Proposition</button>
  ),
}));

import { CRMPanel } from './CRMPanel';

const marie = {
  id: 'ct-1', first_name: 'Marie', last_name: 'Lefevre', company: null, email: null, phone: null,
  notes: null, tags: null, scope: 'global', stage: 'prospect', created_at: '2026-08-01T00:00:00Z', updated_at: '2026-08-01T00:00:00Z',
} as unknown as Contact;

describe('B-1689 : en démo, le pipeline ne déplace pas la vraie fiche', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.updateContactStage.mockResolvedValue({ ...marie, stage: 'proposition' });
    useCRMStore.setState({ projects: [], activeTab: 'pipeline' });
    useContactsStore.setState({ contacts: [marie], loaded: true, loading: false, error: null, selectedContactId: null, truncated: false });
  });
  afterEach(() => useDemoStore.setState({ enabled: false } as never));

  it('en démo, le dépôt ne part pas', async () => {
    useDemoStore.setState({ enabled: true } as never);
    render(<CRMPanel standalone />);
    fireEvent.click(await screen.findByRole('button', { name: 'Déposer en Proposition' }));
    expect(api.updateContactStage).not.toHaveBeenCalled();
  });

  it('témoin : hors démo, le dépôt part', async () => {
    render(<CRMPanel standalone />);
    fireEvent.click(await screen.findByRole('button', { name: 'Déposer en Proposition' }));
    expect(api.updateContactStage).toHaveBeenCalledWith('ct-1', 'proposition');
  });
});
