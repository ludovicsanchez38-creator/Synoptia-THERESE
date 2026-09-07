/** B-611 (Jean, c4) : la mise en route annonçait « ~/.therese/ » en dur, même quand le dossier réel est ailleurs. */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ProfileStep } from './ProfileStep';

const apiMocks = vi.hoisted(() => ({
  setProfile: vi.fn(),
  importClaudeMd: vi.fn(),
  getConfigStats: vi.fn().mockResolvedValue({ data_dir: '/tmp/therese-demo-c4' }),
}));

vi.mock('../../services/api', () => apiMocks);

describe('ProfileStep : le dossier annoncé est celui qui est utilisé', () => {
  it('affiche le dossier de données rendu par le moteur', async () => {
    render(<ProfileStep onNext={vi.fn()} onBack={vi.fn()} />);
    expect(await screen.findByText(/\/tmp\/therese-demo-c4/)).toBeInTheDocument();
    expect(screen.queryByText(/~\/\.therese\//)).not.toBeInTheDocument();
  });
});
