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

  it('ajoute au carnet partagé le contact enregistré depuis une conversation', async () => {
    const createSpy = vi.fn().mockResolvedValue({ id: 'c9', first_name: 'Jean' });
    useContactsStore.setState({ createContact: createSpy });
    useChatStore.setState({ currentConversationId: 'conv-42' });

    render(
      <EntitySuggestion contacts={[detected]} projects={[]} messageId="m1" onDismiss={vi.fn()} onSaved={vi.fn()} />
    );
    fireEvent.click(await screen.findByTitle('Sauvegarder'));

    await waitFor(() => expect(createSpy).toHaveBeenCalled());
    expect(createSpy).toHaveBeenCalledWith(
      expect.objectContaining({ scope: 'global' })
    );
  });

  it('ignorer un projet homonyme ne retire pas l’autre', async () => {
    const onSaved = vi.fn();
    render(
      <EntitySuggestion
        contacts={[]}
        projects={[
          { name: 'Chantier', description: 'A', budget: null, status: null, confidence: 0.8 },
          { name: 'Chantier', description: 'B', budget: null, status: null, confidence: 0.7 },
        ]}
        messageId="m1"
        onDismiss={vi.fn()}
        onSaved={onSaved}
      />
    );
    const ignorer = screen.getAllByTitle('Ignorer');
    expect(ignorer).toHaveLength(2);
    fireEvent.click(ignorer[0]);
    await waitFor(() => expect(screen.getAllByTitle('Ignorer')).toHaveLength(1));
    expect(screen.getByText('B')).toBeTruthy();
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
    expect(arg.scope).toBe('global');
    expect(arg.scope_id).toBeUndefined();
  });
  it('R1-2 : conserve le projet explicitement choisi', async () => {
    const createSpy = vi.fn().mockResolvedValue({ id: 'c9' });
    useContactsStore.setState({ createContact: createSpy });
    useChatStore.setState({ currentConversationId: 'conv-projet', conversations: [{ id: 'conv-projet', title: 'Projet', messages: [], createdAt: new Date(), updatedAt: new Date(), projectId: 'projet-a', memoryScope: 'project' }] });
    render(<EntitySuggestion contacts={[detected]} projects={[]} messageId="m1" onDismiss={vi.fn()} onSaved={vi.fn()} />);
    fireEvent.click(await screen.findByTitle('Sauvegarder'));
    await waitFor(() => expect(createSpy).toHaveBeenCalledWith(expect.objectContaining({ scope: 'project', scope_id: 'projet-a' })));
  });

});
