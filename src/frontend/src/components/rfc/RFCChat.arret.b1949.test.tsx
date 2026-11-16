/**
 * B-1949 : le bouton d’arrêt du mini-chat n’a qu’un title. Le bouton Envoyer,
 * et le même geste dans le composeur, portent un aria-label.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', () => ({
  streamMessage: vi.fn(async function* () {
    yield await new Promise<never>(() => {});
  }),
}));

import { RFCChat } from './RFCChat';

Element.prototype.scrollTo = vi.fn();

describe('B-1949 : le bouton d’arrêt a un nom accessible', () => {
  it('s’annonce « Arrêter la réponse » pendant la génération', async () => {
    render(<RFCChat systemPrompt="x" placeholder="Décris ta commande" onConversationUpdate={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'Un brief' } });
    fireEvent.click(screen.getByRole('button', { name: 'Envoyer' }));
    const arret = await screen.findByRole('button', { name: 'Arrêter la réponse' });
    expect(arret).toHaveAttribute('aria-label', 'Arrêter la réponse');
  });
});
