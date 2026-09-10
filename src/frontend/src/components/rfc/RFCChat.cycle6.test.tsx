/**
 * Cycle 6, lecteur D98 (RFCChat.tsx) : dans le mini-chat de l'assistant de
 * commande, le bouton d'envoi était une icône sans nom ; le bouton d'arrêt
 * voisin en avait un.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', () => ({ streamMessage: vi.fn() }));

import { RFCChat } from './RFCChat';

// jsdom n'implémente pas scrollTo ; l'auto-défilement du fil l'appelle au montage.
Element.prototype.scrollTo = vi.fn();

describe('D98 : le bouton d’envoi du mini-chat a un nom', () => {
  it('s’annonce « Envoyer »', () => {
    render(<RFCChat systemPrompt="x" placeholder="Décris ta commande" onConversationUpdate={vi.fn()} />);
    expect(screen.getByRole('button', { name: /Envoyer/ })).toBeInTheDocument();
  });
});
