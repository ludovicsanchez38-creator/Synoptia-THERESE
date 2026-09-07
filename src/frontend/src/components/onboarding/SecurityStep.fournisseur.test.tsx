/**
 * B-541 (cycle 4) : la case « Je consens » restait cochée quand on revenait en
 * arrière changer de fournisseur : l'accord pouvait être enregistré pour un
 * fournisseur avec une case cochée pour un autre.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { SecurityStep } from './SecurityStep';

describe('SecurityStep : la case de consentement suit le fournisseur affiché (B-541)', () => {
  it('changer de fournisseur décoche la case et désactive « continuer »', () => {
    const { rerender } = render(<SecurityStep provider="mistral" onNext={vi.fn()} onBack={vi.fn()} />);
    fireEvent.click(screen.getByRole('checkbox'));
    expect(screen.getByRole('checkbox')).toBeChecked();
    expect(screen.getByTestId('onboarding-next-btn')).toBeEnabled();

    rerender(<SecurityStep provider="anthropic" onNext={vi.fn()} onBack={vi.fn()} />);

    expect(screen.getByRole('checkbox')).not.toBeChecked();
    expect(screen.getByTestId('onboarding-next-btn')).toBeDisabled();
  });
});
