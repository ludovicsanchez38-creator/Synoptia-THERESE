/**
 * B-1471 (recette P-146, lot 5, KO-4a) : ⌘⇧F, annoncé « Rechercher dans les
 * Contacts », ouvrait la vue Contacts avec le focus sur son titre : dans la
 * coque, le raccourci appelait `openEmbeddedView('memory')` sans poser la
 * demande de focus de la recherche (l'action `memory.search` la pose).
 */
import { fireEvent, render, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { usePanelStore } from '../../stores/panelStore';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

const MODIFICATEUR = navigator.platform.toUpperCase().includes('MAC') ? { metaKey: true } : { ctrlKey: true };

describe('B-1471 : ⌘⇧F met le curseur dans la recherche des contacts', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/?interface=conversation-canvas');
    useChatStore.setState({ conversations: [], currentConversationId: null, isStreaming: false });
    usePanelStore.setState({ showSettings: false, showCommandPalette: false, showConversationSidebar: false });
    _clearEscapeHandlers();
    useNavigationStore.setState(useNavigationStore.getInitialState());
  });

  it('le raccourci pose la demande de focus de la recherche', async () => {
    const demandes: boolean[] = [];
    const desabonner = useNavigationStore.subscribe((etat) => { if (etat.memorySearchFocusRequested) demandes.push(true); });
    render(<ConversationCanvasPrototype />);
    fireEvent.keyDown(window, { key: 'f', shiftKey: true, ...MODIFICATEUR });
    await waitFor(() => expect(useNavigationStore.getState().activeView).toBe('memory'));
    desabonner();
    expect(demandes.length, 'aucune demande de focus de la recherche n’a été posée').toBeGreaterThan(0);
  });
});
