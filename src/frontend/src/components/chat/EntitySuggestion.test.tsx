import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { EntitySuggestion } from './EntitySuggestion';
import { useContactsStore } from '../../stores/contactsStore';
import { useChatStore } from '../../stores/chatStore';
import type { ExtractedContact } from '../../services/api';

const detected: ExtractedContact = {
  name: 'Jean Dupont',
  company: 'ACME',
  role: 'CEO',
  email: 'jean@acme.fr',
  phone: null,
  confidence: 0.9,
};

describe('EntitySuggestion', () => {
  beforeEach(() => {
    useContactsStore.setState({
      contacts: [],
      searchResults: null,
      loading: false,
      selectedContactId: null,
    });
    useChatStore.setState({ currentConversationId: null });
  });

  it('sauvegarder un contact détecté passe par contactsStore.createContact (visible Mémoire ET CRM)', async () => {
    const createSpy = vi.fn().mockResolvedValue({ id: 'c9', first_name: 'Jean' });
    useContactsStore.setState({ createContact: createSpy });

    render(
      <EntitySuggestion
        contacts={[detected]}
        projects={[]}
        messageId="m1"
        onDismiss={vi.fn()}
        onSaved={vi.fn()}
      />
    );

    fireEvent.click(await screen.findByTitle('Sauvegarder'));

    await waitFor(() => expect(createSpy).toHaveBeenCalledTimes(1));
    expect(createSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        first_name: 'Jean',
        last_name: 'Dupont',
        company: 'ACME',
        email: 'jean@acme.fr',
      })
    );
  });

  it('rattache le contact créé à la conversation courante (scope=conversation, L6 pastille)', async () => {
    const createSpy = vi.fn().mockResolvedValue({ id: 'c9', first_name: 'Jean' });
    useContactsStore.setState({ createContact: createSpy });
    useChatStore.setState({ currentConversationId: 'conv-42' });

    render(
      <EntitySuggestion contacts={[detected]} projects={[]} messageId="m1" onDismiss={vi.fn()} onSaved={vi.fn()} />
    );
    fireEvent.click(await screen.findByTitle('Sauvegarder'));

    await waitFor(() => expect(createSpy).toHaveBeenCalled());
    expect(createSpy).toHaveBeenCalledWith(
      expect.objectContaining({ scope: 'conversation', scope_id: 'conv-42' })
    );
  });

  it('ne rattache pas si aucune conversation courante (le contact reste global)', async () => {
    const createSpy = vi.fn().mockResolvedValue({ id: 'c9', first_name: 'Jean' });
    useContactsStore.setState({ createContact: createSpy });
    useChatStore.setState({ currentConversationId: null });

    render(
      <EntitySuggestion contacts={[detected]} projects={[]} messageId="m1" onDismiss={vi.fn()} onSaved={vi.fn()} />
    );
    fireEvent.click(await screen.findByTitle('Sauvegarder'));

    await waitFor(() => expect(createSpy).toHaveBeenCalled());
    const arg = createSpy.mock.calls[0][0];
    expect(arg.scope).toBeUndefined();
    expect(arg.scope_id).toBeUndefined();
  });
});
