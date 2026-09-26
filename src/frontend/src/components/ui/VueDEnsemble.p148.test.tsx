/**
 * P-148, recette dans l'application lancée : un élément sans destination (une
 * tâche) avait la boîte bordée des boutons voisins, et se prenait pour un
 * lien. Seul ce qui mène quelque part a l'allure d'un bouton ; le reste est
 * une ligne, comme celles des livrables.
 */
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { VueDEnsemble } from './VueDEnsemble';

describe('P-148 : VueDEnsemble', () => {
  it('seul un élément qui mène quelque part a l’allure d’un bouton', () => {
    render(
      <VueDEnsemble
        etat="pret"
        onReessayer={vi.fn()}
        messageDePanne="panne"
        messageDeChargement="lecture"
        familles={[
          { cle: 'a', libelle: 'Conversations', total: 1, texteDuVide: '', elements: [{ id: 'c', libelle: 'Devis', nomAccessible: 'Ouvrir la conversation Devis', onOuvrir: vi.fn() }] },
          { cle: 'b', libelle: 'Tâches', total: 1, texteDuVide: '', elements: [{ id: 't', libelle: 'Métrer' }] },
        ]}
      />,
    );
    const bouton = screen.getByRole('button', { name: 'Ouvrir la conversation Devis' });
    expect(bouton.className).toMatch(/\bborder\b/);
    const taches = screen.getByRole('list', { name: 'Tâches (1)' });
    expect(within(taches).queryByRole('button')).toBeNull();
    const ligne = within(taches).getByText('Métrer').parentElement as HTMLElement;
    expect(ligne.className).not.toMatch(/\bborder\b/);
  });
});
