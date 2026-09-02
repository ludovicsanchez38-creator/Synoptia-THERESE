/**
 * 31/08/2026 - Déposer une capture d'écran dans le chat.
 *
 * Ludo glisse une capture dans THÉRÈSE et lit « Type de fichier non autorisé
 * pour l'indexation : '.png' [...] Ce fichier ne sera pas utilisé pour
 * répondre. » Le composeur envoyait toute pièce jointe à l'indexation, y
 * compris une image, que la chaîne d'extraction de texte ne sait pas lire.
 *
 * Une image se montre au modèle, elle ne s'indexe pas.
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

const CAPTURE = {
  path: '/tmp/Capture d’écran 2026-08-31.png',
  name: 'Capture d’écran 2026-08-31.png',
  mimeType: 'image/png',
  size: 240_000,
};
const DOCUMENT = { path: '/tmp/rapport.pdf', name: 'rapport.pdf', mimeType: 'application/pdf', size: 12_000 };

async function deposer(fichiers: unknown[]) {
  await act(async () => {
    void dropMock.onDrop?.(fichiers);
    await Promise.resolve();
    await Promise.resolve();
  });
}

describe('ChatInput - une image se montre, elle ne s’indexe pas', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    dropMock.onDrop = null;
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'openai',
      model: 'gpt-5.6-luna',
      available_models: ['gpt-5.6-luna'],
      available: true,
    });
    apiMocks.indexFile.mockResolvedValue(undefined);
    useStatusStore.setState({ connectionState: 'connected' });
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
  });

  it('n’envoie pas une capture d’écran à l’indexation', async () => {
    render(<ChatInput />);
    await deposer([CAPTURE]);
    await waitFor(() => expect(screen.getByText(CAPTURE.name)).toBeInTheDocument());
    expect(apiMocks.indexFile).not.toHaveBeenCalled();
  });

  it('indexe toujours un document, et seulement lui', async () => {
    render(<ChatInput />);
    await deposer([CAPTURE, DOCUMENT]);
    await waitFor(() => expect(apiMocks.indexFile).toHaveBeenCalledTimes(1));
    expect(apiMocks.indexFile.mock.calls[0][0]).toBe(DOCUMENT.path);
  });

  it('n’affiche aucune erreur d’indexation sur une image', async () => {
    apiMocks.indexFile.mockRejectedValue(new Error('Type de fichier non autorisé'));
    render(<ChatInput />);
    await deposer([CAPTURE]);
    await waitFor(() => expect(screen.getByText(CAPTURE.name)).toBeInTheDocument());
    expect(screen.queryByText(/non autoris/i)).toBeNull();
  });
});
