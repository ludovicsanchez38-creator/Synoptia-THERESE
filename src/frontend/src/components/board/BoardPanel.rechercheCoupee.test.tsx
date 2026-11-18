import { act, fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({ streamDeliberation: vi.fn() }));

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    ...mocks,
    listBoardDecisions: vi.fn().mockResolvedValue([]),
    listAdvisors: vi.fn().mockResolvedValue([]),
    getOllamaStatus: vi.fn().mockResolvedValue({ available: false, models: [] }),
  };
});
vi.mock('../../lib/modeDuBoardParDefaut', () => ({ modeDuBoardParDefaut: async () => 'cloud' }));
vi.mock('../../lib/consent', () => ({ hasCloudConsent: () => true, grantCloudConsent: vi.fn() }));

import { BoardPanel } from './BoardPanel';

describe('Recherche web du Board classique', () => {
  it('garde le refus visible après le démarrage des conseillers', async () => {
    let terminer = () => {};
    mocks.streamDeliberation.mockImplementation(async function* () {
      yield { type: 'web_search_start', content: 'Recherche en cours' };
      yield { type: 'web_search_done', content: 'Recherche web coupée. Réactive-la dans Paramètres > Services.' };
      yield { type: 'advisor_start', role: 'analyst', name: "L'Analyste", content: '' };
      yield { type: 'advisor_chunk', role: 'analyst', content: 'Avis témoin' };
      await new Promise<void>((resolve) => { terminer = resolve; });
    });

    render(<BoardPanel isOpen onClose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Ta question stratégique'), {
      target: { value: 'Faut-il lancer un pilote maintenant ?' },
    });
    fireEvent.click(screen.getByTestId('board-submit-btn'));
    fireEvent.click(await screen.findByRole('button', { name: /Confirmer et lancer/ }));

    expect(await screen.findByText('Avis témoin')).toBeInTheDocument();
    expect(screen.getByText('Recherche web coupée. Réactive-la dans Paramètres > Services.')).toBeInTheDocument();
    await act(async () => { terminer(); });
  });
});
