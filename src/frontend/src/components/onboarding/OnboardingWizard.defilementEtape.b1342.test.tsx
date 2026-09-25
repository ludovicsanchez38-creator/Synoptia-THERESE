/**
 * B-1342 (persona Claire, cycle 13) : l'étape Sécurité s'ouvrait défilée.
 *
 * Le conteneur défilant de l'assistant survit d'une étape à l'autre : Claire
 * avait défilé jusqu'à Ollama à l'étape Service d'IA, et l'étape suivante
 * s'ouvrait avec `scrollTop = 188`, son titre caché sous le bandeau d'étapes.
 * Chaque étape s'ouvre désormais en haut.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('@tauri-apps/api/window', () => ({
  getCurrentWindow: () => ({ close: vi.fn(), minimize: vi.fn(), toggleMaximize: vi.fn() }),
}));
vi.mock('./WelcomeStep', () => ({
  WelcomeStep: ({ onNext }: { onNext: () => void }) => <button type="button" onClick={onNext}>Étape suivante</button>,
}));
vi.mock('./ProfileStep', () => ({
  ProfileStep: ({ onNext }: { onNext: () => void }) => <button type="button" onClick={onNext}>Étape suivante</button>,
}));

import { OnboardingWizard } from './OnboardingWizard';

describe('assistant : chaque étape s’ouvre en haut (B-1342)', () => {
  it('le défilement d’une étape ne se reporte pas sur la suivante', async () => {
    render(<OnboardingWizard isOpen onComplete={vi.fn()} />);
    const conteneur = screen.getByTestId('onboarding-step-0').closest('.overflow-y-auto') as HTMLElement;
    expect(conteneur).not.toBeNull();
    conteneur.scrollTop = 188;

    fireEvent.click(screen.getByRole('button', { name: 'Étape suivante' }));

    await screen.findByTestId('onboarding-step-1');
    await waitFor(() => expect(conteneur.scrollTop).toBe(0));
  });
});
