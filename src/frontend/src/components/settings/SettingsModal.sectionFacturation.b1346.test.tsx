/**
 * B-1346 (persona Claire, cycle 13) : arrivée dans Paramètres depuis « Compléter
 * le profil de facturation », le focus se pose dans la section facturation.
 */
import { render, screen, waitFor, within } from '@testing-library/react';
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

describe('Paramètres ouverts sur la facturation (B-1346)', () => {
  it('le focus se pose dans « Profil émetteur des factures »', async () => {
    render(<SettingsModal isOpen onClose={vi.fn()} requestedTab="profile" requestedSection="facturation" />);
    const section = (await screen.findByText('Profil émetteur des factures')).closest('section') as HTMLElement;
    await waitFor(() => expect(section.contains(document.activeElement)).toBe(true));
    expect(within(section).getAllByRole('textbox')).toContain(document.activeElement);
  });
});
