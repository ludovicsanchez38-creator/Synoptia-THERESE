import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { usePanelStore } from '../../stores/panelStore';
import { useStatusStore } from '../../stores/statusStore';
import { useAccessibilityStore } from '../../stores/accessibilityStore';
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
    useAccessibilityStore.setState({ showKeyboardHints: true });
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

  it('masque immédiatement les indications de raccourcis selon le réglage d’accessibilité', async () => {
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'ollama', model: 'gemma4-tia:latest',
      available_models: ['gemma4-tia:latest'], available: true,
    });
    render(<ChatInput />);
    await screen.findByPlaceholderText("Comment puis-je t'aider ?");
    expect(screen.getByText(/nouvelle ligne/)).toBeInTheDocument();
    expect(screen.getByText(/commandes/)).toBeInTheDocument();

    act(() => useAccessibilityStore.setState({ showKeyboardHints: false }));
    expect(screen.queryByText(/nouvelle ligne/)).not.toBeInTheDocument();
    expect(screen.queryByText(/commandes/)).not.toBeInTheDocument();
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
    // Consentement v2 (revue 0.40) : finalité llm + ID du fournisseur en clé.
    expect(localStorage.setItem).toHaveBeenCalledWith(
      'therese-cloud-consent', expect.stringContaining('"llm:openai"'),
    );
    await waitFor(() => expect(apiMocks.streamMessage).toHaveBeenCalledTimes(1));
  });

  it('marque une pièce jointe en échec, bloque l’envoi et permet de relancer l’indexation', async () => {
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'ollama', model: 'gemma4-tia:latest',
      available_models: ['gemma4-tia:latest'], available: true,
    });
    apiMocks.indexFile.mockRejectedValueOnce(new Error('Index corrompu'));
    const { container } = render(<ChatInput />);
    const messageInput = await screen.findByPlaceholderText("Comment puis-je t'aider ?");
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(fileInput, { target: { files: [new File(['contenu'], 'audit.pdf', { type: 'application/pdf' })] } });

    expect(await screen.findByText('Échec')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('Échec');
    fireEvent.change(messageInput, { target: { value: 'Analyse ce document' } });
    expect(screen.getByTestId('chat-send-btn')).toBeDisabled();

    apiMocks.indexFile.mockResolvedValueOnce(undefined);
    fireEvent.click(screen.getByRole('button', { name: 'Réessayer l’indexation de audit.pdf' }));
    expect(await screen.findByText('Prêt')).toBeInTheDocument();
    expect(screen.getByTestId('chat-send-btn')).toBeEnabled();
  });

  it('explique un changement de modèle refusé et permet de le réessayer', async () => {
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'ollama', model: 'modèle-a', available_models: ['modèle-a', 'modèle-b'], available: true,
    });
    apiMocks.setLLMConfig.mockRejectedValueOnce(new Error('Backend indisponible'));
    render(<ChatInput />);

    const selector = await screen.findByLabelText('Modèle de conversation');
    fireEvent.change(selector, { target: { value: 'modèle-b' } });
    expect(await screen.findByRole('alert')).toHaveTextContent('Changement de modèle non enregistré');
    expect(selector).toHaveValue('modèle-a');

    apiMocks.setLLMConfig.mockResolvedValueOnce({ provider: 'ollama', model: 'modèle-b', available_models: ['modèle-a', 'modèle-b'], available: true });
    apiMocks.getLLMConfig.mockResolvedValueOnce({ provider: 'ollama', model: 'modèle-b', available_models: ['modèle-a', 'modèle-b'], available: true });
    fireEvent.click(screen.getByRole('button', { name: 'Réessayer' }));
    await waitFor(() => expect(apiMocks.setLLMConfig).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(selector).toHaveValue('modèle-b'));
    expect(screen.queryByText(/Changement de modèle non enregistré/)).not.toBeInTheDocument();
  });

  it('restaure la saisie et les pièces jointes quand l’envoi échoue', async () => {
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'ollama', model: 'gemma4-tia:latest',
      available_models: ['gemma4-tia:latest'], available: true,
    });
    apiMocks.indexFile.mockResolvedValue(undefined);
    apiMocks.streamMessage.mockReturnValue((async function* () {
      yield { type: 'status', content: 'Connexion…' };
      throw new Error('Réseau interrompu');
    })());

    const { container } = render(<ChatInput />);
    const input = await screen.findByPlaceholderText("Comment puis-je t'aider ?");
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(fileInput, { target: { files: [new File(['contenu'], 'preuve.pdf', { type: 'application/pdf' })] } });
    expect(await screen.findByText('Prêt')).toBeInTheDocument();
    fireEvent.change(input, { target: { value: 'Analyse cette preuve' } });

    fireEvent.click(screen.getByTestId('chat-send-btn'));

    await waitFor(() => expect(input).toHaveValue('Analyse cette preuve'));
    expect(screen.getByLabelText('Pièces jointes')).toHaveTextContent('Prêt');
  });
});
