/**
 * B-1352 (persona Claire, cycle 13) : le tiroir ne retrouvait pas une
 * conversation par le nom de la cliente.
 *
 * Le titre est la demande coupée à 50 caractères ; « Hélène » arrivait après.
 * Le filtre ne regardait que ce titre, alors que l'aperçu affiché juste
 * dessous contenait « Hélène Ménard-Lefèvre ». La recherche porte désormais
 * aussi sur les messages chargés, accents et casse repliés.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { PrototypeConversationDrawer } from './PrototypeConversationDrawer';
import { _clearEscapeHandlers } from '../../lib/escapeStack';
import { useChatStore } from '../../stores/chatStore';

vi.mock('../../hooks/useConversationSync', () => ({
  useConversationSync: vi.fn(() => ({ syncConversations: vi.fn(), loadConversationMessages: vi.fn() })),
}));

vi.mock('../../services/api/chat', () => ({
  renameConversation: vi.fn(),
  deleteConversation: vi.fn(),
  exportConversation: vi.fn(),
}));

const message = (id: string, role: 'user' | 'assistant', content: string) => ({
  id, role, content, timestamp: new Date(),
});

describe('recherche du tiroir dans le contenu (B-1352)', () => {
  beforeEach(() => {
    _clearEscapeHandlers();
    useChatStore.setState({
      conversations: [
        {
          id: 'cr-helene',
          title: 'Rédige le compte rendu de ma séance de 16 h avec H',
          messages: [
            message('m1', 'user', 'Rédige le compte rendu de ma séance de 16 h avec Hélène Ménard-Lefèvre, bilan du premier mois.'),
            message('m2', 'assistant', 'Compte rendu de séance : Hélène Ménard-Lefèvre a posé ses priorités.'),
          ],
          createdAt: new Date(),
          updatedAt: new Date(),
          synced: true,
        },
        {
          id: 'autre',
          title: 'Devis pour Julien Garnier',
          messages: [message('m3', 'user', 'Prépare un devis pour Julien Garnier.')],
          createdAt: new Date(),
          updatedAt: new Date(),
          synced: true,
        },
      ],
      currentConversationId: null,
    } as never);
  });

  const chercher = (texte: string) => {
    render(<PrototypeConversationDrawer onClose={vi.fn()} onOpenChat={vi.fn()} surface="search" />);
    fireEvent.change(screen.getByLabelText('Rechercher une conversation'), { target: { value: texte } });
  };

  it('retrouve la conversation par un nom écrit après le 50e caractère', () => {
    chercher('Hélène');
    expect(screen.getByText('Rédige le compte rendu de ma séance de 16 h avec H')).toBeInTheDocument();
    expect(screen.queryByText('Devis pour Julien Garnier')).not.toBeInTheDocument();
  });

  it('retrouve aussi le nom tapé sans accent', () => {
    chercher('menard');
    expect(screen.getByText('Rédige le compte rendu de ma séance de 16 h avec H')).toBeInTheDocument();
    expect(screen.queryByText('Devis pour Julien Garnier')).not.toBeInTheDocument();
  });

  it('un mot absent partout ne rend rien', () => {
    chercher('Zorro');
    expect(screen.getByText('Aucune conversation trouvée')).toBeInTheDocument();
  });
});
