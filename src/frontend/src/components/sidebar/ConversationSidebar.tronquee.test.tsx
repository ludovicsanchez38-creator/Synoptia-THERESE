import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { useChatStore } from '../../stores/chatStore';
import { ConversationSidebar } from './ConversationSidebar';

describe('ConversationSidebar - lot F plafond', () => {
  beforeEach(() => {
    useChatStore.setState({
      conversations: [],
      currentConversationId: null,
      conversationsTruncated: true,
    });
  });

  it('dit que l’historique est incomplet plutôt que de s’arrêter à 50 en silence', () => {
    render(<ConversationSidebar isOpen onClose={() => undefined} />);
    expect(screen.getByRole('alert')).toHaveTextContent(/Liste incomplète/);
  });
});
