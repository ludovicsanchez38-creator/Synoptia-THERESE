/**
 * B-248 — la carte de confirmation recouvre la fin du dernier message.
 *
 * Constat du 01/09/2026 (persona RP18c, 1280x800) : 175 px de la dernière bulle
 * masqués. La couche est un calque en position fixe ancré à 96 px du bas de la
 * fenêtre et posé au-dessus de tout (`bottom-24`, `z-[70]`), monté à la racine
 * de l'application — délibérément, pour survivre au remplacement du contenu
 * principal par un canevas ou un panneau. Côté fil, rien ne compensait : aucun
 * composant de la conversation n'observait le store de confirmation.
 *
 * Le correctif garde le calque là où il est (l'exigence de survie tient) et
 * fait réserver au fil la bande que le calque occupe. Le contrat vérifié ici
 * est structurel — jsdom ne met rien en page : la réserve existe quand une
 * confirmation est en attente, et seulement là. La mesure en pixels reste au
 * navigateur.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useToolConfirmationStore } from '../../stores/toolConfirmationStore';
import { useChatStore } from '../../stores/chatStore';
import { MessageList } from '../chat/MessageList';
import { CommonToolConfirmationLayer } from './CommonToolConfirmationLayer';

vi.mock('../../hooks/useConversationSync', () => ({ useConversationSync: vi.fn() }));

const confirmationEnAttente = {
  confirmation_id: 'b248',
  tool_name: 'send_email',
  arguments: { to: 'client@example.fr', subject: 'Devis', body: 'Bonjour,' },
};

function conversationAvecMessages() {
  useChatStore.setState({
    currentConversationId: 'conv-b248',
    isStreaming: false,
    conversations: [
      {
        id: 'conv-b248',
        title: 'Devis',
        messages: [
          { id: 'm1', role: 'user', content: 'Envoie le devis à Camille.', timestamp: new Date() },
          { id: 'm2', role: 'assistant', content: 'Je prépare l’envoi.', timestamp: new Date() },
        ],
        createdAt: new Date(),
        updatedAt: new Date(),
      },
    ] as never,
  });
}

describe('B-248 — une confirmation en attente ne recouvre pas le fil', () => {
  beforeEach(() => {
    useToolConfirmationStore.setState({ pending: [] });
    conversationAvecMessages();
  });

  it('le fil réserve la bande occupée par le calque quand une action attend', () => {
    useToolConfirmationStore.setState({ pending: [confirmationEnAttente] });

    render(
      <>
        <MessageList />
        <CommonToolConfirmationLayer />
      </>,
    );

    const reserve = screen.getByTestId('reserve-confirmation');
    // La réserve appartient au fil, pas au calque : c'est le fil qui doit
    // libérer la place, le calque restant à la racine de l'application.
    expect(screen.getByTestId('chat-message-list')).toContainElement(reserve);
    // Une réserve de hauteur nulle serait un leurre : elle ne libère rien.
    expect(parseFloat(reserve.style.height)).toBeGreaterThan(0);
  });

  it('sans confirmation en attente, le fil ne réserve rien', () => {
    render(
      <>
        <MessageList />
        <CommonToolConfirmationLayer />
      </>,
    );

    // Sans cette borne, un fil qui ne rendrait plus rien (état vide, plantage)
    // rendrait le test vert sans avoir examiné la moindre conversation.
    expect(screen.getByTestId('chat-message-list')).toBeInTheDocument();
    expect(screen.queryByTestId('reserve-confirmation')).toBeNull();
  });
});
