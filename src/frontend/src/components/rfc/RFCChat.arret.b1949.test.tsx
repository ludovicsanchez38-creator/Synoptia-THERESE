/**
 * B-1949 : amélioration du libellé explicite, pas réparation d'un nom absent.
 * Le title donnait déjà son nom accessible au bouton avant l'aria-label.
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

  it('R1-9 : le title fournissait déjà le même nom accessible avant l’aria-label', async () => {
    render(<RFCChat systemPrompt="x" placeholder="Décris ta commande" onConversationUpdate={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'Un brief' } });
    fireEvent.click(screen.getByRole('button', { name: 'Envoyer' }));
    const arret = await screen.findByRole('button', { name: 'Arrêter la réponse' });
    // Reconstituer uniquement le balisage antérieur, dans le DOM du test.
    arret.removeAttribute('aria-label');
    expect(arret).toHaveAttribute('title', 'Arrêter la réponse');
    expect(arret).toHaveAccessibleName('Arrêter la réponse');
    expect(screen.getByRole('button', { name: 'Arrêter la réponse' })).toBe(arret);
  });
});
