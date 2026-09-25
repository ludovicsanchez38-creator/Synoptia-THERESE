/** B-1416 : le formulaire de contact disait « Stage » ; l'écran, l'export et l'import disent « Étape ». */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useCRMStore } from '../../stores/crmStore';
import { useContactsStore } from '../../stores/contactsStore';

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

describe('B-1416 : le champ d’étape du formulaire de contact', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useCRMStore.setState({ projects: [], activeTab: 'pipeline' });
    useContactsStore.setState({ contacts: [], selectedContactId: null, truncated: false });
  });

  it('se nomme « Étape »', async () => {
    render(<CRMPanel standalone />);
    fireEvent.click(await screen.findByRole('button', { name: /Nouveau contact/ }));
    expect(screen.getByLabelText('Étape')).toBeInTheDocument();
    expect(screen.queryByLabelText('Stage')).toBeNull();
  });
});
