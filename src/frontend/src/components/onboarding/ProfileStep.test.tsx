import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ProfileStep } from './ProfileStep';

const apiMocks = vi.hoisted(() => ({
  setProfile: vi.fn(),
  importClaudeMd: vi.fn(),
}));

vi.mock('../../services/api', () => apiMocks);

describe('ProfileStep', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('affiche la sauvegarde réussie, bloque le double-clic puis avance', async () => {
    let resolveProfile: ((value: unknown) => void) | undefined;
    apiMocks.setProfile.mockImplementation(() => new Promise((resolve) => {
      resolveProfile = resolve;
    }));
    const onNext = vi.fn();
    render(<ProfileStep onNext={onNext} onBack={vi.fn()} />);

    fireEvent.change(screen.getByLabelText('Nom complet *'), { target: { value: 'Camille Martin' } });
    const continueButton = screen.getByTestId('onboarding-next-btn');
    fireEvent.click(continueButton);
    fireEvent.click(continueButton);

    expect(apiMocks.setProfile).toHaveBeenCalledTimes(1);
    expect(continueButton).toBeDisabled();
    expect(screen.getByText('Enregistrement en cours...')).toBeInTheDocument();

    await act(async () => {
      resolveProfile?.({ name: 'Camille Martin' });
      await Promise.resolve();
    });

    expect(screen.getByRole('status')).toHaveTextContent('Profil enregistré');
    expect(onNext).not.toHaveBeenCalled();
    act(() => vi.advanceTimersByTime(650));
    expect(onNext).toHaveBeenCalledTimes(1);
  });

  it('affiche l’échec et permet une nouvelle tentative', async () => {
    apiMocks.setProfile
      .mockRejectedValueOnce(new Error('Sauvegarde indisponible'))
      .mockResolvedValueOnce({ name: 'Camille Martin' });
    render(<ProfileStep onNext={vi.fn()} onBack={vi.fn()} />);

    fireEvent.change(screen.getByLabelText('Nom complet *'), { target: { value: 'Camille Martin' } });
    await act(async () => fireEvent.click(screen.getByTestId('onboarding-next-btn')));

    expect(screen.getByRole('alert')).toHaveTextContent('Sauvegarde indisponible');
    expect(screen.getByTestId('onboarding-next-btn')).not.toBeDisabled();
    await act(async () => fireEvent.click(screen.getByTestId('onboarding-next-btn')));
    expect(apiMocks.setProfile).toHaveBeenCalledTimes(2);
  });
});
