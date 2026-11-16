/**
 * B-1950 : « THÉRÈSE réfléchit... » n’est ni un statut ni une région live.
 * Un lecteur d’écran n’est pas prévenu du début du flux.
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

describe('B-1950 : le début du flux est annoncé', () => {
  it('« THÉRÈSE réfléchit... » est un statut live', async () => {
    render(<RFCChat systemPrompt="x" placeholder="Décris ta commande" onConversationUpdate={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'Un brief' } });
    fireEvent.click(screen.getByRole('button', { name: 'Envoyer' }));
    const annonce = await screen.findByText('THÉRÈSE réfléchit...');
    expect(annonce).toHaveAttribute('role', 'status');
    expect(annonce).toHaveAttribute('aria-live', 'polite');
  });
});
