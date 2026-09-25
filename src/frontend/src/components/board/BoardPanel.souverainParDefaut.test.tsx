/**
 * Décision du 25/09 (délégation de Ludo) : Décision part en « Souverain »
 * quand le service choisi est Ollama. La recette a vu « Cloud » coché par
 * défaut avec Ollama seul configuré : une délibération vouée à l'échec, ou
 * en ligne sans l'avoir choisi.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const config = vi.hoisted(() => ({ getLLMConfig: vi.fn() }));
vi.mock('../../services/api/config', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  ...config,
}));
vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    streamDeliberation: vi.fn(),
    listBoardDecisions: vi.fn().mockResolvedValue([]),
    getOllamaStatus: vi.fn().mockResolvedValue({
      available: true, base_url: 'http://127.0.0.1:11434',
      models: [{ name: 'qwen3:8b', size: 5, modified_at: null, digest: null }], error: null,
    }),
  };
});

import { BoardPanel } from './BoardPanel';
import { BoardWorkspaceCanvas } from '../prototype/BoardConversationCard';

const idleRun = {
  status: 'idle', question: '', context: '', mode: 'cloud', phase: '', isSearchingWeb: false,
  advisors: {}, synthesis: null, decisionId: null, error: null,
} as never;

describe('Décision : Souverain par défaut quand Ollama est le service choisi', () => {
  beforeEach(() => vi.clearAllMocks());

  it('la fenêtre Décision coche Souverain', async () => {
    config.getLLMConfig.mockResolvedValue({ provider: 'ollama', model: 'qwen3:8b', available_models: [] });
    render(<BoardPanel isOpen onClose={vi.fn()} />);
    await waitFor(() => expect(screen.getByRole('button', { name: /Souverain/ })).toHaveAttribute('aria-pressed', 'true'));
  });

  it('avec un service en ligne, Cloud reste coché', async () => {
    config.getLLMConfig.mockResolvedValue({ provider: 'anthropic', model: 'claude-fable-5', available_models: [] });
    render(<BoardPanel isOpen onClose={vi.fn()} />);
    await waitFor(() => expect(config.getLLMConfig).toHaveBeenCalled());
    expect(screen.getByRole('button', { name: /Cloud/ })).toHaveAttribute('aria-pressed', 'true');
  });

  it('le canevas Décision coche Souverain', async () => {
    config.getLLMConfig.mockResolvedValue({ provider: 'ollama', model: 'qwen3:8b', available_models: [] });
    render(<BoardWorkspaceCanvas
      resource={{ status: 'ready', data: { advisors: [], decisions: [] }, error: null }} decisionResource={null}
      run={idleRun} target="new-board" onRetry={vi.fn()} onRetryDecision={vi.fn()}
      onStart={vi.fn()} onCancel={vi.fn()} onReset={vi.fn()} onOpenClassic={vi.fn()}
    />);
    await waitFor(() => expect(screen.getByRole('radio', { name: /Souverain/ })).toHaveAttribute('aria-checked', 'true'));
  });
});
