/** B-610 (Jean, c4) : le tiroir listait une conversation que le moteur ne connaissait pas, sans la distinguer. */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { useChatStore } from '../../stores/chatStore';
import { PrototypeConversationDrawer } from './PrototypeConversationDrawer';

describe('PrototypeConversationDrawer : une conversation non enregistrée le dit', () => {
  it('marque la conversation locale non synchronisée comme non enregistrée', () => {
    useChatStore.setState({
      conversations: [{
        id: 'locale-1', title: 'Devis Martin', createdAt: new Date(), updatedAt: new Date(), synced: false,
        messages: [{ id: 'm1', role: 'user', content: 'Prépare le devis Martin', timestamp: new Date() }],
      } as never],
      currentConversationId: null,
    });
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} />);
    expect(screen.getByText(/non enregistrée/i)).toBeInTheDocument();
  });

  it('P-054 : une conversation sans aucun message n\'est pas listée, même courante (⌘N ne crée pas de fantôme)', () => {
    useChatStore.setState({
      conversations: [
        { id: 'vide-1', title: 'Nouvelle conversation', messages: [], createdAt: new Date(), updatedAt: new Date(), synced: false } as never,
        {
          id: 'pleine-1', title: 'Relance Dupont', createdAt: new Date(), updatedAt: new Date(), synced: true,
          messages: [{ id: 'm2', role: 'user', content: 'Relance Dupont', timestamp: new Date() }],
        } as never,
      ],
      currentConversationId: 'vide-1',
    });
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} />);
    expect(screen.getByText('Relance Dupont')).toBeInTheDocument();
    // Le bouton « Nouvelle conversation » (⌘N) reste ; aucune ENTRÉE de liste ne porte la conversation vide, même courante.
    expect(document.querySelector('[aria-current="page"]')).toBeNull();
    expect(screen.queryByText(/0 message/)).toBeNull();
  });
  it('revue COCO 0.69.0 : une conversation sans message mais avec un brouillon local reste listée', () => {
    vi.mocked(localStorage.getItem).mockImplementation((cle: string) =>
      cle === 'therese-draft-brouillon-1' ? 'Bonjour Camille, suite à notre échange…' : null,
    );
    useChatStore.setState({
      conversations: [
        { id: 'brouillon-1', title: 'Relance Camille', messages: [], createdAt: new Date(), updatedAt: new Date(), synced: false } as never,
        { id: 'vide-1', title: 'Nouvelle conversation', messages: [], createdAt: new Date(), updatedAt: new Date(), synced: false } as never,
      ],
      currentConversationId: null,
    });
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} />);
    // Le brouillon est du travail : sa conversation doit rester joignable.
    expect(screen.getByText('Relance Camille')).toBeInTheDocument();
    expect(screen.getByText(/Brouillon en attente/)).toBeInTheDocument();
    expect(screen.queryByText(/0 message/)).toBeNull();
    // La conversation vide sans brouillon reste absente.
    expect(screen.getAllByText(/non enregistrée/).length).toBe(1);
  });
});

describe('P-070 : le tiroir montre l’aperçu du dernier message', () => {
  it('sous le titre, les premiers mots du dernier message', () => {
    useChatStore.setState({
      conversations: [{
        id: 'c-1', title: 'Devis Martin', createdAt: new Date(), updatedAt: new Date(), synced: true,
        messages: [
          { id: 'm1', role: 'user', content: 'Prépare le devis Martin', timestamp: new Date() },
          { id: 'm2', role: 'assistant', content: 'Voici une proposition de devis pour la mission Martin, en trois lots.', timestamp: new Date() },
        ],
      } as never],
      currentConversationId: null,
    });
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} />);
    expect(screen.getByText(/Voici une proposition de devis pour la mission Martin/)).toBeInTheDocument();
  });
});

describe('audit release 0.74 : le tiroir respecte le mode démonstration', () => {
  it('titre et aperçu passent par le masque', async () => {
    const { useDemoStore } = await import('../../stores/demoStore');
    useDemoStore.setState({ enabled: true, replacementMap: new Map([['Martin', 'Bernard'], ['Devis Martin', 'Devis Bernard']]) });
    useChatStore.setState({
      conversations: [{
        id: 'c-1', title: 'Devis Martin', createdAt: new Date(), updatedAt: new Date(), synced: true,
        messages: [
          { id: 'm1', role: 'user', content: 'Prépare le devis', timestamp: new Date() },
          { id: 'm2', role: 'assistant', content: 'Voici une proposition pour **Martin** en trois lots.', timestamp: new Date() },
        ],
      } as never],
      currentConversationId: null,
    });
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} />);
    expect(screen.getByText('Devis Bernard')).toBeInTheDocument();
    expect(screen.getByText(/Voici une proposition pour Bernard en trois lots/)).toBeInTheDocument();
    expect(screen.queryByText(/Martin/)).toBeNull();
    useDemoStore.setState({ enabled: false, replacementMap: new Map() });
  });
});
