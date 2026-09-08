/** P-053 (Nadia, c4) : le tiroir des conversations est une région ; une région sans nom n'est pas annoncée utilement par une synthèse vocale. Garde : nommé dans ses trois surfaces. */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { PrototypeConversationDrawer } from './PrototypeConversationDrawer';

describe('PrototypeConversationDrawer : région nommée (P-053)', () => {
  it.each(['history', 'new', 'search'] as const)('surface %s : role=region nommé « Conversations »', (surface) => {
    useChatStore.setState({ conversations: [], currentConversationId: null });
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} surface={surface} />);
    expect(screen.getByRole('region', { name: 'Conversations' })).toBe(screen.getByTestId('prototype-conversation-drawer'));
  });
});
