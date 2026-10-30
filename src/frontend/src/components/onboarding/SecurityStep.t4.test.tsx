import { render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { SecurityStep } from './SecurityStep';

it('annonce les données que les outils peuvent lire avant l’accord', () => {
  render(<SecurityStep provider="mistral" onNext={vi.fn()} onBack={vi.fn()} />);
  const label = screen.getByRole('checkbox').closest('label');
  for (const categorie of ['mails', 'fiches contacts', 'factures', 'agenda', 'tâches', 'fichiers']) {
    expect(label).toHaveTextContent(categorie);
  }
});
