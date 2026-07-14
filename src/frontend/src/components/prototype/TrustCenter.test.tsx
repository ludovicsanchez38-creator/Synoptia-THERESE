import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { TrustCenter } from './CapabilityCenter';

describe('TrustCenter', () => {
  it('décrit exactement le stockage et ouvre les réglages réels', () => {
    const onOpenPrivacy = vi.fn();
    const onOpenAdvanced = vi.fn();
    render(
      <TrustCenter
        onClose={vi.fn()}
        onOpenPrivacy={onOpenPrivacy}
        onOpenAdvanced={onOpenAdvanced}
      />,
    );

    expect(screen.getByText(/Données métier conservées localement/)).toBeInTheDocument();
    expect(screen.getByText(/secrets protégés par le trousseau système/)).toBeInTheDocument();
    expect(screen.queryByText('Stockage local chiffré. Sources affichées dans chaque résultat.')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Confidentialité' }));
    fireEvent.click(screen.getByRole('button', { name: 'Réglages avancés' }));

    expect(onOpenPrivacy).toHaveBeenCalledTimes(1);
    expect(onOpenAdvanced).toHaveBeenCalledTimes(1);
  });
});
