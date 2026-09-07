/**
 * B-199 (cycle 4) : après « Configurer plus tard » à l'étape du service d'IA,
 * le récapitulatif affichait quand même « openai / gpt-5.6 » avec une coche,
 * parce qu'il relisait la configuration par défaut du serveur au lieu du
 * choix fait dans l'assistant.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import * as api from '../../services/api';
import { CompleteStep } from './CompleteStep';

vi.mock('../../services/api', () => ({
  getProfile: vi.fn().mockResolvedValue(null),
  getLLMConfig: vi.fn().mockResolvedValue(null),
  getWorkingDirectory: vi.fn().mockResolvedValue(null),
  completeOnboarding: vi.fn().mockResolvedValue(undefined),
}));

describe('CompleteStep : le récapitulatif respecte « Configurer plus tard » (B-199)', () => {
  it('n’affiche pas le fournisseur par défaut du serveur quand l’étape a été passée', async () => {
    vi.mocked(api.getLLMConfig).mockResolvedValue({
      provider: 'openai', model: 'gpt-5.6', available: true,
    } as unknown as api.LLMConfig);

    render(<CompleteStep onComplete={vi.fn()} onBack={vi.fn()} llmSkipped />);

    const ligne = await screen.findByTestId('summary-service-d-ia');
    expect(ligne).toHaveTextContent('À configurer plus tard');
    expect(ligne).not.toHaveTextContent('openai');
    expect(ligne).toHaveAttribute('data-configured', 'false');
  });

  it('affiche le fournisseur configuré quand l’étape a été faite', async () => {
    vi.mocked(api.getLLMConfig).mockResolvedValue({
      provider: 'mistral', model: 'mistral-medium-latest', available: true,
    } as unknown as api.LLMConfig);

    render(<CompleteStep onComplete={vi.fn()} onBack={vi.fn()} llmSkipped={false} />);

    const ligne = await screen.findByTestId('summary-service-d-ia');
    expect(ligne).toHaveTextContent('mistral / mistral-medium-latest');
    expect(ligne).toHaveAttribute('data-configured', 'true');
  });
});
