/**
 * B-1375 (persona Hugo, cycle 13), volet « nom » : ⌘K s'appelait
 * « Rechercher » (en-tête), « Rechercher dans Thérèse » (dialogue),
 * « Palette de commandes » (raccourcis) et « commandes » (pied du composeur),
 * et promettait de chercher « dans Thérèse » alors qu'il ne parcourt que les
 * commandes et les capacités (« Orion », « Hélène » : 0 résultat). Un seul
 * nom, « Rechercher », qui dit ce qu'il parcourt ; l'état vide dit ce que la
 * recherche ne parcourt pas encore. La recherche dans les données suivra
 * P-016 et P-116.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../../hooks/useConversationSync', () => ({ useConversationSync: vi.fn() }));

import { descriptionDuRaccourci } from '../../lib/raccourcisAnnonces';
import { ConversationCanvasPrototype } from './ConversationCanvasPrototype';

const NOM = 'Rechercher une commande, une capacité ou une donnée';

describe('B-1375 : un nom pour ⌘K, qui dit ce qu’il parcourt', () => {
  it('le dialogue et la fiche des raccourcis portent le même nom', async () => {
    render(<ConversationCanvasPrototype />);
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /^Rechercher/ }));
    });

    expect(screen.getByRole('dialog', { name: NOM })).toBeInTheDocument();
    expect(descriptionDuRaccourci('⌘ + K')).toBe(NOM);
  });

  it('l’état vide dit ce que la recherche ne parcourt pas encore', async () => {
    render(<ConversationCanvasPrototype />);
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /^Rechercher/ }));
    });
    await act(async () => {
      fireEvent.change(screen.getByRole('combobox'), { target: { value: 'Orion' } });
    });

    // P-016 : contacts, projets et conversations sont désormais parcourus ;
    // l'état vide dit ce qui ne l'est toujours pas.
    expect(screen.getByText(/pas encore tes documents ni ton agenda/)).toBeInTheDocument();
  });
});
