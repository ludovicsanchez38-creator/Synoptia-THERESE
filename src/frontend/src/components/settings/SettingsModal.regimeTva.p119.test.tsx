/**
 * P-119 (persona Claire, cycle 13) : aucun écran ne permettait de déclarer la
 * franchise de TVA ; la mention légale ne pouvait donc pas s'imprimer. Le
 * profil de facturation porte « Régime de TVA », lu et renvoyé tel quel.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import * as api from '../../services/api';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { SettingsModal } from './SettingsModal';
import { usePersonalisationStore } from '../../stores/personalisationStore';

const profil = vi.hoisted(() => ({
  name: 'Claire Exemple', nickname: '', company: 'Claire Exemple Coaching', role: '',
  email: '', location: '', address: '8 place de la Démonstration, 69002 Lyon',
  siren: '', tva_intra: '', siret: '99988877900009', code_ape: '', nda: '', context: '', regime_tva: 'franchise',
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
  vi.mocked(api.setProfile).mockClear();
});

describe('P-119 : le régime de TVA se déclare dans le profil', () => {
  it('le régime lu s’affiche, se change et part à l’enregistrement', async () => {
    render(<SettingsModal isOpen onClose={vi.fn()} />);
    const regime = (await screen.findByLabelText('Régime de TVA')) as HTMLSelectElement;
    await waitFor(() => expect(regime.value).toBe('franchise'));
    fireEvent.change(regime, { target: { value: 'exoneration_formation' } });
    const bouton = await screen.findByTestId('settings-save-btn');
    await waitFor(() => expect(bouton).not.toBeDisabled());
    fireEvent.click(bouton);
    await waitFor(() => expect(api.setProfile).toHaveBeenCalled());
    expect(vi.mocked(api.setProfile).mock.calls[0][0]).toMatchObject({ regime_tva: 'exoneration_formation' });
  });
});
