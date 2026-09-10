/** Cycle 6, #294 / D202 : la phrase de consentement nomme le fournisseur, pas son identifiant. */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { SecurityStep } from './SecurityStep';

describe('#294 : le consentement nomme le fournisseur', () => {
  it('avec glm, la phrase dit « Zhipu GLM » et jamais « vers glm »', () => {
    render(<SecurityStep provider="glm" onNext={vi.fn()} onBack={vi.fn()} />);
    expect(screen.getByText(/transfert de mes données vers Zhipu GLM/)).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/vers glm\b/);
  });
});
