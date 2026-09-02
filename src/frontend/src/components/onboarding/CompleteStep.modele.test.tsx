/**
 * B-243 - le récapitulatif nomme le modèle réellement enregistré.
 *
 * Constat du 02/09/2026 (persona A3 Léa, reproduction RP18c) : l'étape 6 de la
 * mise en route affichait « mistral / mistral-medium » pour un
 * mistral-medium-latest enregistré. La valeur était tronquée à ses deux
 * premiers segments (`model.split('-').slice(0, 2).join('-')`), ce qui
 * fabrique un identifiant qui n'existe dans aucune liste : « claude-opus-4-8 »
 * devenait « claude-opus » et le récapitulatif perdait la version.
 *
 * C'est le seul écran de confirmation avant la fin de la mise en route : il
 * doit dire ce qui part au serveur, pas une abréviation inventée.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { CompleteStep } from './CompleteStep';

vi.mock('../../services/api', () => ({
  getProfile: vi.fn().mockResolvedValue(null),
  getLLMConfig: vi.fn().mockResolvedValue(null),
  getWorkingDirectory: vi.fn().mockResolvedValue({ path: null, exists: false }),
  completeOnboarding: vi.fn().mockResolvedValue(undefined),
}));

async function rendreAvecModele(provider: string, model: string) {
  const api = await import('../../services/api');
  vi.mocked(api.getLLMConfig).mockResolvedValue({
    provider,
    model,
    available: true,
  } as Awaited<ReturnType<typeof api.getLLMConfig>>);
  render(<CompleteStep onComplete={vi.fn()} onBack={vi.fn()} />);
}

describe('B-243 - le récapitulatif nomme le modèle enregistré', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('« mistral-medium-latest » s’affiche en entier', async () => {
    await rendreAvecModele('mistral', 'mistral-medium-latest');

    expect(await screen.findByText('mistral / mistral-medium-latest')).toBeInTheDocument();
    expect(screen.queryByText('mistral / mistral-medium')).toBeNull();
  });

  it('la version d’un modèle Claude reste visible', async () => {
    await rendreAvecModele('anthropic', 'claude-opus-4-8');

    const ligne = await screen.findByText(/claude-opus/);
    expect(
      ligne.textContent,
      'la version « 4-8 » a disparu du récapitulatif',
    ).toContain('claude-opus-4-8');
  });

  it('« gpt-5.6-luna » garde sa variante, pas seulement sa version', async () => {
    await rendreAvecModele('openai', 'gpt-5.6-luna');

    expect(await screen.findByText('openai / gpt-5.6-luna')).toBeInTheDocument();
  });
});
