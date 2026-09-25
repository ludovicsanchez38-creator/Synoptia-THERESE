/**
 * P-143 (persona Zoé, cycle 13) : « aide » dans ⌘K rendait « 0 résultat »,
 * et l'icône « ? » du rail ouvrait « Plus d'outils » : un point
 * d'interrogation promettait une aide qu'il n'ouvrait pas. ⌘K « aide » mène
 * à l'aide des raccourcis, et l'icône du rail dit ce qu'elle ouvre.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../hooks/useConversationSync', () => ({ useConversationSync: vi.fn() }));

import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

describe('P-143 : l’aide se trouve, et l’icône ne promet pas autre chose', () => {
  it('⌘K « aide » propose au moins une réponse', async () => {
    render(<ConversationCanvasPrototype />);
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /^Rechercher/ }));
    });
    await act(async () => {
      fireEvent.change(screen.getByRole('combobox'), { target: { value: 'aide' } });
    });

    expect(screen.getByRole('option', { name: /Raccourcis clavier/ })).toBeInTheDocument();
  });

  it('« Plus d’outils » n’a plus l’icône « ? »', () => {
    render(<ConversationCanvasPrototype />);
    const bouton = screen.getByRole('button', { name: 'Plus d’outils' });
    expect(bouton.querySelector('svg')?.getAttribute('class') ?? '').not.toMatch(/help|circle-question|circle-help/);
  });
});
