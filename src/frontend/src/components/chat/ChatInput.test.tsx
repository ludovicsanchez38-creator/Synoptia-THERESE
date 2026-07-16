import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { usePanelStore } from '../../stores/panelStore';
import { useStatusStore } from '../../stores/statusStore';
import { ChatInput } from './ChatInput';

const apiMocks = vi.hoisted(() => ({
  getLLMConfig: vi.fn(),
  setLLMConfig: vi.fn(),
  streamMessage: vi.fn(),
  streamDeepResearch: vi.fn(),
  indexFile: vi.fn(),
}));

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
vi.mock('../../hooks/useFileDrop', () => ({ useFileDrop: () => ({ isDragging: false }) }));
vi.mock('./SlashCommandsMenu', () => ({
  SlashCommandsMenu: () => null,
  detectSlashCommand: () => false,
}));
vi.mock('./ActionChips', () => ({ ActionChips: () => null }));
vi.mock('../files/DropZone', () => ({ InlineDropZone: () => null, FileChip: () => null }));
vi.mock('./VoiceDictationButton', () => ({
  VoiceDictationButton: ({ onError }: { onError: (message: string) => void }) => (
    <button type="button" onClick={() => onError('Micro indisponible')}>Simuler erreur dictée</button>
  ),
}));

describe('ChatInput sans modèle', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'ollama',
      model: 'gemma4-tia:latest',
      available_models: ['gemma4-tia:latest'],
      available: false,
    });
    useStatusStore.setState({ connectionState: 'connected' });
    useChatStore.setState({
      conversations: [],
      currentConversationId: null,
      isStreaming: false,
      queuedPrompt: null,
    });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
  });

  it('explique l’absence de modèle, bloque l’envoi et ouvre les réglages IA', async () => {
    render(<ChatInput />);

    expect(await screen.findByTestId('chat-model-unavailable')).toHaveTextContent('Choisis d’abord un modèle');
    expect(screen.getByTestId('chat-message-input')).toBeDisabled();
    expect(screen.getByTestId('chat-send-btn')).toBeDisabled();

    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir les réglages IA' }));
    expect(usePanelStore.getState().showSettings).toBe(true);
    expect(usePanelStore.getState().requestedSettingsTab).toBe('ai');
    expect(apiMocks.streamMessage).not.toHaveBeenCalled();
  });

  it('bloque aussi l’envoi pendant la vérification initiale du modèle', () => {
    apiMocks.getLLMConfig.mockReturnValue(new Promise(() => {}));

    render(<ChatInput />);

    expect(screen.getByTestId('chat-message-input')).toBeDisabled();
    expect(screen.getByPlaceholderText('Vérification du modèle disponible...')).toBeInTheDocument();
    expect(screen.getByTestId('chat-send-btn')).toBeDisabled();
    expect(apiMocks.streamMessage).not.toHaveBeenCalled();
  });

  it('conserve une erreur de dictée jusqu’à sa fermeture explicite', async () => {
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'ollama', model: 'gemma4-tia:latest',
      available_models: ['gemma4-tia:latest'], available: true,
    });
    render(<ChatInput />);
    await screen.findByPlaceholderText("Comment puis-je t'aider ?");

    fireEvent.click(screen.getByRole('button', { name: 'Simuler erreur dictée' }));

    expect(screen.getByRole('alert')).toHaveTextContent('Micro indisponible');
    fireEvent.click(screen.getByRole('button', { name: 'Fermer l’erreur de dictée' }));
    expect(screen.queryByText('Micro indisponible')).not.toBeInTheDocument();
  });

  it('demande le consentement au premier envoi cloud en nommant le fournisseur et les données', async () => {
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'openai', model: 'gpt-test', available_models: ['gpt-test'], available: true,
    });
    apiMocks.streamMessage.mockReturnValue((async function* () {
      yield { type: 'done' };
    })());
    render(<ChatInput />);
    const input = await screen.findByPlaceholderText("Comment puis-je t'aider ?");
    fireEvent.change(input, { target: { value: 'Résume ce dossier' } });

    fireEvent.click(screen.getByTestId('chat-send-btn'));
    expect(screen.getByTestId('chat-cloud-consent')).toHaveTextContent('OpenAI');
    expect(screen.getByTestId('chat-cloud-consent')).toHaveTextContent('message saisi, contexte de conversation, mémoire locale utile');
    expect(apiMocks.streamMessage).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));
    expect(screen.queryByTestId('chat-cloud-consent')).not.toBeInTheDocument();
    expect(input).toHaveValue('Résume ce dossier');

    fireEvent.click(screen.getByTestId('chat-send-btn'));
    fireEvent.click(screen.getByRole('button', { name: 'Autoriser et envoyer' }));
    expect(localStorage.setItem).toHaveBeenCalledWith(
      'therese-cloud-consent', expect.stringContaining('"provider":"OpenAI"'),
    );
    await waitFor(() => expect(apiMocks.streamMessage).toHaveBeenCalledTimes(1));
  });
});
