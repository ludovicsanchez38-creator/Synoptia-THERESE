/**
 * B-1403 (persona Zoé, cycle 13) : à 200 % (fenêtre de 720×450), le bouton
 * « Rechercher ⌘K » disparaissait de l'en-tête (`hidden md:flex`, sous
 * 768 px) : la palette n'avait plus d'entrée visible. Et le composeur, avec
 * son fond, occupait 245 px sur 398 : la carte « Ton attention aujourd'hui »
 * passait dessous, « Voir la suite » posé sur son titre.
 *
 * « Rechercher » reste affiché (l'icône, le mot restant dans le nom
 * accessible) et, quand la fenêtre est basse, le composeur se resserre.
 * jsdom n'applique pas les requêtes média : les classes sont vérifiées ici,
 * la mesure a été faite dans Chrome à 720×450.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../hooks/useConversationSync', () => ({ useConversationSync: vi.fn() }));

import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

const BASSE = '[@media(max-height:560px)]';

describe('B-1403 : l’Accueil tient dans une fenêtre petite', () => {
  it('« Rechercher » reste dans l’en-tête sous 768 px', () => {
    render(<ConversationCanvasPrototype />);
    const bouton = screen.getByRole('button', { name: /^Rechercher/ });
    expect(bouton.className.split(/\s+/)).not.toContain('hidden');
  });

  it('fenêtre basse : le fond et le champ du composeur se resserrent', () => {
    render(<ConversationCanvasPrototype />);
    const fond = screen.getByTestId('prototype-composer-backdrop');
    expect(fond.className).toContain(`${BASSE}:pt-9`);
    expect(fond.className).toContain(`${BASSE}:pb-3`);
    const champ = screen.getByPlaceholderText(/Demande à Thérèse/);
    expect(champ.className).toContain(`${BASSE}:min-h-9`);
    expect(champ.className).toContain(`${BASSE}:h-9`);
  });
});
