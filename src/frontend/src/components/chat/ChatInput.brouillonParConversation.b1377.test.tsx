/**
 * B-1377 (persona Hugo, cycle 13) : le brouillon tapé dans la conversation
 * Orion se retrouvait dans le champ de la conversation Veille, d'un autre
 * projet, et y restait au retour.
 *
 * Le champ gardait son texte quand la conversation changeait (la restauration
 * ne remplissait qu'un champ vide), et une sauvegarde encore en attente était
 * perdue dès qu'on tapait ailleurs. Un brouillon appartient à sa conversation ;
 * seul un vrai changement de conversation remplace le texte (l'identifiant
 * adopté du serveur, ou une conversation qui vient d'être créée, gardent la
 * saisie).
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { usePanelStore } from '../../stores/panelStore';
import { useStatusStore } from '../../stores/statusStore';
import { useAccessibilityStore } from '../../stores/accessibilityStore';

const apiMocks = vi.hoisted(() => ({
  getLLMConfig: vi.fn(),
  setLLMConfig: vi.fn(),
  streamMessage: vi.fn(),
  streamDeepResearch: vi.fn(),
  indexFile: vi.fn(),
  cancelGeneration: vi.fn(),
  createConversation: vi.fn().mockResolvedValue({ id: 'conv-serveur', title: 'Nouvelle conversation' }),
}));
vi.mock('../../services/api', () => ({ ...apiMocks, ApiError: class ApiError extends Error { status = 500; } }));
vi.mock('../../hooks/useFileDrop', () => ({ useFileDrop: () => ({ isDragging: false }) }));
vi.mock('./SlashCommandsMenu', () => ({ SlashCommandsMenu: () => null, detectSlashCommand: () => false }));
vi.mock('./ActionChips', () => ({ ActionChips: () => null }));
vi.mock('../files/DropZone', () => ({ InlineDropZone: () => null, FileChip: () => null }));
vi.mock('./VoiceDictationButton', () => ({ VoiceDictationButton: () => null }));

import { ChatInput } from './ChatInput';

const conversation = (id: string, title: string) => ({
  id, title, messages: [], messageCount: 2, createdAt: new Date(), updatedAt: new Date(), synced: true,
});

function champ() {
  return screen.getByTestId('chat-message-input') as HTMLTextAreaElement;
}

describe('ChatInput - un brouillon par conversation (B-1377)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    const stockage: Record<string, string> = {};
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => stockage[k] ?? null,
      setItem: (k: string, v: string) => { stockage[k] = v; },
      removeItem: (k: string) => { delete stockage[k]; },
      clear: () => { for (const k of Object.keys(stockage)) delete stockage[k]; },
    });
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'anthropic', model: 'claude-sonnet-4-6', available_models: [], available: true });
    useStatusStore.setState({ connectionState: 'connected' });
    usePanelStore.setState({ showSettings: false, requestedSettingsTab: null });
    useAccessibilityStore.setState({ showKeyboardHints: true });
    useChatStore.setState({
      conversations: [conversation('orion', 'Orion'), conversation('veille', 'Veille')],
      currentConversationId: 'orion', isStreaming: false, queuedPrompt: null,
    } as never);
  });
  afterEach(() => vi.unstubAllGlobals());

  it('le brouillon d’Orion ne passe pas dans Veille, et revient dans Orion', async () => {
    render(<ChatInput />);
    await screen.findByTestId('chat-message-input');
    fireEvent.change(champ(), { target: { value: 'Brouillon pour Orion' } });

    act(() => { useChatStore.setState({ currentConversationId: 'veille' }); });
    expect(champ().value).toBe('');

    act(() => { useChatStore.setState({ currentConversationId: 'orion' }); });
    expect(champ().value).toBe('Brouillon pour Orion');
  });

  it('l’identifiant adopté du serveur garde la saisie', async () => {
    render(<ChatInput />);
    await screen.findByTestId('chat-message-input');
    fireEvent.change(champ(), { target: { value: 'La suite de ma question' } });

    act(() => {
      useChatStore.setState((etat) => ({
        conversations: etat.conversations.map((c) => (c.id === 'orion' ? { ...c, id: 'orion-serveur' } : c)),
        currentConversationId: 'orion-serveur',
      }));
    });
    expect(champ().value).toBe('La suite de ma question');
  });

  it('une conversation qui vient d’être créée garde la saisie', async () => {
    useChatStore.setState({ currentConversationId: null });
    render(<ChatInput />);
    await screen.findByTestId('chat-message-input');
    fireEvent.change(champ(), { target: { value: 'Premier message' } });

    act(() => {
      useChatStore.setState((etat) => ({
        conversations: [conversation('neuve', 'Nouvelle conversation'), ...etat.conversations],
        currentConversationId: 'neuve',
      }));
    });
    expect(champ().value).toBe('Premier message');
  });
});
