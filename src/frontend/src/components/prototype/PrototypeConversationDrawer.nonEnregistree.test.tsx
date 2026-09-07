/** B-610 (Jean, c4) : le tiroir listait une conversation que le moteur ne connaissait pas, sans la distinguer. */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { PrototypeConversationDrawer } from './PrototypeConversationDrawer';

describe('PrototypeConversationDrawer : une conversation non enregistrée le dit', () => {
  it('marque la conversation locale sans message comme non enregistrée', () => {
    useChatStore.setState({
      conversations: [{
        id: 'locale-1', title: 'Nouvelle conversation', messages: [], createdAt: new Date(), updatedAt: new Date(), synced: false,
      } as never],
      currentConversationId: null,
    });
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} />);
    expect(screen.getByText(/non enregistrée/i)).toBeInTheDocument();
  });
});
