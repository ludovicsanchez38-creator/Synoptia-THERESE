/**
 * Lot M1 : le sélecteur des réglages nomme Mistral Large 4 et dit
 * « Préversion ». La liste servie échoue : on retombe sur le repli.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../lib/catalogueModeles', async (importOriginal) => {
  const reel = await importOriginal<typeof import('../../lib/catalogueModeles')>();
  return { ...reel, chargerCatalogue: vi.fn().mockResolvedValue(null) };
});
vi.mock('../../services/api', () => ({
  getLLMConfig: vi.fn().mockResolvedValue({ provider: 'mistral', model: 'mistral-large-latest', effort: 'auto' }),
  setLLMConfig: vi.fn(),
}));

import { LLMTab } from './LLMTab';

describe('sélecteur des réglages, lot M1', () => {
  it('propose Mistral Large 4 en préversion', async () => {
    render(
      <LLMTab
        selectedProvider="mistral"
        selectedModel="mistral-large-latest"
        apiKeys={{}}
        apiKeyInput=""
        setApiKeyInput={vi.fn()}
        showApiKey={false}
        setShowApiKey={vi.fn()}
        ollamaStatus={null}
        ollamaModels={[]}
        systemResources={null}
        saving={false}
        saved={false}
        error={null}
        setError={vi.fn()}
        onSelectProvider={vi.fn()}
        onSelectModel={vi.fn()}
        onSaveApiKey={vi.fn()}
      />,
    );
    const select = await screen.findByLabelText('Modèle');
    const libelles = Array.from(select.querySelectorAll('option')).map((o) => o.textContent);
    expect(libelles[0]).toBe('Mistral Medium 3.5 (Équilibré)');
    expect(libelles).toContain('Mistral Large 4 (Préversion)');
  });
});
