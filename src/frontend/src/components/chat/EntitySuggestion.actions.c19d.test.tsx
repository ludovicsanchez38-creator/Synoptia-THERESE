import { render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { EntitySuggestion } from './EntitySuggestion';
it('B-1061 : les actions et leur confiance nomment leur entité', () => {
  render(<EntitySuggestion projects={[{ name: 'Rénover la grange', confidence: 0.9, description: null, budget: null, status: null }]} contacts={[]} messageId="m" onDismiss={vi.fn()} onSaved={vi.fn()} />);
  const sauver = screen.getByRole('button', { name: 'Sauvegarder Rénover la grange' });
  expect(sauver).toHaveAttribute('type', 'button');
  expect(sauver).toHaveAccessibleDescription('Confiance pour Rénover la grange : 90 %');
  expect(screen.getByRole('button', { name: 'Ignorer Rénover la grange' })).toHaveAttribute('type', 'button');
});
