/**
 * B-642 (persona Nadia, c4) : le bloc de confirmation d'un lancement
 * souverain expliquait les frais du mode cloud (« Jusqu'à six appels LLM
 * peuvent consommer des crédits API »), ce qui fait douter de ce qui part.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...reel, streamDeliberation: vi.fn(), listBoardDecisions: vi.fn().mockResolvedValue([]) };
});
vi.mock('../../lib/consent', () => ({ hasCloudConsent: () => true }));

import { BoardPanel } from './BoardPanel';

describe('B-642 : la confirmation décrit le mode réellement choisi', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ json: async () => ({ models: [{ name: 'qwen3:8b', size: 5 }] }) }));
  });

  it('en mode souverain, elle parle d’Ollama local et pas de crédits cloud', async () => {
    render(<BoardPanel isOpen onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: /Souverain/ }));
    fireEvent.change(screen.getByLabelText('Question soumise au Board'), { target: { value: 'Dois-je passer ma société en SASU cette année ?' } });
    fireEvent.click(screen.getByTestId('board-submit-btn'));
    const confirmation = await screen.findByTestId('board-confirmation');
    expect(confirmation).toHaveTextContent(/Ollama/);
    expect(confirmation).toHaveTextContent(/reste sur cette machine/i);
    expect(confirmation).not.toHaveTextContent(/crédits/i);
  });

  it('en mode cloud, elle garde l’avertissement sur les crédits', async () => {
    render(<BoardPanel isOpen onClose={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Question soumise au Board'), { target: { value: 'Dois-je passer ma société en SASU cette année ?' } });
    fireEvent.click(screen.getByTestId('board-submit-btn'));
    expect(await screen.findByTestId('board-confirmation')).toHaveTextContent(/crédits/i);
  });
});
