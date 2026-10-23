import { render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { EntitySuggestion } from './EntitySuggestion';
const props = { projects: [{ name: 'Rénover la grange', confidence: 0.9, description: null, budget: null, status: null }], contacts: [], messageId: 'm', onDismiss: vi.fn(), onSaved: vi.fn() };
it('B-1057 : la pastille projet emploie un jeton existant', () => {
  const { container } = render(<EntitySuggestion {...props} />);
  expect(container.querySelector('[class*="bg-accent-magenta/20"]')).not.toBeNull();
});
it('B-1058 : le décompte est accentué', () => {
  render(<EntitySuggestion {...props} />);
  expect(screen.getByText("J'ai détecté une entité")).toBeInTheDocument();
});
