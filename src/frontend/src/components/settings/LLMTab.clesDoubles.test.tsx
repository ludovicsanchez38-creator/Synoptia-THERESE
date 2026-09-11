/**
 * B-753 - « two children with the same key » dans le sélecteur de modèle.
 *
 * React avertissait au montage de l'écran Paramètres sur `claude-fable-5` et
 * `claude-sonnet-5`. La cause est en amont du composant : la liste de repli
 * de `FOURNISSEURS` porte ces identifiants deux fois, `ModelSelector` en fait
 * autant d'options, et `Select` pose `key={opt.value}`. Deux lignes
 * identiques dans la liste déroulante, dont une seule est atteignable.
 *
 * Le premier rendu se sert de cette liste de repli, avant que la promesse du
 * catalogue backend ne revienne : l'avertissement sort donc dès le montage,
 * sans avoir à simuler le réseau.
 */

import { render } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { LLMTab } from './LLMTab';
import { _viderLeCache } from '../../lib/catalogueModeles';

function monter(selectedProvider: 'anthropic' | 'grok', selectedModel: string) {
  render(
    <LLMTab
      selectedProvider={selectedProvider}
      selectedModel={selectedModel}
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
}

describe('B-753 - le sélecteur de modèle ne pose pas deux fois la même clé', () => {
  beforeEach(() => {
    _viderLeCache();
  });

  it('Anthropic : aucun avertissement de clé en double au montage', () => {
    const journal = vi.spyOn(console, 'error').mockImplementation(() => {});
    monter('anthropic', 'claude-opus-5');

    const clesDoubles = journal.mock.calls.filter((appel) =>
      appel.some((argument) => typeof argument === 'string' && argument.includes('same key')),
    );
    expect(clesDoubles).toEqual([]);
    journal.mockRestore();
  });

  it('Grok : aucun avertissement de clé en double au montage', () => {
    const journal = vi.spyOn(console, 'error').mockImplementation(() => {});
    monter('grok', 'grok-4.6');

    const clesDoubles = journal.mock.calls.filter((appel) =>
      appel.some((argument) => typeof argument === 'string' && argument.includes('same key')),
    );
    expect(clesDoubles).toEqual([]);
    journal.mockRestore();
  });
});
