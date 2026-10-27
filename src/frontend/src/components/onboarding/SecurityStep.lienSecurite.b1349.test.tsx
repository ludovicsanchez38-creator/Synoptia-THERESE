/**
 * B-1349 (audit bêta du 27/10/2026) : « En savoir plus sur la sécurité » menait à
 * https://synoptia.fr/therese/securite, qui répond 404. Le lien vise désormais la politique
 * de sécurité du dépôt public (SECURITY.md, en français), vérifiée en ligne le 27/10.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { LIEN_SECURITE, SecurityStep } from './SecurityStep';

describe('SecurityStep : le lien sécurité mène à une page qui existe', () => {
  it('pointe vers SECURITY.md du dépôt public, jamais vers l’ancienne page du site', () => {
    render(<SecurityStep provider="ollama" onNext={vi.fn()} onBack={vi.fn()} />);
    const lien = screen.getByRole('link', { name: /En savoir plus sur la sécurité/ });

    expect(lien).toHaveAttribute('href', LIEN_SECURITE);
    expect(LIEN_SECURITE).toMatch(/^https:\/\/github\.com\/ludovicsanchez38-creator\/Synoptia-THERESE\/blob\/main\/SECURITY\.md$/);
    expect(lien.getAttribute('href')).not.toContain('synoptia.fr/therese/securite');
    expect(lien).toHaveAttribute('target', '_blank');
    expect(lien).toHaveAttribute('rel', expect.stringContaining('noopener'));
  });
});
