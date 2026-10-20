import { useState } from 'react';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { SettingsModal } from './SettingsModal';
import { FOURNISSEURS } from '../../lib/catalogueModeles';
import * as api from '../../services/api';

// Observer l'état initial, masqué par le squelette, sans modifier les hooks.
vi.mock('react', async (importOriginal) => {
  const react = await importOriginal<typeof import('react')>();
  return { ...react, useState: vi.fn(react.useState) };
});

vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  getApiKeysWithCorrupted: vi.fn().mockResolvedValue({ keys: {}, corrupted: [] }),
  getLLMConfig: vi.fn(),
  getPreferences: vi.fn().mockResolvedValue({}),
  getStats: vi.fn().mockResolvedValue(null),
  getProfile: vi.fn().mockResolvedValue(null),
  getWorkingDirectory: vi.fn().mockResolvedValue({ path: null, exists: false }),
  getOllamaStatus: vi.fn().mockResolvedValue(null),
  getSystemResources: vi.fn().mockResolvedValue(null),
  hasGroqKey: vi.fn().mockResolvedValue(false),
  getWebSearchStatus: vi.fn().mockResolvedValue({ enabled: true, providers: {}, description: '' }),
}));

const defaut = FOURNISSEURS.find((p) => p.id === 'anthropic')!.models[0].id;

afterEach(cleanup);
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.getLLMConfig).mockRejectedValue(new Error('lecture indisponible'));
});

describe('R1-9b : même défaut généré que la mise en route', () => {
  it('initialise le modèle depuis le catalogue dès le premier rendu', () => {
    render(<SettingsModal isOpen={false} onClose={vi.fn()} requestedTab="ai" />);

    const etats = vi.mocked(useState).mock.results.map((resultat) => resultat.value?.[0]);
    expect(etats).toContain(defaut);
  });

  it('replie sur le défaut du catalogue si la lecture échoue', async () => {
    render(<SettingsModal isOpen onClose={vi.fn()} requestedTab="ai" />);

    expect(await screen.findByLabelText('Modèle')).toHaveValue(defaut);
    expect(screen.getByTestId('settings-load-warning')).toHaveTextContent('configuration IA');
  });

  it('conserve un modèle enregistré différent du défaut', async () => {
    vi.mocked(api.getLLMConfig).mockResolvedValue({
      provider: 'anthropic', model: 'claude-sonnet-4-6', available_models: [], available: true,
    });
    render(<SettingsModal isOpen onClose={vi.fn()} requestedTab="ai" />);

    expect(await screen.findByLabelText('Modèle')).toHaveValue('claude-sonnet-4-6');
  });
});
