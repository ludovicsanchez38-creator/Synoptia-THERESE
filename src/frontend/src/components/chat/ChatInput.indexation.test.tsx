/**
 * BUG-155 (27/07/2026) - Indexation d'une pièce jointe : annulation réelle.
 *
 * L'appel était émis sans délai maximal ET sans signal d'annulation : retirer
 * la pièce jointe laissait le traitement tourner côté backend, et rien ne
 * permettait de l'interrompre. Le testeur a fermé THÉRÈSE pour s'en sortir.
 *
 * BUG-158 - L'état d'indexation doit se voir (indicateur animé) et l'échec
 * doit être lisible à l'écran, pas seulement pour les lecteurs d'écran.
 */
import { act, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { useStatusStore } from '../../stores/statusStore';
import { ChatInput } from './ChatInput';

const apiMocks = vi.hoisted(() => ({
  getLLMConfig: vi.fn(),
  setLLMConfig: vi.fn(),
  streamMessage: vi.fn(),
  streamDeepResearch: vi.fn(),
  indexFile: vi.fn(),
}));

const dropMock = vi.hoisted(() => ({ onDrop: null as null | ((files: unknown[]) => Promise<void>) }));

vi.mock('../../services/api', () => ({
  ...apiMocks,
  ApiError: class ApiError extends Error {
    status = 500;
  },
}));
vi.mock('../../hooks/useGhostText', () => ({
  useGhostText: () => ({ suggestion: '', accept: vi.fn(), dismiss: vi.fn() }),
}));
vi.mock('../../hooks/useAutosave', () => ({
  useAutosave: () => ({ saveDraft: vi.fn(), restoreDraft: vi.fn(() => ''), clearDraft: vi.fn(), lastSavedAt: null }),
}));
vi.mock('../../hooks/useFileDrop', () => ({
  useFileDrop: (options: { onDrop: (files: unknown[]) => Promise<void> }) => {
    dropMock.onDrop = options.onDrop;
    return { isDragging: false };
  },
}));
vi.mock('./SlashCommandsMenu', () => ({
  SlashCommandsMenu: () => null,
  detectSlashCommand: () => false,
}));
vi.mock('./ActionChips', () => ({ ActionChips: () => null }));
vi.mock('../files/DropZone', () => ({
  InlineDropZone: () => null,
  FileChip: ({ name, onRemove }: { name: string; onRemove: () => void }) => (
    <span>
      {name}
      <button type="button" onClick={onRemove} aria-label={`Retirer ${name}`}>
        Retirer
      </button>
    </span>
  ),
}));
vi.mock('./VoiceDictationButton', () => ({ VoiceDictationButton: () => null }));

const FICHIER = { path: '/tmp/rapport.pdf', name: 'rapport.pdf', mimeType: 'application/pdf', size: 12_000_000 };

async function joindreFichier() {
  // Ne pas attendre la fin du dépôt : l'indexation peut rester en cours (c'est
  // précisément le cas testé). On laisse seulement React appliquer les états.
  await act(async () => {
    void dropMock.onDrop?.([FICHIER]);
    await Promise.resolve();
    await Promise.resolve();
  });
}

describe('ChatInput - indexation des pièces jointes', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    dropMock.onDrop = null;
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'ollama',
      model: 'gemma4-tia:latest',
      available_models: ['gemma4-tia:latest'],
      available: true,
    });
    useStatusStore.setState({ connectionState: 'connected' });
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
  });

  it('transmet un signal d’annulation à l’indexation', async () => {
    apiMocks.indexFile.mockImplementation(() => new Promise(() => {}));
    render(<ChatInput />);
    await joindreFichier();

    expect(apiMocks.indexFile).toHaveBeenCalledTimes(1);
    const signal = apiMocks.indexFile.mock.calls[0][1] as AbortSignal | undefined;
    expect(signal).toBeInstanceOf(AbortSignal);
    expect(signal?.aborted).toBe(false);
  });

  it('retirer la pièce jointe interrompt réellement l’indexation en cours', async () => {
    apiMocks.indexFile.mockImplementation(() => new Promise(() => {}));
    render(<ChatInput />);
    await joindreFichier();

    const signal = apiMocks.indexFile.mock.calls[0][1] as AbortSignal;
    expect(signal.aborted).toBe(false);

    await act(async () => {
      screen.getByLabelText('Retirer rapport.pdf').click();
    });

    expect(signal.aborted).toBe(true);
  });

  it('l’indexation en cours est signalée comme active, pas comme un bouton', async () => {
    apiMocks.indexFile.mockImplementation(() => new Promise(() => {}));
    render(<ChatInput />);
    await joindreFichier();

    const etat = screen.getByTestId('index-status-/tmp/rapport.pdf');
    expect(etat).toHaveTextContent('Indexation');
    expect(etat.querySelector('[data-testid="index-spinner"]')).not.toBeNull();
    expect(etat.tagName).not.toBe('BUTTON');
  });

  it('affiche la cause de l’échec à l’écran, pas seulement aux lecteurs d’écran', async () => {
    apiMocks.indexFile.mockRejectedValue(new Error('Format PDF protégé par mot de passe'));
    render(<ChatInput />);
    await joindreFichier();

    await waitFor(() => {
      expect(screen.getByText(/Format PDF protégé par mot de passe/)).toBeInTheDocument();
    });
    const cause = screen.getByText(/Format PDF protégé par mot de passe/);
    expect(cause.className).not.toContain('sr-only');
  });

  it('une annulation ne s’affiche pas comme un échec d’indexation', async () => {
    let rejeter: ((raison: unknown) => void) | null = null;
    apiMocks.indexFile.mockImplementation(
      () => new Promise((_resolve, reject) => {
        rejeter = reject;
      }),
    );
    render(<ChatInput />);
    await joindreFichier();

    await act(async () => {
      screen.getByLabelText('Retirer rapport.pdf').click();
      rejeter?.(new DOMException('Aborted', 'AbortError'));
      await Promise.resolve();
    });

    expect(screen.queryByText(/Échec/)).toBeNull();
  });
});
