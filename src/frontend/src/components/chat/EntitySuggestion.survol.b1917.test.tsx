/**
 * B-1917 : « Tout ignorer » porte la même couleur au repos et au survol,
 * donc le survol ne se voit pas.
 */
import { render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { EntitySuggestion } from './EntitySuggestion';

it('B-1917 : Tout ignorer change de couleur au survol', () => {
  render(
    <EntitySuggestion
      contacts={[{
        name: 'Jean Dupont',
        company: 'ACME',
        role: null,
        email: null,
        phone: null,
        confidence: 0.9,
      }]}
      projects={[]}
      messageId="m"
      onDismiss={vi.fn()}
      onSaved={vi.fn()}
    />,
  );

  const classes = screen.getByRole('button', { name: 'Tout ignorer' }).className.split(/\s+/);
  expect(classes).toContain('hover:text-text');
  expect(classes).not.toContain('hover:text-text-muted');
});
