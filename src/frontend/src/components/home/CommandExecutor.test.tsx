import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { CommandDefinition } from '../../types/command';
import { useChatStore } from '../../stores/chatStore';
import { PrototypeExternalActionConfirmationProvider } from '../app/ExternalActionConfirmation';
import { CommandExecutor } from './CommandExecutor';

const { generateImageMock } = vi.hoisted(() => ({ generateImageMock: vi.fn() }));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    generateImage: generateImageMock,
    getImageDownloadUrl: vi.fn((id: string) => `/api/images/download/${id}`),
  };
});

const imageCommand: CommandDefinition = {
  id: 'image-gpt',
  name: 'Créer une image',
  description: 'Générer un visuel',
  icon: 'Image',
  category: 'production',
  source: 'builtin',
  action: 'image',
  prompt_template: 'Décris le visuel',
  skill_id: null,
  system_prompt: null,
  show_on_home: true,
  show_in_slash: true,
  sort_order: 1,
  image_config: {
    provider: 'gpt-image-2',
    default_size: '1024x1024',
    default_quality: 'medium',
  },
  navigate_target: null,
  is_editable: false,
};

describe('CommandExecutor - génération Images 0.40', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
    generateImageMock.mockResolvedValue({
      id: 'image-1',
      provider: 'gpt-image-2',
      file_name: 'image.png',
      file_size: 1024,
      mime_type: 'image/png',
      created_at: '2026-07-15T10:00:00Z',
      prompt: 'Un atelier lumineux avec un MacBook noir',
      download_url: '/api/images/download/image-1',
    });
  });

  afterEach(() => {
    // Le chat persiste avec un debounce de 400 ms. Retirer la clé en attente
    // évite qu'un timer du test survive à la destruction de jsdom.
    useChatStore.persist.clearStorage();
  });

  it('sépare la saisie du prompt et la confirmation avant tout appel provider', async () => {
    render(
      <PrototypeExternalActionConfirmationProvider>
        <CommandExecutor
          command={imageCommand}
          onClose={vi.fn()}
          onPromptSelect={vi.fn()}
          onStartRFC={vi.fn()}
        />
      </PrototypeExternalActionConfirmationProvider>,
    );

    fireEvent.change(await screen.findByRole('textbox'), {
      target: { value: 'Un atelier lumineux avec un MacBook noir' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Générer' }));

    const preview = screen.getByTestId('external-action-confirmation');
    expect(preview).toHaveTextContent('Un atelier lumineux avec un MacBook noir');
    expect(preview).toHaveTextContent('GPT Image 2');
    expect(preview).toHaveTextContent('1024x1024');
    expect(generateImageMock).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Confirmer et générer' }));

    await waitFor(() => {
      expect(generateImageMock).toHaveBeenCalledWith({
        prompt: 'Un atelier lumineux avec un MacBook noir',
        provider: 'gpt-image-2',
        quality: 'medium',
        size: '1024x1024',
      });
    });
  });
});
