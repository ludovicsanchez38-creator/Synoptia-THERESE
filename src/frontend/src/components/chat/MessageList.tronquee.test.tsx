import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useChatStore } from '../../stores/chatStore';
import { MessageList } from './MessageList';

vi.mock('react-virtuoso', () => ({
  Virtuoso: ({ components }: { components?: { Header?: React.ComponentType } }) => {
    const Header = components?.Header;
    return <div>{Header ? <Header /> : null}</div>;
  },
}));

describe('MessageList - plafond silencieux', () => {
  beforeEach(() => {
    useChatStore.setState({
      conversations: [{
        id: 'c1',
        title: 'Fil long',
        messages: [
          { id: 'm1', role: 'user', content: 'dernier', timestamp: new Date() },
        ],
        createdAt: new Date(),
        updatedAt: new Date(),
        messageCount: 110,
        synced: true,
      }],
      currentConversationId: 'c1',
      isStreaming: false,
    });
  });

  it('dit que le fil est incomplet plutôt que de faire croire que tout y est', () => {
    render(<MessageList />);
    const alerte = screen.getByRole('alert');
    expect(alerte).toHaveTextContent('1 / 110 messages affichés');
  });
});
