/**
 * B-1343 (persona Claire, cycle 13) : le pied de l'assistant changeait d'une
 * étape à l'autre, et le bouton final sortait de l'écran.
 *
 * - Étape Sécurité : pas de marge intérieure (« Retour » collé au bord du
 *   dialogue) et deux gros boutons pleine largeur, là où les autres étapes ont
 *   « Retour » discret à gauche et l'action à droite, sous un filet.
 * - Étape finale : son pied est épinglé dans une colonne `h-full`, mais
 *   l'enveloppe de l'étape n'avait pas de hauteur ; la colonne grandissait avec
 *   le contenu et « Commencer » défilait sous le bas du dialogue.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('@tauri-apps/api/window', () => ({
  getCurrentWindow: () => ({ close: vi.fn(), minimize: vi.fn(), toggleMaximize: vi.fn() }),
}));
vi.mock('./WelcomeStep', () => ({ WelcomeStep: () => <p>Bienvenue</p> }));

import { OnboardingWizard } from './OnboardingWizard';
import { SecurityStep } from './SecurityStep';

describe('assistant : un pied cohérent et toujours visible (B-1343)', () => {
  it('l’enveloppe d’une étape prend la hauteur du dialogue', () => {
    render(<OnboardingWizard isOpen onComplete={vi.fn()} />);
    expect(screen.getByTestId('onboarding-step-0').className).toContain('h-full');
  });

  it('l’étape Sécurité a la marge et le pied des autres étapes', () => {
    const { container } = render(<SecurityStep provider="ollama" onNext={vi.fn()} onBack={vi.fn()} />);
    const racine = container.firstElementChild as HTMLElement;
    expect(racine.className).toMatch(/\bpx-8\b/);
    const retour = screen.getByTestId('onboarding-prev-btn');
    const pied = retour.parentElement as HTMLElement;
    expect(pied.className).toMatch(/\bjustify-between\b/);
    expect(pied.className).toMatch(/\bborder-t\b/);
    expect(retour.className).not.toMatch(/\bflex-1\b/);
    expect(screen.getByTestId('onboarding-next-btn').className).not.toMatch(/\bflex-1\b/);
  });
});
