/**
 * B-056 : un échec réseau doit rester visible.
 *
 * Quatre surfaces du fil de conversation transformaient une panne en état
 * vide, donc en affirmation fausse :
 *  - le sélecteur de dossier vidait sa liste (« aucun projet où se rattacher »
 *    alors que la liste n'avait pas pu être lue) ;
 *  - la pastille mémoire rendait `null` (« aucun contact lié » alors que les
 *    contacts n'avaient pas été lus, et que le store POSE pourtant l'erreur) ;
 *  - la suggestion d'entité revenait à son état initial, indiscernable d'un
 *    clic jamais fait ;
 *  - le téléchargement d'image ne disait rien, là où le MÊME composant
 *    notifie l'utilisateur pour un fichier de skill.
 *
 * Le contrat vérifié ici : une panne se distingue d'une absence.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ConversationProjectPicker } from './ConversationProjectPicker';
import { ConversationMemoryChip } from './ConversationMemoryChip';
import { EntitySuggestion } from './EntitySuggestion';
import { MessageBubble } from './MessageBubble';
import { useChatStore } from '../../stores/chatStore';
import { useContactsStore } from '../../stores/contactsStore';
import { useStatusStore } from '../../stores/statusStore';
import type { ExtractedContact } from '../../services/api';
import type { Message } from '../../stores/chatStore';

const apiMocks = vi.hoisted(() => ({
  listProjects: vi.fn(),
  downloadGeneratedImage: vi.fn(),
}));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>(
    '../../services/api',
  );
  return {
    ...actual,
    listProjects: apiMocks.listProjects,
    downloadGeneratedImage: apiMocks.downloadGeneratedImage,
  };
});

beforeEach(() => {
  vi.clearAllMocks();
  useStatusStore.setState({ notifications: [] });
  useChatStore.setState({ currentConversationId: null });
  useContactsStore.setState({
    contacts: [],
    searchResults: null,
    loading: false,
    loaded: false,
    error: null,
    selectedContactId: null,
    fetchContacts: vi.fn().mockRejectedValue(new Error('réseau')),
  });
});

describe('B-056 : un échec réseau reste visible', () => {
  it('sélecteur de dossier : la liste non lue est annoncée', async () => {
    apiMocks.listProjects.mockRejectedValue(new Error('500'));

    render(<ConversationProjectPicker conversationId="conv-1" projectId={null} />);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
    expect(screen.getByRole('alert').textContent).toMatch(/dossiers?/i);
  });

  it('sélecteur de dossier : rien à signaler quand la lecture réussit', async () => {
    apiMocks.listProjects.mockResolvedValue([{ id: 'p1', name: 'Coaching Q2' }]);

    render(<ConversationProjectPicker conversationId="conv-1" projectId={null} />);

    await waitFor(() => {
      expect(screen.getByRole('option', { name: 'Coaching Q2' })).toBeInTheDocument();
    });
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('pastille mémoire : des contacts non lus ne valent pas zéro contact', () => {
    useChatStore.setState({ currentConversationId: 'c1' });
    useContactsStore.setState({ error: 'Impossible de charger les contacts.' });

    render(<ConversationMemoryChip />);

    expect(screen.getByRole('alert').textContent).toMatch(/contacts/i);
  });

  it('pastille mémoire : sans erreur, zéro contact lié ne montre toujours rien', () => {
    useChatStore.setState({ currentConversationId: 'c1' });
    useContactsStore.setState({ error: null });

    const { container } = render(<ConversationMemoryChip />);

    expect(container.firstChild).toBeNull();
  });

  it("suggestion d'entité : un enregistrement échoué le dit", async () => {
    const detected: ExtractedContact = {
      name: 'Jean Dupont',
      company: 'ACME',
      role: 'CEO',
      email: 'jean@acme.fr',
      phone: null,
      confidence: 0.9,
    };
    useContactsStore.setState({
      createContact: vi.fn().mockRejectedValue(new Error('500')),
    });

    render(
      <EntitySuggestion
        contacts={[detected]}
        projects={[]}
        messageId="m1"
        onDismiss={vi.fn()}
        onSaved={vi.fn()}
      />,
    );

    fireEvent.click(await screen.findByTitle('Sauvegarder'));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
    // La carte reste actionnable : on doit pouvoir réessayer.
    expect(screen.getByTitle('Sauvegarder')).toBeInTheDocument();
  });

  it("téléchargement d'image : l'échec est dit à l'utilisateur", async () => {
    apiMocks.downloadGeneratedImage.mockRejectedValue(new Error('404'));
    const message = {
      id: 'm1',
      role: 'assistant',
      content: 'Voici ton image',
      timestamp: new Date(),
      imageId: 'img-1',
    } as Message;

    render(<MessageBubble message={message} />);

    fireEvent.click(screen.getByTitle("Enregistrer l'image"));

    await waitFor(() => {
      expect(useStatusStore.getState().notifications.length).toBeGreaterThan(0);
    });
    expect(useStatusStore.getState().notifications[0].type).toBe('error');
  });
});
