/**
 * B-1345 (persona Claire, cycle 13) : « ne quittent jamais ta machine » était
 * une promesse absolue, écrite en 12 px, et fausse dès qu'un service en ligne
 * est choisi à l'étape suivante : le profil est injecté dans le prompt système
 * quel que soit le fournisseur (`llm.py`, `_get_system_prompt_with_identity`).
 * La phrase dit désormais les deux cas, en 14 px.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ProfileStep } from './ProfileStep';

vi.mock('../../services/api', () => ({
  setProfile: vi.fn(),
  importClaudeMd: vi.fn(),
  getConfigStats: vi.fn().mockResolvedValue({ data_dir: '/tmp/therese-demo-c13/data' }),
}));

describe('ProfileStep : la promesse de stockage est vraie (B-1345)', () => {
  it('ne promet plus que le profil ne quitte jamais la machine', async () => {
    render(<ProfileStep onNext={vi.fn()} onBack={vi.fn()} />);
    await screen.findByText(/\/tmp\/therese-demo-c13\/data/);
    expect(screen.queryByText(/ne quittent jamais/)).not.toBeInTheDocument();
  });

  it('dit ce qui se passe avec un service en ligne, en 14 px', async () => {
    render(<ProfileStep onNext={vi.fn()} onBack={vi.fn()} />);
    const phrase = await screen.findByText(/avec un service en ligne/);
    expect(phrase.textContent).toMatch(/modèle local/);
    expect(phrase.className).toContain('text-sm');
    expect(phrase.className).not.toContain('text-xs');
  });
});
