/**
 * Cycle 6, lecteur #162 (LLMStep / OnboardingWizard / CompleteStep) : quand
 * « Configurer plus tard » suit un enregistrement, l'effacement au serveur
 * était tenté deux fois et son échec avalé aux deux endroits ; le
 * récapitulatif affichait « À configurer plus tard » sans réserve alors que
 * le serveur gardait un fournisseur actif.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { CompleteStep } from './CompleteStep';

vi.mock('../../services/api', () => ({
  getProfile: vi.fn().mockResolvedValue(null),
  getLLMConfig: vi.fn().mockResolvedValue({ provider: 'ollama', model: 'qwen:14b', available: true }),
  getWorkingDirectory: vi.fn().mockResolvedValue(null),
  completeOnboarding: vi.fn().mockResolvedValue(undefined),
}));

describe('#162 : le récapitulatif dit quand l’ancien réglage n’a pas pu être effacé', () => {
  it('« plus tard » avec un service conservé nomme le fournisseur qui reste actif', async () => {
    render(<CompleteStep onComplete={vi.fn()} onBack={vi.fn()} llmSkipped serviceIaConserve="ollama" />);
    const ligne = await screen.findByTestId('summary-service-d-ia');
    expect(ligne).toHaveTextContent(/À configurer plus tard/);
    expect(ligne).toHaveTextContent(/Ollama local/);
    expect(ligne).toHaveTextContent(/n’a pas pu être effacé/);
    expect(ligne).toHaveAttribute('data-configured', 'false');
  });
});
