/**
 * B-933 : en mode démonstration, les entités détectées d'un message ne sont
 * pas affichées. MessageList masquait le contenu, les sources et les
 * fichiers, puis transmettait `detectedEntities` en clair à EntitySuggestion :
 * un vrai nom de contact ou de projet apparaissait sous le masque, et
 * « Enregistrer » l'aurait écrit dans la vraie mémoire. Le flux ne publie
 * plus ces entités (B-1154) ; la garde tient pour toute publication future.
 */
import { render, screen } from '@testing-library/react';
import type { ComponentType, ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useChatStore, type Message } from '../../stores/chatStore';
import { useDemoStore } from '../../stores/demoStore';
import { MessageList } from './MessageList';

// JSDOM n'a pas de viewport : seule la virtualisation est remplacée.
// MessageBubble et TypingIndicator restent les composants de production.
vi.mock('react-virtuoso', () => ({
  Virtuoso: ({ components, data, itemContent }: {
    components?: { Header?: ComponentType; Footer?: ComponentType };
    data?: Message[];
    itemContent?: (index: number, message: Message) => ReactNode;
  }) => {
    const Header = components?.Header;
    const Footer = components?.Footer;
    return <div>
      {Header && <Header />}
      {(data ?? []).map((message, index) => <div key={message.id}>{itemContent?.(index, message)}</div>)}
      {Footer && <Footer />}
    </div>;
  },
}));

describe('B-933 : entités détectées sous le mode démonstration', () => {
  beforeEach(() => {
    useChatStore.setState({
      conversations: [{
        id: 'c13-entites', title: 'Entités',
        createdAt: new Date(), updatedAt: new Date(), synced: true,
        messages: [
          { id: 'c13-q', role: 'user', content: 'Note ce rendez-vous', timestamp: new Date() },
          {
            id: 'c13-r', role: 'assistant', content: 'C’est noté.', timestamp: new Date(),
            detectedEntities: {
              contacts: [{ name: 'Gaspard Réelnom', company: 'Brasserie Véritable', role: null, email: null, phone: null, confidence: 0.9 }],
              projects: [{ name: 'Projet Confidentiel', description: null, budget: null, status: null, confidence: 0.9 }],
            },
          },
        ],
      }],
      currentConversationId: 'c13-entites',
      isStreaming: false,
    });
  });

  it('hors démo, la suggestion montre les entités (témoin)', () => {
    useDemoStore.setState({ enabled: false });
    render(<MessageList />);
    expect(screen.getAllByText(/Gaspard Réelnom/).length).toBeGreaterThan(0);
  });

  it('en démo, aucun nom réel ne sort par la suggestion', () => {
    useDemoStore.setState({ enabled: true });
    render(<MessageList />);
    expect(screen.queryByText(/Gaspard Réelnom/)).toBeNull();
    expect(screen.queryByText(/Brasserie Véritable/)).toBeNull();
    expect(screen.queryByText(/Projet Confidentiel/)).toBeNull();
  });
});
