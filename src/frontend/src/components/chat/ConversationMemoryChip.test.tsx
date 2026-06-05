import { render, screen, fireEvent } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ConversationMemoryChip } from './ConversationMemoryChip';
import { useContactsStore } from '../../stores/contactsStore';
import { useChatStore } from '../../stores/chatStore';
import { useNavigationStore } from '../../stores/navigationStore';
import type { Contact } from '../../services/api';

const mk = (over: Partial<Contact>): Contact =>
  ({ id: 'x', first_name: 'A', ...over } as Contact);

describe('ConversationMemoryChip (pastille de glance L6)', () => {
  beforeEach(() => {
    useContactsStore.setState({
      contacts: [],
      searchResults: null,
      loading: false,
      selectedContactId: null,
      fetchContacts: vi.fn().mockResolvedValue(undefined),
    });
    useChatStore.setState({ currentConversationId: null });
    useNavigationStore.setState({ activeView: 'chat', history: [] });
  });

  it('affiche le nombre de contacts liés à la conversation courante (et ignore global / autre conv)', () => {
    useChatStore.setState({ currentConversationId: 'c1' });
    useContactsStore.setState({
      contacts: [
        mk({ id: '1', scope: 'conversation', scope_id: 'c1' }),
        mk({ id: '2', scope: 'conversation', scope_id: 'c1' }),
        mk({ id: '3', scope: 'global' }),
        mk({ id: '4', scope: 'conversation', scope_id: 'autre' }),
      ],
    });
    render(<ConversationMemoryChip />);
    expect(screen.getByText(/2\s+contacts?\s+liés?\s+à cette conversation/i)).toBeInTheDocument();
  });

  it('accorde le singulier pour un seul contact', () => {
    useChatStore.setState({ currentConversationId: 'c1' });
    useContactsStore.setState({ contacts: [mk({ id: '1', scope: 'conversation', scope_id: 'c1' })] });
    render(<ConversationMemoryChip />);
    expect(screen.getByText(/1\s+contact\s+lié\s+à cette conversation/i)).toBeInTheDocument();
  });

  it('clic ouvre la vue Mémoire', () => {
    useChatStore.setState({ currentConversationId: 'c1' });
    useContactsStore.setState({ contacts: [mk({ id: '1', scope: 'conversation', scope_id: 'c1' })] });
    render(<ConversationMemoryChip />);
    fireEvent.click(screen.getByRole('button'));
    expect(useNavigationStore.getState().activeView).toBe('memory');
  });

  it('ne rend rien si aucun contact lié', () => {
    useChatStore.setState({ currentConversationId: 'c1' });
    useContactsStore.setState({ contacts: [mk({ id: '3', scope: 'global' })] });
    const { container } = render(<ConversationMemoryChip />);
    expect(container.firstChild).toBeNull();
  });

  it('ne rend rien hors conversation', () => {
    useChatStore.setState({ currentConversationId: null });
    useContactsStore.setState({ contacts: [mk({ id: '1', scope: 'conversation', scope_id: 'c1' })] });
    const { container } = render(<ConversationMemoryChip />);
    expect(container.firstChild).toBeNull();
  });
});
