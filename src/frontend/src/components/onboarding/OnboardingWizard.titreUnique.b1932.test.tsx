/**
 * B-1932 : le dialogue a déjà un h1, « Configuration initiale de Thérèse ».
 * L'accueil et le récapitulatif en ajoutent un second.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('@tauri-apps/api/window', () => ({
  getCurrentWindow: () => ({ close: vi.fn(), minimize: vi.fn(), toggleMaximize: vi.fn() }),
}));
vi.mock('../../services/api', () => ({
  getProfile: vi.fn().mockResolvedValue({ name: 'Gérard', display_name: 'Gérard' }),
  getLLMConfig: vi.fn().mockResolvedValue({ provider: 'ollama', model: 'qwen3:8b', available: true }),
  getWorkingDirectory: vi.fn().mockResolvedValue({ path: '/tmp/dossier', exists: true }),
  completeOnboarding: vi.fn().mockResolvedValue(undefined),
}));

import { CompleteStep } from './CompleteStep';
import { OnboardingWizard } from './OnboardingWizard';

describe('un seul titre de niveau 1 dans la mise en route (B-1932)', () => {
  it('l’accueil laisse le titre du dialogue seul au niveau 1', () => {
    render(<OnboardingWizard isOpen onComplete={vi.fn()} />);
    const titres = screen.getAllByRole('heading', { level: 1 });
    expect(titres).toHaveLength(1);
    expect(titres[0]).toHaveAccessibleName('Configuration initiale de Thérèse');
    expect(screen.getByRole('heading', { level: 2, name: 'Bienvenue sur THÉRÈSE' })).toBeInTheDocument();
  });

  it('le récapitulatif est un titre de niveau 2', async () => {
    render(<CompleteStep onComplete={vi.fn()} onBack={vi.fn()} />);
    const titre = await screen.findByRole('heading', { name: "C'est parti !" });
    expect(titre.tagName).toBe('H2');
  });
});

it('P-006 : un exemple métier est lisible dès l’accueil du parcours', () => {
  render(<OnboardingWizard isOpen onComplete={vi.fn()} />);
  const accueil = screen.getByTestId('onboarding-step-0');
  expect(accueil).toHaveTextContent(/Préparer une relance pour un devis resté sans réponse/);
  expect(screen.getByRole('button', { name: 'Commencer la configuration' })).toBeEnabled();
});
