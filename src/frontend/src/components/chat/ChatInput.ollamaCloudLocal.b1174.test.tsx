/**
 * B-1174 : un modèle Ollama Cloud n'est jamais présenté comme local sous le composeur ni dans le fil.
 *
 * Règle écrite par B-1156 (MessageBubble.tsx:710) : « Local » seulement si le
 * fournisseur est ollama ET que le modèle n'est pas un modèle Ollama Cloud
 * (estModeleOllamaCloud). Le même composeur exige d'ailleurs un accord
 * « Ollama Cloud (ollama.com) » pour ce modèle (B-1158). On mesure la pastille
 * sous le champ de saisie et le repère de durée du fil pendant un flux.
 */
import { act, render, screen, waitFor } from '@testing-library/react';
import type { ComponentType, ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore, type Message } from '../../stores/chatStore';
import { usePanelStore } from '../../stores/panelStore';
import { useStatusStore } from '../../stores/statusStore';
import { useAccessibilityStore } from '../../stores/accessibilityStore';
import { useDemoStore } from '../../stores/demoStore';

const apiMocks = vi.hoisted(() => ({
  getLLMConfig: vi.fn(),
  setLLMConfig: vi.fn(),
  streamMessage: vi.fn(),
  streamDeepResearch: vi.fn(),
  indexFile: vi.fn(),
  createConversation: vi.fn().mockResolvedValue({ id: 'conv-serveur', title: 'Nouvelle conversation' }),
}));

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...reel, ...apiMocks };
});
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
vi.mock('./VoiceDictationButton', () => ({ VoiceDictationButton: () => null }));
// JSDOM n'a pas de viewport : seule la virtualisation est remplacée (comme MessageList.attenteLocale.c10).
vi.mock('react-virtuoso', () => ({
  Virtuoso: ({ components, data, itemContent }: {
    components?: { Header?: ComponentType; Footer?: ComponentType };
    data?: Message[];
    itemContent?: (index: number, message: Message) => ReactNode;
  }) => {
    const Header = components?.Header;
    const Footer = components?.Footer;
    return <div>
      {Header && <Header />}
      {(data ?? []).map((message, index) => <div key={message.id}>{itemContent?.(index, message)}</div>)}
      {Footer && <Footer />}
    </div>;
  },
}));

import { ChatInput } from './ChatInput';
import { MessageList } from './MessageList';

function config(provider: string, model: string) {
  return { provider, model, available_models: [model], available: true };
}

async function pastilleDuComposeur(provider: string, model: string) {
  apiMocks.getLLMConfig.mockResolvedValue(config(provider, model));
  render(<ChatInput />);
  await waitFor(() => expect(apiMocks.getLLMConfig).toHaveBeenCalled());
  const pastille = await screen.findByText(/^(local|cloud)$/);
  return { texte: pastille.textContent, infobulle: pastille.getAttribute('title') };
}

describe('B-1174 : composeur et fil face à un modèle Ollama Cloud', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useStatusStore.setState({ connectionState: 'connected' });
    useDemoStore.setState({ enabled: false });
    useChatStore.setState({
      conversations: [],
      currentConversationId: null,
      isStreaming: false,
      queuedPrompt: null,
      fournisseurCourant: null,
    });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
    useAccessibilityStore.setState({ showKeyboardHints: true });
  });

  it('la pastille du composeur ne dit pas « local » pour kimi-k2.6:cloud', async () => {
    const etat = await pastilleDuComposeur('ollama', 'kimi-k2.6:cloud');
    expect(etat).toEqual({
      texte: 'cloud',
      infobulle: 'Modèle Ollama Cloud : le traitement part chez ollama.com',
    });
  });

  it('le repère du fil ne parle pas d’un « modèle local » pendant un flux Ollama Cloud', async () => {
    apiMocks.getLLMConfig.mockResolvedValue(config('ollama', 'gpt-oss:120b-cloud'));
    render(<><MessageList /><ChatInput /></>);
    await waitFor(() => expect(useChatStore.getState().fournisseurCourant).not.toBeNull());
    act(() => {
      useChatStore.setState({
        conversations: [{
          id: 'c13-flux', title: 'Flux', createdAt: new Date(), updatedAt: new Date(), synced: true,
          messages: [
            { id: 'q', role: 'user', content: 'Résume ce dossier', timestamp: new Date() },
            { id: 'r', role: 'assistant', content: '', timestamp: new Date(), isStreaming: true },
          ],
        }],
        currentConversationId: 'c13-flux',
        isStreaming: true,
      });
    });
    const etat = {
      fournisseurCourant: useChatStore.getState().fournisseurCourant,
      repereLocal: screen.queryByText(/Avec un modèle local, cela peut prendre plusieurs minutes/) !== null,
    };
    expect(etat).toEqual({ fournisseurCourant: expect.anything(), repereLocal: false });
  });

  it('témoin : qwen3:8b (installé) garde la pastille « local »', async () => {
    const etat = await pastilleDuComposeur('ollama', 'qwen3:8b');
    expect(etat).toEqual({
      texte: 'local',
      infobulle: 'Modèle local (Ollama) : le traitement reste sur ta machine',
    });
  });

  it('témoin : un fournisseur en ligne affiche « cloud »', async () => {
    const etat = await pastilleDuComposeur('anthropic', 'claude-sonnet-4-6');
    expect(etat.texte).toBe('cloud');
  });
});
