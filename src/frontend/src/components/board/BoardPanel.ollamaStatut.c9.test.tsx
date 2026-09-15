/**
 * B-842 (cycle 9) : le Board sondait Ollama par un `fetch` direct vers
 * `http://localhost:11434/api/tags`, en contournant le moteur. Un Ollama
 * configuré sur une autre adresse (préférence `base_url`) était déclaré absent
 * et le mode souverain restait grisé, alors que Réglages le voyait très bien.
 * Le Board passe désormais par `api.getOllamaStatus()` comme le reste de l'app.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({
  streamDeliberation: vi.fn(),
  listBoardDecisions: vi.fn().mockResolvedValue([]),
  getBoardDecision: vi.fn(),
  deleteBoardDecision: vi.fn(),
  getOllamaStatus: vi.fn(),
}));
vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...reel, ...apiMocks };
});
vi.mock('../../lib/consent', () => ({ hasCloudConsent: () => true }));

import { BoardPanel } from './BoardPanel';

const fetchDirect = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  // Le témoin : un Ollama joignable seulement par le moteur (autre adresse).
  apiMocks.getOllamaStatus.mockResolvedValue({
    available: true,
    base_url: 'http://192.168.1.20:11434',
    models: [
      { name: 'mistral-nemo:12b', size: 7_000_000_000, modified_at: null, digest: null },
      { name: 'qwen2.5:3b', size: 2_000_000_000, modified_at: null, digest: null },
    ],
    error: null,
  });
  // Un fetch direct sur localhost échoue, comme sur un poste sans Ollama local.
  fetchDirect.mockRejectedValue(new TypeError('Failed to fetch'));
  vi.stubGlobal('fetch', fetchDirect);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('B-842 : le Board interroge Ollama par le moteur', () => {
  it('propose le mode souverain et les modèles vus par le moteur, sans fetch direct', async () => {
    render(<BoardPanel isOpen onClose={vi.fn()} />);

    const souverain = await screen.findByRole('button', { name: /Souverain/ });
    await waitFor(() => expect(apiMocks.getOllamaStatus).toHaveBeenCalled());
    await waitFor(() => expect(souverain).not.toBeDisabled());
    fireEvent.click(souverain);

    const selecteurs = await screen.findAllByRole('combobox', { name: /Modèle du conseiller/ });
    expect(selecteurs.length).toBeGreaterThan(0);
    const options = Array.from(selecteurs[0].querySelectorAll('option')).map((o) => o.value);
    expect(options).toEqual(['qwen2.5:3b', 'mistral-nemo:12b']);

    const appelsDirects = fetchDirect.mock.calls.filter(([url]) => String(url).includes('11434'));
    expect(appelsDirects).toEqual([]);
  });
});
