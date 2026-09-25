/**
 * B-1347 (persona Claire, cycle 13) : l'enregistrement de la facturation
 * n'était confirmé nulle part de visible.
 *
 * Claire remplit « Profil émetteur des factures », en bas de la rubrique, et
 * clique « Enregistrer » au pied de la modale. La confirmation « Profil
 * enregistré » s'affichait dans la carte d'identité, en haut, hors de la zone
 * défilante visible. Elle s'affiche désormais au pied, à côté du bouton, là où
 * le regard se trouve, et une seule fois (une double région `status` ferait
 * annoncer deux fois le même message).
 */
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { SettingsModal } from './SettingsModal';
import { usePersonalisationStore } from '../../stores/personalisationStore';

const profil = vi.hoisted(() => ({
  name: 'Claire Exemple', nickname: '', company: 'Claire Exemple Coaching', role: '',
  email: '', location: '', address: '8 place de la Démonstration, 69002 Lyon',
  siren: '', tva_intra: '', siret: '99988877900009', code_ape: '', nda: '', context: '',
}));

vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  getApiKeysWithCorrupted: vi.fn().mockResolvedValue({ keys: {}, corrupted: [], sources: {} }),
  getLLMConfig: vi.fn().mockResolvedValue({
    provider: 'anthropic', model: 'claude-sonnet-4-6', available_models: [], effort: 'auto',
  }),
  setLLMConfig: vi.fn().mockResolvedValue({}),
  getPreferences: vi.fn().mockResolvedValue({}),
  getStats: vi.fn().mockResolvedValue(null),
  getProfile: vi.fn().mockResolvedValue(profil),
  setProfile: vi.fn().mockResolvedValue(profil),
  getBillingProfileStatus: vi.fn().mockResolvedValue({ is_complete: true, missing: [] }),
  getWorkingDirectory: vi.fn().mockResolvedValue({ path: null, exists: false }),
  getOllamaStatus: vi.fn().mockResolvedValue(null),
  getSystemResources: vi.fn().mockResolvedValue(null),
  hasGroqKey: vi.fn().mockResolvedValue(false),
  getWebSearchStatus: vi.fn().mockResolvedValue({
    enabled: true,
    providers: { gemini: 'indisponible', others: 'indisponible' },
    description: '',
  }),
}));

beforeEach(() => {
  usePersonalisationStore.setState({ uxMode: 'contributeur' });
});

describe('confirmation d\'enregistrement du profil (B-1347)', () => {
  it('« Profil enregistré » s\'affiche au pied, à côté du bouton, une seule fois', async () => {
    render(<SettingsModal isOpen onClose={vi.fn()} />);
    const bouton = await screen.findByTestId('settings-save-btn');
    await waitFor(() => expect(bouton).not.toBeDisabled());

    fireEvent.click(bouton);

    const pied = bouton.parentElement as HTMLElement;
    expect(await within(pied).findByRole('status')).toHaveTextContent('Profil enregistré');
    expect(screen.getAllByText('Profil enregistré')).toHaveLength(1);
  });
});
