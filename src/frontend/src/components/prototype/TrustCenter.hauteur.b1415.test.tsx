/**
 * B-1415 (contrôle Chrome de P-118, cycle 13) : avec la ligne d'état et les
 * rubriques en phrases, le panneau mesurait 901 px dans une fenêtre de 800,
 * en `overflow-hidden` : « Confidentialité » et « Paramètres » sortaient de
 * l'écran. jsdom ne mesure pas : le test garde la structure (panneau borné
 * à la fenêtre, corps défilant, en-tête et pied fixes), Chrome mesure.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  getLLMConfig: vi.fn().mockResolvedValue({ provider: 'ollama', model: 'qwen3:8b', available: true, available_models: [] }),
  getWebSearchStatus: vi.fn().mockResolvedValue({ enabled: true, providers: { gemini: '', others: '' }, description: '' }),
}));

import { TrustCenter } from './CapabilityCenter';

describe('B-1415 : le Centre de confiance tient dans la fenêtre', () => {
  it('panneau borné à la hauteur de la fenêtre, corps défilant, boutons hors du corps', async () => {
    render(<TrustCenter onClose={vi.fn()} onOpenPrivacy={vi.fn()} onOpenAdvanced={vi.fn()} />);
    const panneau = screen.getByRole('dialog', { name: 'Centre de confiance' });
    expect(panneau.className).toMatch(/max-h-\[calc\(100dvh-/);
    expect(panneau.className).toMatch(/\bflex-col\b/);
    const corps = screen.getByTestId('confiance-corps');
    expect(corps.className).toMatch(/\boverflow-y-auto\b/);
    expect(corps.className).toMatch(/\bmin-h-0\b/);
    expect(corps).toContainElement(await screen.findByTestId('confiance-etat-actuel'));
    expect(corps).not.toContainElement(screen.getByRole('button', { name: 'Paramètres' }));
  });
});
